import pytest
from apps.inventory.services import adjust_inventory
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