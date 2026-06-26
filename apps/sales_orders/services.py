from django.db import transaction
from django.utils.crypto import get_random_string
from .models import SalesOrder, SalesOrderItem
from apps.inventory.models import Inventory
from apps.inventory.services import adjust_inventory
from core.exceptions import InsufficientStockException, InvalidOperationException
from apps.sales_orders.tasks import process_sales_order_created_event, process_sales_order_cancelled_event

def generate_so_number() -> str:
    # Generates a random 8-character string for the Order Number
    return f"SO-{get_random_string(8).upper()}"

@transaction.atomic
def create_sales_order(data: dict, created_by_user_id: int) -> SalesOrder:
    items_data = data.pop('items', [])
    warehouse_id = data['warehouse'].id if hasattr(data['warehouse'], 'id') else data['warehouse']
    
    if not items_data:
        raise InvalidOperationException("Sales Order must contain at least one item.", "EMPTY_ORDER")

    if 'order_number' not in data or not data['order_number']:
        data['order_number'] = generate_so_number()
        
    short_items = []
    total_amount = 0
    # WHY: If a customer orders 5 items, and we only have stock for 4 of them, the entire order must be rejected. 
    # HOW: select_for_update() locks the specific inventory row so no one else can buy it while we do the math.
    for item in items_data:
        try:
            inventory = Inventory.objects.select_for_update().get(
                product_id=item['product'], 
                warehouse_id=warehouse_id
            )
        except Inventory.DoesNotExist:
            # If the product doesn't even exist in this warehouse, it's a massive shortage.
            short_items.append({
                "product_id": item['product'],
                "requested_quantity": item['quantity'],
                "available_quantity": 0
            })
            continue

        if inventory.quantity_available < item['quantity']:
            short_items.append({
                "product_id": item['product'],
                "requested_quantity": item['quantity'],
                "available_quantity": inventory.quantity_available
            })
            
    # WHAT: The Shortage Circuit Breaker
    # WHY: If the short_items array has even 1 item in it, we abort the entire process and return the exact payload the spec demands.
    if short_items:
        raise InsufficientStockException(short_items=short_items)
        
    # PHASE 2: Create Order and Reserve Stock
    data['created_by_id'] = created_by_user_id
    data['status'] = 'CONFIRMED'
    data['total_amount'] = 0
    
    so = SalesOrder.objects.create(**data)
    
    for item in items_data:
        line_total = item['quantity'] * float(item['unit_price'])
        total_amount += line_total
        
        SalesOrderItem.objects.create(
            sales_order=so,
            product_id=item['product'],
            quantity=item['quantity'],
            unit_price=item['unit_price'],
            total_price=line_total
        )
        
        inventory = Inventory.objects.get(product_id=item['product'], warehouse_id=warehouse_id)
        inventory.quantity_available -= item['quantity']
        inventory.quantity_reserved += item['quantity']
        inventory.save()
        
    so.total_amount = total_amount
    so.save()
    process_sales_order_created_event.delay(so.id, created_by_user_id)
    return so

@transaction.atomic
def dispatch_sales_order(so_id: int) -> SalesOrder:
    so = SalesOrder.objects.select_for_update().get(id=so_id)
    
    if so.status != 'CONFIRMED':
        raise InvalidOperationException("Only CONFIRMED orders can be dispatched.", "INVALID_TRANSITION")
    for item in so.items.all():
        inventory = Inventory.objects.select_for_update().get(product_id=item.product.id, warehouse_id=so.warehouse.id)
        inventory.quantity_reserved -= item.quantity
        inventory.save()
        
        # Calls the Phase 3 Inventory Service to log the physical deduction
        adjust_inventory({
            "product_id": item.product.id,
            "warehouse_id": so.warehouse.id,
            "transaction_type": "OUTBOUND",
            "quantity": item.quantity,
            "notes": f"SO Dispatch: {so.order_number}"
        }, so.created_by_id) # Using created_by as the actor for simplicity right now
        
    from django.utils import timezone
    so.status = 'DISPATCHED'
    so.dispatched_at = timezone.now()
    so.save()
    return so

@transaction.atomic
def deliver_sales_order(so_id: int) -> SalesOrder:
    so = SalesOrder.objects.select_for_update().get(id=so_id)
    if so.status != 'DISPATCHED':
        raise InvalidOperationException("Only DISPATCHED orders can be delivered.", "INVALID_TRANSITION")
        
    from django.utils import timezone
    so.status = 'DELIVERED'
    so.delivered_at = timezone.now()
    so.save()
    return so

@transaction.atomic
def cancel_sales_order(so_id: int, reason: str) -> SalesOrder:
    so = SalesOrder.objects.select_for_update().get(id=so_id)
    
    if so.status not in ['PENDING', 'CONFIRMED']:
        raise InvalidOperationException("Order has already been dispatched or delivered.", "CANCEL_NOT_ALLOWED")
        
    #  The customer cancelled. The goods are taken off the holding shelf and put back on the available shelf.
    for item in so.items.all():
        inventory = Inventory.objects.select_for_update().get(product_id=item.product.id, warehouse_id=so.warehouse.id)
        inventory.quantity_available += item.quantity
        inventory.quantity_reserved -= item.quantity
        inventory.save()
        
    so.status = 'CANCELLED'
    so.save()
    process_sales_order_cancelled_event.delay(so.id)
    return so