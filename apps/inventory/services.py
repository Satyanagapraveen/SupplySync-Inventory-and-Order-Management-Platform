import uuid
from django.db import transaction
from .models import Inventory, InventoryTransaction
from core.exceptions import InsufficientInventoryException
from django.core.cache import cache
from django.db.models import F
import logging
from django.core.cache import cache
@transaction.atomic
def adjust_inventory(data: dict, performed_by_user_id: int) -> InventoryTransaction:
    inventory, created = Inventory.objects.select_for_update().get_or_create(
        product_id=data['product_id'],
        warehouse_id=data['warehouse_id'],
        defaults={'quantity_available': 0, 'quantity_reserved': 0, 'quantity_damaged': 0}
    )

    t_type = data['transaction_type']
    qty = data['quantity']

    if t_type == 'INBOUND':
        inventory.quantity_available += qty
    elif t_type in ['OUTBOUND', 'DAMAGE_REPORT']:
        if inventory.quantity_available < qty:
            raise InsufficientInventoryException(detail="Not enough stock available.", code="INSUFFICIENT_INVENTORY")
        inventory.quantity_available -= qty
        if t_type == 'DAMAGE_REPORT':
            inventory.quantity_damaged += qty
    elif t_type == 'ADJUSTMENT':
        if inventory.quantity_available + qty < 0:
            raise InsufficientInventoryException(detail="Adjustment would result in negative stock.", code="INSUFFICIENT_INVENTORY")
        inventory.quantity_available += qty

    inventory.save()

    transaction_record = InventoryTransaction.objects.create(
        product=inventory.product,
        warehouse=inventory.warehouse,
        transaction_type=t_type,
        quantity=qty,
        reference_id=f"ADJ-{str(uuid.uuid4())[:8].upper()}",
        notes=data.get('notes', ''),
        performed_by_id=performed_by_user_id
    )

    # TODO: Dispatch Celery Task (process_inventory_updated_event)
    return transaction_record

@transaction.atomic
def transfer_inventory(data: dict, performed_by_user_id: int) -> dict:
    product_id = data['product_id']
    source_id = data['source_warehouse_id']
    dest_id = data['destination_warehouse_id']
    qty = data['quantity']

    first_lock_id = min(source_id, dest_id)
    second_lock_id = max(source_id, dest_id)

    first_inv, _ = Inventory.objects.select_for_update().get_or_create(
        product_id=product_id, warehouse_id=first_lock_id, 
        defaults={'quantity_available': 0, 'quantity_reserved': 0, 'quantity_damaged': 0}
    )
    second_inv, _ = Inventory.objects.select_for_update().get_or_create(
        product_id=product_id, warehouse_id=second_lock_id, 
        defaults={'quantity_available': 0, 'quantity_reserved': 0, 'quantity_damaged': 0}
    )

    source_inv = first_inv if first_inv.warehouse_id == source_id else second_inv
    dest_inv = first_inv if first_inv.warehouse_id == dest_id else second_inv

    if source_inv.quantity_available < qty:
        raise InsufficientInventoryException(detail="Source warehouse lacks sufficient stock.", code="INSUFFICIENT_INVENTORY")

    source_inv.quantity_available -= qty
    dest_inv.quantity_available += qty

    source_inv.save()
    dest_inv.save()

    transfer_ref = f"TRANSFER-{str(uuid.uuid4())[:8].upper()}"

    outbound_tx = InventoryTransaction.objects.create(
        inventory=source_inv, transaction_type='OUTBOUND', quantity=qty,
        reference_id=transfer_ref, notes=data.get('notes', ''), performed_by_id=performed_by_user_id
    )
    
    inbound_tx = InventoryTransaction.objects.create(
        inventory=dest_inv, transaction_type='INBOUND', quantity=qty,
        reference_id=transfer_ref, notes=data.get('notes', ''), performed_by_id=performed_by_user_id
    )

    # TODO: Dispatch Celery Task (process_inventory_transfer_event)
    return {"outbound": outbound_tx, "inbound": inbound_tx}

def get_low_stock_alerts() -> list:
    cached_alerts = cache.get('inventory:low-stock')
    if cached_alerts is not None:
        return cached_alerts

    low_stock_records = Inventory.objects.filter(
        is_deleted=False,
        quantity_available__lte=F('product__reorder_level')
    ).select_related('product', 'warehouse')

    alerts = []
    for inv in low_stock_records:
        alerts.append({
            "product_id": inv.product.id,
            "sku": inv.product.sku,
            "product_name": inv.product.name,
            "warehouse_id": inv.warehouse.id,
            "warehouse_name": inv.warehouse.name,
            "quantity_available": inv.quantity_available,
            "reorder_level": inv.product.reorder_level,
            "deficit": inv.product.reorder_level - inv.quantity_available
        })

    cache.set('inventory:low-stock', alerts, timeout=300)
    return alerts

logger=logging.getLogger(__name__)
def check_and_publish_low_stock_alert(product_id: int, warehouse_id: int) -> None:
    try:
        inventory=Inventory.objects.get(product_id=product_id,warehouse_id=warehouse_id)
        if inventory.quantity_available<=inventory.product.reorder_level:
            logger.warning(
                f"LOW STOCK ALERT:PRODUCT{inventory.product.sku} in Warehouse{inventory.warehouse.name}"
                f" has{inventory.quantity_available} units remaining(reorder_level:{inventory.product.reorder_level})"
            )
            cache.delete('inventory:low-stock')
    except Inventory.DoesNotExist:
        logger.error(f"Failed to check low stock:Inventory record not found for product{product_id} in warehouse{warehouse_id}")

