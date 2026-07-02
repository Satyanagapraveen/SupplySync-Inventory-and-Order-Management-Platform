import pytest
from apps.sales_orders.services import create_sales_order, cancel_sales_order, dispatch_sales_order
from apps.sales_orders.models import SalesOrder
from apps.inventory.models import InventoryTransaction
from core.exceptions import InsufficientStockException, InvalidOperationException

def test_create_sales_order_reserves_inventory_on_creation(db, sample_inventory, staff_user):
    initial_available = sample_inventory.quantity_available
    initial_reserved = sample_inventory.quantity_reserved

    test_data = {
        'customer_name': 'Acme Corp',
        'customer_email': 'contact@acme.com',
        'warehouse_id': sample_inventory.warehouse.id,
        'items': [
            {'product_id': sample_inventory.product.id, 'quantity': 10}
        ]
    }

    order = create_sales_order(data=test_data, created_by_user_id=staff_user.id)
    
    sample_inventory.refresh_from_db()

    assert order.status == 'PENDING'
    assert sample_inventory.quantity_available == initial_available - 10
    assert sample_inventory.quantity_reserved == initial_reserved + 10

def test_create_sales_order_raises_exception_when_insufficient_stock(db, sample_inventory, staff_user):
    initial_available = sample_inventory.quantity_available

    test_data = {
        'customer_name': 'Acme Corp',
        'warehouse_id': sample_inventory.warehouse.id,
        'items': [
            {'product_id': sample_inventory.product.id, 'quantity': 999}
        ]
    }

    with pytest.raises(InsufficientStockException) as exc_info:
        create_sales_order(data=test_data, created_by_user_id=staff_user.id)

    assert exc_info.value.default_code == "INSUFFICIENT_STOCK_FOR_ORDER"
    
    sample_inventory.refresh_from_db()
    assert sample_inventory.quantity_available == initial_available

def test_create_sales_order_dispatches_celery_task_on_success(db, sample_inventory, staff_user, mocker):
    mock_task = mocker.patch('apps.sales_orders.services.process_sales_order_created_event.delay')

    test_data = {
        'customer_name': 'Acme Corp',
        'warehouse_id': sample_inventory.warehouse.id,
        'items': [
            {'product_id': sample_inventory.product.id, 'quantity': 5}
        ]
    }

    order = create_sales_order(data=test_data, created_by_user_id=staff_user.id)

    mock_task.assert_called_once_with(order_id=order.id,created_by_user_id=staff_user.id)

def test_cancel_sales_order_releases_reserved_inventory(db, sample_inventory, staff_user):
    test_data = {
        'customer_name': 'Acme Corp',
        'warehouse_id': sample_inventory.warehouse.id,
        'items': [{'product_id': sample_inventory.product.id, 'quantity': 15}]
    }
    order = create_sales_order(data=test_data, created_by_user_id=staff_user.id)
    
    sample_inventory.refresh_from_db()
    reserved_after_creation = sample_inventory.quantity_reserved

    cancel_sales_order(order_id=order.id, performed_by_user_id=staff_user.id)

    sample_inventory.refresh_from_db()
    order.refresh_from_db()

    assert order.status == 'CANCELLED'
    assert sample_inventory.quantity_reserved == reserved_after_creation - 15
    assert sample_inventory.quantity_available == sample_inventory.quantity_available + 0

def test_cancel_sales_order_raises_exception_when_order_is_already_dispatched(db, sample_inventory, staff_user):
    test_data = {
        'customer_name': 'Acme Corp',
        'warehouse_id': sample_inventory.warehouse.id,
        'items': [{'product_id': sample_inventory.product.id, 'quantity': 5}]
    }
    order = create_sales_order(data=test_data, created_by_user_id=staff_user.id)
    
    order.status = 'DISPATCHED'
    order.save()

    with pytest.raises(InvalidOperationException) as exc_info:
        cancel_sales_order(order_id=order.id, performed_by_user_id=staff_user.id)

    assert exc_info.value.default_code == "INVALID_OPERATION"

def test_dispatch_sales_order_creates_outbound_transactions_for_all_items(db, sample_inventory, staff_user):
    test_data = {
        'customer_name': 'Acme Corp',
        'warehouse_id': sample_inventory.warehouse.id,
        'items': [{'product_id': sample_inventory.product.id, 'quantity': 20}]
    }
    order = create_sales_order(data=test_data, created_by_user_id=staff_user.id)
    
    initial_transactions = InventoryTransaction.objects.count()

    dispatch_sales_order(order_id=order.id, performed_by_user_id=staff_user.id)

    order.refresh_from_db()
    sample_inventory.refresh_from_db()

    assert order.status == 'DISPATCHED'
    assert sample_inventory.quantity_reserved == 0 
    assert InventoryTransaction.objects.count() == initial_transactions + 1
    
    latest_tx = InventoryTransaction.objects.latest('created_at')
    assert latest_tx.transaction_type == 'OUTBOUND'
    assert latest_tx.quantity == 20