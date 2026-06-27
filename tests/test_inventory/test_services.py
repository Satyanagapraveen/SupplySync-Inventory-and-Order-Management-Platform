import pytest
from apps.inventory.services import adjust_inventory
from apps.inventory.models import InventoryTransaction

@pytest.mark.django_db
def test_adjust_inventory_creates_transaction_record_when_inbound(sample_inventory, staff_user):
    # Setup data
    data = {
        'product_id': sample_inventory.product.id,
        'warehouse_id': sample_inventory.warehouse.id,
        'transaction_type': 'INBOUND',
        'quantity': 50
    }
    
    # Execute
    tx = adjust_inventory(data, performed_by_user_id=staff_user.id)
    
    # Verify
    assert tx.quantity == 50
    assert tx.transaction_type == 'INBOUND'
    assert InventoryTransaction.objects.count() == 1