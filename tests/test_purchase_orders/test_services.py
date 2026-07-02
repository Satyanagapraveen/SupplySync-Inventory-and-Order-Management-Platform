import pytest
import re
from apps.purchase_orders.services import (
    create_purchase_order,
    approve_purchase_order,
    receive_purchase_order,
    cancel_purchase_order
)
from apps.inventory.models import Inventory
from core.exceptions import InvalidOperationException, PermissionDeniedException

def test_create_purchase_order_generates_po_number_with_correct_format(db, sample_supplier, sample_warehouse, procurement_manager_user):
    test_data = {
        'supplier': sample_supplier,
        'warehouse': sample_warehouse,
        'items': []
    }
    
    po = create_purchase_order(data=test_data, created_by_user_id=procurement_manager_user.id)
    
    assert re.match(r'^PO-\d{8}-\d{4}$', po.po_number) is not None
    assert po.status == 'DRAFT'

def test_approve_purchase_order_raises_exception_when_approver_is_same_as_creator(db, sample_supplier, sample_warehouse, procurement_manager_user):
    test_data = {
        'supplier': sample_supplier,
        'warehouse': sample_warehouse,
        'items': []
    }
    
    po = create_purchase_order(data=test_data, created_by_user_id=procurement_manager_user.id)
    
    po.status = 'PENDING_APPROVAL'
    po.save()

    with pytest.raises(PermissionDeniedException) as exc_info:
        approve_purchase_order(po_id=po.id, approved_by_user_id=procurement_manager_user.id)
        
    assert exc_info.value.get_codes() == "SELF_APPROVAL_NOT_ALLOWED"

def test_approve_purchase_order_raises_exception_when_status_is_not_pending_approval(db, sample_supplier, sample_warehouse, procurement_manager_user, warehouse_manager_user):
    test_data = {
        'supplier': sample_supplier,
        'warehouse': sample_warehouse,
        'items': []
    }
    
    po = create_purchase_order(data=test_data, created_by_user_id=procurement_manager_user.id)
    
    with pytest.raises(InvalidOperationException) as exc_info:
        approve_purchase_order(po_id=po.id, approved_by_user_id=warehouse_manager_user.id)
        
    assert exc_info.value.get_codes() == "INVALID_STATUS_TRANSITION"

def test_receive_purchase_order_updates_inventory_for_received_items(db, sample_supplier, sample_warehouse, sample_product, procurement_manager_user, staff_user):
    test_data = {
        'supplier': sample_supplier,
        'warehouse': sample_warehouse,
        'items': [{'product': sample_product.id, 'quantity_ordered': 50, 'unit_price': 10.0}]
    }
    
    po = create_purchase_order(data=test_data, created_by_user_id=procurement_manager_user.id)
    
    po.status = 'APPROVED'
    po.save()
    
    po_item = po.items.first()
    
    receive_data = {
        'items': [{'po_item_id': po_item.id, 'quantity_received': 50}]
    }
    
    receive_purchase_order(po_id=po.id, data=receive_data, performed_by_user_id=staff_user.id)
    
    po.refresh_from_db()
    inventory = Inventory.objects.get(product=sample_product, warehouse=sample_warehouse)
    
    assert po.status == 'RECEIVED'
    assert inventory.quantity_available == 50

def test_receive_purchase_order_sets_status_to_partially_received_when_not_all_items_received(db, sample_supplier, sample_warehouse, sample_product, procurement_manager_user):
    test_data = {
        'supplier': sample_supplier,
        'warehouse': sample_warehouse,
        'items': [{'product': sample_product.id, 'quantity_ordered': 100, 'unit_price': 15.0}]
    }
    
    po = create_purchase_order(data=test_data, created_by_user_id=procurement_manager_user.id)
    
    po.status = 'APPROVED'
    po.save()
    
    po_item = po.items.first()
    
    receive_data = {
        'items': [{'po_item_id': po_item.id, 'quantity_received': 20}]
    }
    
    receive_purchase_order(po_id=po.id, data=receive_data, performed_by_user_id=procurement_manager_user.id)
    
    po.refresh_from_db()
    
    assert po.status == 'PARTIALLY_RECEIVED'

def test_cancel_purchase_order_raises_exception_when_status_is_received(db, sample_supplier, sample_warehouse, procurement_manager_user):
    test_data = {
        'supplier': sample_supplier,
        'warehouse': sample_warehouse,
        'items': []
    }
    
    po = create_purchase_order(data=test_data, created_by_user_id=procurement_manager_user.id)
    
    po.status = 'RECEIVED'
    po.save()
    
    with pytest.raises(InvalidOperationException) as exc_info:
        cancel_purchase_order(po_id=po.id, reason="No longer needed")
        
    assert exc_info.value.get_codes() == "PO_CANCELLATION_NOT_ALLOWED"