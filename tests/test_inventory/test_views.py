import pytest
from django.urls import reverse
from rest_framework import status

def test_adjust_inventory_returns_200_for_authorized_user(authenticated_staff_client, sample_inventory, mocker):
    mocker.patch('apps.inventory.services.process_inventory_updated_event.delay')
    url = reverse('inventory-adjust')
    data = {
        "product_id": sample_inventory.product.id,
        "warehouse_id": sample_inventory.warehouse.id,
        "transaction_type": "INBOUND",
        "quantity": 10,
        "notes": "API Test"
    }
    response = authenticated_staff_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK

def test_adjust_inventory_returns_403_for_unauthorized_role(authenticated_pm_client, sample_inventory):
    url = reverse('inventory-adjust')
    data = {
        "product_id": sample_inventory.product.id,
        "warehouse_id": sample_inventory.warehouse.id,
        "transaction_type": "INBOUND",
        "quantity": 10
    }
    response = authenticated_pm_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_get_low_stock_alerts_returns_200_with_list(authenticated_wm_client, sample_inventory):
    url = reverse('inventory-low-stock')
    response = authenticated_wm_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)

def test_transfer_inventory_returns_200_with_valid_request(authenticated_wm_client, sample_inventory, sample_warehouse, mocker):
    mocker.patch('apps.inventory.services.process_inventory_transfer_event.delay')
    from apps.warehouses.models import Warehouse
    dest_wh = Warehouse.objects.create(name="Dest WH", warehouse_code="WH-DEST", location="Dest", city="Dest", state="Dest", pincode="123", capacity=100)
    url = reverse('inventory-transfer')
    data = {"product_id": sample_inventory.product.id, "source_warehouse_id": sample_inventory.warehouse.id, "destination_warehouse_id": dest_wh.id, "quantity": 5}
    response = authenticated_wm_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
