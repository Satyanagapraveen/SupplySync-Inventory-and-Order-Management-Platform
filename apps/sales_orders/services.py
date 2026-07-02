from django.db import transaction
from django.utils.crypto import get_random_string
from django.utils import timezone
from .models import SalesOrder, SalesOrderItem
from apps.inventory.models import Inventory
from apps.inventory.services import adjust_inventory
from core.exceptions import InsufficientStockException, InvalidOperationException
from apps.sales_orders.tasks import process_sales_order_created_event, process_sales_order_cancelled_event

def generate_so_number() -> str:
    return f"SO-{get_random_string(8).upper()}"

@transaction.atomic
def create_sales_order(data: dict, created_by_user_id: int) -> SalesOrder:
    items_data = data.pop('items', [])
    warehouse_id = data.get('warehouse_id')
    
    if not items_data:
        raise InvalidOperationException("Sales Order must contain at least one item.", "EMPTY_ORDER")

    if 'order_number' not in data or not data['order_number']:
        data['order_number'] = generate_so_number()
        
    short_items = []
    total_amount = 0
    inventories = {}
    
    for item in items_data:
        product_id = item['product_id']
        qty = item['quantity']
        
        try:
            inventory = Inventory.objects.select_for_update().select_related('product').get(
                product_id=product_id, 
                warehouse_id=warehouse_id
            )
            inventories[product_id] = inventory
        except Inventory.DoesNotExist:
            short_items.append({
                "product_id": product_id,
                "requested_quantity": qty,
                "available_quantity": 0
            })
            continue

        if inventory.quantity_available < qty:
            short_items.append({
                "product_id": product_id,
                "requested_quantity": qty,
                "available_quantity": inventory.quantity_available
            })
            
    if short_items:
        raise InsufficientStockException(short_items=short_items)
        
    data['created_by_id'] = created_by_user_id
    data['status'] = 'PENDING'
    data['warehouse_id'] = warehouse_id
    
    so = SalesOrder.objects.create(**data)
    
    for item in items_data:
        product_id = item['product_id']
        qty = item['quantity']
        inventory = inventories[product_id]
        
        unit_price = item.get('unit_price', inventory.product.unit_price) 
        line_total = qty * float(unit_price)
        total_amount += line_total
        
        SalesOrderItem.objects.create(
            sales_order=so,
            product_id=product_id,
            quantity=qty,
            unit_price=unit_price,
            total_price=line_total
        )
        
        inventory.quantity_available -= qty
        inventory.quantity_reserved += qty
        inventory.save()
        
    so.total_amount = total_amount
    so.save()
    process_sales_order_created_event.delay(order_id=so.id,created_by_user_id=created_by_user_id)
    return so

@transaction.atomic
def dispatch_sales_order(order_id: int, performed_by_user_id: int) -> SalesOrder:
    so = SalesOrder.objects.select_for_update().get(id=order_id)
    
    if so.status not in ['PENDING', 'CONFIRMED']:
        raise InvalidOperationException("Only PENDING or CONFIRMED orders can be dispatched.", "INVALID_TRANSITION")
        
    for item in so.items.all():
        inventory = Inventory.objects.select_for_update().get(product_id=item.product.id, warehouse_id=so.warehouse.id)
        inventory.quantity_reserved -= item.quantity
        inventory.save()
        
        adjust_inventory({
            "product_id": item.product.id,
            "warehouse_id": so.warehouse.id,
            "transaction_type": "OUTBOUND",
            "quantity": item.quantity,
            "notes": f"SO Dispatch: {so.order_number}"
        }, performed_by_user_id) 
        
    so.status = 'DISPATCHED'
    so.dispatched_at = timezone.now()
    so.save()
    return so

@transaction.atomic
def deliver_sales_order(order_id: int, performed_by_user_id: int = None) -> SalesOrder:
    so = SalesOrder.objects.select_for_update().get(id=order_id)
    if so.status != 'DISPATCHED':
        raise InvalidOperationException("Only DISPATCHED orders can be delivered.", "INVALID_TRANSITION")
        
    so.status = 'DELIVERED'
    so.delivered_at = timezone.now()
    so.save()
    return so

@transaction.atomic
def cancel_sales_order(order_id: int, performed_by_user_id: int) -> SalesOrder:
    so = SalesOrder.objects.select_for_update().get(id=order_id)
    
    if so.status not in ['PENDING', 'CONFIRMED']:
        raise InvalidOperationException("Order has already been dispatched or delivered.", "INVALID_OPERATION")
        
    for item in so.items.all():
        inventory = Inventory.objects.select_for_update().get(product_id=item.product.id, warehouse_id=so.warehouse.id)
        inventory.quantity_available += item.quantity
        inventory.quantity_reserved -= item.quantity
        inventory.save()
        
    so.status = 'CANCELLED'
    so.save()
    process_sales_order_cancelled_event.delay(order_id=so.id)
    return so