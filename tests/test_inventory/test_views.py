import pytest

pytestmark = pytest.mark.django_db

def test_adjust_inventory_returns_200_for_authorized_user(authenticated_staff_client, sample_inventory):
    url = '/api/v1/inventory/adjust/'
    payload = {
        "product_id": sample_inventory.product.id,
        "warehouse_id": sample_inventory.warehouse.id,
        "transaction_type": "INBOUND",
        "quantity": 10,
        "notes": "Restock"
    }
    
    response = authenticated_staff_client.post(url, payload, format='json')
    
    assert response.status_code == 200

def test_adjust_inventory_returns_403_for_unauthorized_role(authenticated_pm_client, sample_inventory):
    url = '/api/v1/inventory/adjust/'
    payload = {
        "product_id": sample_inventory.product.id,
        "warehouse_id": sample_inventory.warehouse.id,
        "transaction_type": "INBOUND",
        "quantity": 10,
        "notes": "Restock"
    }
    
    response = authenticated_pm_client.post(url, payload, format='json')
    
    assert response.status_code == 403

def test_get_low_stock_alerts_returns_200_with_list(authenticated_wm_client, sample_inventory):
    url = '/api/v1/inventory/low-stock/'
    
    response = authenticated_wm_client.get(url)
    
    assert response.status_code == 200
    assert isinstance(response.data, list)

def test_transfer_inventory_returns_200_with_valid_request(authenticated_wm_client, sample_inventory):
    from apps.warehouses.models import Warehouse
    destination_warehouse = Warehouse.objects.create(
        name="Transfer Dest", warehouse_code="WH-TRF", 
        location="123 Transfer St", city="City", 
        state="State", pincode="000000", capacity=100
    )
    
    url = '/api/v1/inventory/transfer/'
    payload = {
        "product_id": sample_inventory.product.id,
        "source_warehouse_id": sample_inventory.warehouse.id,
        "destination_warehouse_id": destination_warehouse.id,
        "quantity": 5,
        "notes": "Moving stock"
    }
    
    response = authenticated_wm_client.post(url, payload, format='json')
    
    assert response.status_code == 200