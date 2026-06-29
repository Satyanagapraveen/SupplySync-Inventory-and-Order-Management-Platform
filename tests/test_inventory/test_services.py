import pytest
from apps.inventory.services import adjust_inventory,transfer_inventory
from apps.inventory.models import InventoryTransaction
from core.exceptions import InsufficientInventoryException

def test_adjust_inventory_creates_transaction_record_when_inbound(db, sample_inventory, staff_user, mocker):
    
    mocker.patch('apps.inventory.services.process_inventory_updated_event.delay')
    
    initial_quantity = sample_inventory.quantity_available

    test_data = {
        'product_id': sample_inventory.product.id,
        'warehouse_id': sample_inventory.warehouse.id,
        'transaction_type': 'INBOUND',
        'quantity': 20,
        'notes': 'Restocking test'
    }
    
    transaction_record = adjust_inventory(data=test_data, performed_by_user_id=staff_user.id)
    
    sample_inventory.refresh_from_db()
    
    assert sample_inventory.quantity_available == initial_quantity + 20
    
    assert transaction_record.transaction_type == 'INBOUND'
    
    assert transaction_record.quantity == 20
    
    assert InventoryTransaction.objects.count() == 1

def test_adjust_inventory_raises_exception_when_outbound_exceeds_available(db, sample_inventory, staff_user):
    
    initial_quantity = sample_inventory.quantity_available
    
    test_data = {
        'product_id': sample_inventory.product.id,
        'warehouse_id': sample_inventory.warehouse.id,
        'transaction_type': 'OUTBOUND',
        'quantity': 999,
        'notes': 'Trying to ship more than we have'
    }
    
    with pytest.raises(InsufficientInventoryException) as exc_info:
        adjust_inventory(data=test_data, performed_by_user_id=staff_user.id)
        
    assert exc_info.value.default_code == "INSUFFICIENT_INVENTORY"
    
    sample_inventory.refresh_from_db()
    
    assert sample_inventory.quantity_available == initial_quantity
    
    assert InventoryTransaction.objects.count() == 0

def test_adjust_inventory_dispatches_celery_task_on_success(db, sample_inventory, staff_user, mocker):
    
    mock_celery_task = mocker.patch('apps.inventory.services.process_inventory_updated_event.delay')
    
    test_data = {
        'product_id': sample_inventory.product.id,
        'warehouse_id': sample_inventory.warehouse.id,
        'transaction_type': 'INBOUND',
        'quantity': 15,
        'notes': 'Triggering Celery'
    }
    
    adjust_inventory(data=test_data, performed_by_user_id=staff_user.id)
    
    mock_celery_task.assert_called_once_with(
        product_id=sample_inventory.product.id,
        warehouse_id=sample_inventory.warehouse.id,
        transaction_type='INBOUND',
        quantity=15
    )

def test_transfer_inventory_deducts_from_source_and_adds_to_destination(db, sample_inventory, sample_warehouse, staff_user, mocker):
    
    mocker.patch('apps.inventory.services.process_inventory_transfer_event.delay')
    from apps.warehouses.models import Warehouse
    destination_warehouse = Warehouse.objects.create(
        name="Dest Warehouse", warehouse_code="WH-DEST", 
        location="456 Dest St", city="Dest City", 
        state="Dest State", pincode="654321", capacity=500
    )
    
    initial_source_qty = sample_inventory.quantity_available
    
    test_data = {
        'product_id': sample_inventory.product.id,
        'source_warehouse_id': sample_inventory.warehouse.id,
        'destination_warehouse_id': destination_warehouse.id,
        'quantity': 10,
        'notes': 'Warehouse transfer'
    }
    
    result = transfer_inventory(data=test_data, performed_by_user_id=staff_user.id)
    
    # Refresh the source inventory from the database
    sample_inventory.refresh_from_db()
    
    # Fetch the newly created destination inventory record
    from apps.inventory.models import Inventory
    dest_inventory = Inventory.objects.get(product=sample_inventory.product, warehouse=destination_warehouse)
    
    # 1. Assert math is correct
    assert sample_inventory.quantity_available == initial_source_qty - 10
    assert dest_inventory.quantity_available == 10
    
    # 2. Assert Audit Trails were created correctly
    assert result['outbound'].transaction_type == 'OUTBOUND'
    assert result['outbound'].warehouse.id == sample_inventory.warehouse.id
    
    assert result['inbound'].transaction_type == 'INBOUND'
    assert result['inbound'].warehouse.id == destination_warehouse.id
    
    assert InventoryTransaction.objects.count() == 2