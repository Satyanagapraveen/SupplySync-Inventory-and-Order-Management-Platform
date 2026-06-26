import redis
from django.db import transaction
from .models import PurchaseOrder,PurchaseOrderItem
from django.utils import timezone
from core.exceptions import InvalidOperationException,PermissionDeniedException
from apps.inventory.services import adjust_inventory
redis_client=redis.Redis(host='localhost',port=6379,db=0,decode_responses=True)
from django.core.cache import cache
from apps.purchase_orders.tasks import process_purchase_order_received_event

def generate_po_number() -> str:
    today_str = timezone.now().strftime("%Y%m%d")
    redis_key = f"po-sequence:{today_str}"
    
    cache.add(redis_key, 0, timeout=86400)
    current_sequence = cache.incr(redis_key)
    
    padded_sequence = str(current_sequence).zfill(4)
    return f"PO-{today_str}-{padded_sequence}"

@transaction.atomic
def create_purchase_order(data: dict, created_by_user_id: int) -> PurchaseOrder:
    items_data = data.pop('items', [])
    if 'supplier' not in data or 'warehouse' not in data:
        raise InvalidOperationException(
            detail="Supplier or Warehouse missing from validated data. Ensure your JSON payload keys exactly match 'supplier' and 'warehouse'.", 
            code="MISSING_RELATIONS"
        )

    if 'po_number' not in data or not data['po_number']:
        data['po_number'] = generate_po_number()
        
    if PurchaseOrder.objects.filter(po_number=data['po_number']).exists():
        raise InvalidOperationException(detail="PO number collision detected.", code="DUPLICATE_PO_NUMBER")
        
    data['created_by_id'] = created_by_user_id
    data['status'] = 'DRAFT'
    data['total_amount'] = 0

    po = PurchaseOrder.objects.create(**data)
    
    total_amount = 0
    for item in items_data:
        line_total = item['quantity_ordered'] * float(item['unit_price'])
        total_amount += line_total
        
        PurchaseOrderItem.objects.create(
            purchase_order=po,
            product_id=item['product'],
            quantity_ordered=item['quantity_ordered'],
            quantity_received=0,
            unit_price=item['unit_price'],
            total_price=line_total
        )
    po.total_amount = total_amount
    po.save()
    
    return po

@transaction.atomic
def submit_purchase_order(po_id: int) -> PurchaseOrder:
    po = PurchaseOrder.objects.select_for_update().get(id=po_id)
    
    if po.status != 'DRAFT':
        raise InvalidOperationException(detail="Only DRAFT orders can be submitted.", code="INVALID_STATUS_TRANSITION")
        
    if not po.items.exists():
        raise InvalidOperationException(detail="Cannot submit an empty purchase order.", code="PO_HAS_NO_ITEMS")
        
    po.status = 'PENDING_APPROVAL'
    po.save()
    return po

@transaction.atomic
def approve_purchase_order(po_id: int, approved_by_user_id: int) -> PurchaseOrder:
    po = PurchaseOrder.objects.select_for_update().get(id=po_id)
    
    if po.status != 'PENDING_APPROVAL':
        raise InvalidOperationException(detail="Only PENDING_APPROVAL orders can be approved.", code="INVALID_STATUS_TRANSITION")
        
    # if po.created_by_id == approved_by_user_id:
    #     raise PermissionDeniedException(detail="Self-approval is strictly forbidden.", code="SELF_APPROVAL_NOT_ALLOWED")
        
    po.status = 'APPROVED'
    po.approved_by_id = approved_by_user_id
    po.save()
    return po

@transaction.atomic
def receive_purchase_order(po_id: int, data: dict, performed_by_user_id: int) -> PurchaseOrder:
    po = PurchaseOrder.objects.select_for_update().get(id=po_id)
    
    if po.status not in ['APPROVED', 'PARTIALLY_RECEIVED']:
        raise InvalidOperationException(detail="PO must be APPROVED or PARTIALLY_RECEIVED to receive items.", code="PO_NOT_RECEIVABLE")
        
    items_payload = data['items']
    all_items_fulfilled = True
    any_item_received = False
    
    for entry in items_payload:
        line_item = po.items.select_for_update().get(id=entry['po_item_id'])
        qty_received = entry['quantity_received']
        
        max_allowable = line_item.quantity_ordered - line_item.quantity_received
        if qty_received > max_allowable:
            raise InvalidOperationException(
                detail=f"Item {line_item.id} received quantity exceeds balance ordered.", 
                code="RECEIVE_QUANTITY_EXCEEDED"
            )
            
        line_item.quantity_received += qty_received
        line_item.save()
        
        adjust_inventory({
            "product_id": line_item.product.id,
            "warehouse_id": po.warehouse.id,
            "transaction_type": "INBOUND",
            "quantity": qty_received,
            "notes": f"Automated PO Intake Receipt. Reference PO: {po.po_number}"
        }, performed_by_user_id)
        
    for item in po.items.all():
        if item.quantity_received < item.quantity_ordered:
            all_items_fulfilled = False
        if item.quantity_received > 0:
            any_item_received = True
            
    if all_items_fulfilled:
        po.status = 'RECEIVED'
    elif any_item_received:
        po.status = 'PARTIALLY_RECEIVED'
        
    po.save()
    
    process_purchase_order_received_event.delay(po.id, performed_by_user_id)
    
    return po

@transaction.atomic
def cancel_purchase_order(po_id: int, reason: str) -> PurchaseOrder:
    po = PurchaseOrder.objects.select_for_update().get(id=po_id)
    
    if po.status in ['ORDERED', 'PARTIALLY_RECEIVED', 'RECEIVED']:
        raise InvalidOperationException(detail="Cannot cancel an active fulfilling order.", code="PO_CANCELLATION_NOT_ALLOWED")
        
    po.status = 'CANCELLED'
    po.save()
    return po
