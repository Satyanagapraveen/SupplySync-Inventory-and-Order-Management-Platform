import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.warehouses.models import Warehouse
from apps.categories.models import Category
from apps.products.models import Product
from apps.suppliers.models import Supplier
from apps.inventory.models import Inventory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_test",
        email="admin@test.com",
        password="TestPassword123!",
        full_name="Admin User",
        role="ADMIN"
    )

@pytest.fixture
def warehouse_manager_user(db):
    return User.objects.create_user(
        username="wm_test",
        email="wm@test.com",
        password="TestPassword123!",
        full_name="Warehouse Manager",
        role="WAREHOUSE_MANAGER"
    )

@pytest.fixture
def procurement_manager_user(db):
    return User.objects.create_user(
        username="pm_test",
        email="pm@test.com",
        password="TestPassword123!",
        full_name="Procurement Manager",
        role="PROCUREMENT_MANAGER"
    )

@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="staff_test",
        email="staff@test.com",
        password="TestPassword123!",
        full_name="Staff User",
        role="STAFF"
    )

@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def authenticated_wm_client(api_client, warehouse_manager_user):
    api_client.force_authenticate(user=warehouse_manager_user)
    return api_client

@pytest.fixture
def authenticated_pm_client(api_client, procurement_manager_user):
    api_client.force_authenticate(user=procurement_manager_user)
    return api_client

@pytest.fixture
def authenticated_staff_client(api_client, staff_user):
    api_client.force_authenticate(user=staff_user)
    return api_client

@pytest.fixture
def sample_warehouse(db):
    return Warehouse.objects.create(
        name="Test Warehouse",
        warehouse_code="WH-TEST01",
        location="123 Test St",
        city="Test City",
        state="Test State",
        pincode="123456",
        capacity=1000
    )

@pytest.fixture
def sample_category(db):
    return Category.objects.create(
        name="Test Category",
        category_code="CAT-TEST01",
        description="Test Description"
    )

@pytest.fixture
def sample_product(db, sample_category):
    return Product.objects.create(
        name="Test Product",
        sku="SKU-TEST01",
        description="A test product",
        unit_price=100.00,
        reorder_level=10,
        category=sample_category
    )

@pytest.fixture
def sample_supplier(db):
    return Supplier.objects.create(
        name="Test Supplier",
        supplier_code="SUP-TEST01",
        email="supplier@test.com",
        phone="1234567890",
        address="456 Vendor Rd"
    )

@pytest.fixture
def sample_inventory(db, sample_product, sample_warehouse):
    return Inventory.objects.create(
        product=sample_product,
        warehouse=sample_warehouse,
        quantity_available=50,
        quantity_reserved=0
    )