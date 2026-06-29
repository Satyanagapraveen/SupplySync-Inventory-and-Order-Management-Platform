import pytest
from freezegun import freeze_time
from apps.purchase_orders.services import (
    create_purchase_order,
    approve_purchase_order,
    receive_purchase_order,
    cancel_purchase_order
)
from apps.purchase_orders.models import PurchaseOrder, PurchaseOrderItem
from apps.inventory.models import Inventory
from core.exceptions import InvalidOperationException, PermissionDeniedException

@freeze_time("2026-07-15")
def test_create_purchase_order_generates_po_number_with_correct_format(db, sample_supplier, sample_warehouse, procurement_manager_user):
    po_data = {
        "supplier": sample_supplier,
        "warehouse": sample_warehouse,
        "items": []
    }
    po = create_purchase_order(data=po_data, created_by_user_id=procurement_manager_user.id)
    assert po.po_number.startswith("PO-20260715-")

def test_approve_purchase_order_raises_exception_when_approver_is_same_as_creator(db, sample_supplier, sample_warehouse, procurement_manager_user):
    po_data = {"supplier": sample_supplier, "warehouse": sample_warehouse, "items": []}
    po = create_purchase_order(data=po_data, created_by_user_id=procurement_manager_user.id)
    po.status = 'PENDING_APPROVAL'
    po.save()

    with pytest.raises(PermissionDeniedException) as exc_info:
        approve_purchase_order(po_id=po.id, approved_by_user_id=procurement_manager_user.id)
    assert exc_info.value.default_code == "SELF_APPROVAL_NOT_ALLOWED"

def test_approve_purchase_order_raises_exception_when_status_is_not_pending_approval(db, sample_supplier, sample_warehouse, procurement_manager_user, warehouse_manager_user):
    po_data = {"supplier": sample_supplier, "warehouse": sample_warehouse, "items": []}
    po = create_purchase_order(data=po_data, created_by_user_id=procurement_manager_user.id)
    # PO is in DRAFT status, not PENDING_APPROVAL

    with pytest.raises(InvalidOperationException):
        approve_purchase_order(po_id=po.id, approved_by_user_id=warehouse_manager_user.id)

def test_receive_purchase_order_updates_inventory_for_received_items(db, sample_supplier, sample_warehouse, sample_product, procurement_manager_user, staff_user, mocker):
    mocker.patch('apps.inventory.services.process_inventory_updated_event.delay')
    mocker.patch('apps.purchase_orders.tasks.process_purchase_order_receicesed_event.delay')
    
    po_data = {
        "supplier": sample_supplier, "warehouse": sample_warehouse,
        "items": [{"product": sample_product.id, "quantity_ordered": 20, "unit_price": 100.00}]
    }
    po = create_purchase_order(data=po_data, created_by_user_id=procurement_manager_user.id)
    po.status = 'APPROVED'
    po.save()

    initial_inventory, _ = Inventory.objects.get_or_create(product=sample_product, warehouse=sample_warehouse)
    initial_qty = initial_inventory.quantity_available

    receive_data = {
        "items": [{"po_item_id": po.items.first().id, "quantity_received": 15}]
    }
    receive_purchase_order(po_id=po.id, data=receive_data, performed_by_user_id=staff_user.id)

    initial_inventory.refresh_from_db()
    assert initial_inventory.quantity_available == initial_qty + 15

def test_receive_purchase_order_sets_status_to_partially_received_when_not_all_items_received(db, sample_supplier, sample_warehouse, sample_product, procurement_manager_user, mocker):
    mocker.patch('apps.inventory.services.process_inventory_updated_event.delay')
    mocker.patch('apps.purchase_orders.tasks.process_purchase_order_received_event.delay')

    po_data = {
        "supplier": sample_supplier, "warehouse": sample_warehouse,
        "items": [{"product": sample_product.id, "quantity_ordered": 20, "unit_price": 100.00}]
    }
    po = create_purchase_order(data=po_data, created_by_user_id=procurement_manager_user.id)
    po.status = 'APPROVED'
    po.save()

    receive_data = {
        "items": [{"po_item_id": po.items.first().id, "quantity_received": 15}]
    }
    updated_po = receive_purchase_order(po_id=po.id, data=receive_data, performed_by_user_id=procurement_manager_user.id)

    assert updated_po.status == 'PARTIALLY_RECEIVED'

def test_cancel_purchase_order_raises_exception_when_status_is_received(db, sample_supplier, sample_warehouse, procurement_manager_user):
    po_data = {
        "supplier": sample_supplier, "warehouse": sample_warehouse,
        "items": []
    }
    po = create_purchase_order(data=po_data, created_by_user_id=procurement_manager_user.id)
    po.status = 'RECEIVED'
    po.save()

    with pytest.raises(InvalidOperationException) as exc_info:
        cancel_purchase_order(po_id=po.id, reason="Test cancel")
    
    assert exc_info.value.default_code == "PO_CANCELLATION_NOT_ALLOWED"
