import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

# 1. API Client
@pytest.fixture
def api_client():
    return APIClient()

# 2. User Factories
@pytest.fixture
def user_factory(db):
    def create_user(username, email, password, role, is_staff=False, is_superuser=False, full_name=None):
        User = get_user_model()
        if full_name is None:
            full_name = username.replace("_", " ").title()
            
        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password, 
            role=role,
            full_name=full_name
        )
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()
        return user
    return create_user

@pytest.fixture
def admin_user(user_factory):
    return user_factory("admin", "admin@sync.com", "pass", role="ADMIN", is_staff=True, is_superuser=True)

@pytest.fixture
def warehouse_manager_user(user_factory):
    return user_factory("wm_user", "wm@sync.com", "pass", role="WAREHOUSE_MANAGER", is_staff=True)

@pytest.fixture
def procurement_manager_user(user_factory):
    return user_factory("pm_user", "pm@sync.com", "pass", role="PROCUREMENT_MANAGER", is_staff=True)

@pytest.fixture
def staff_user(user_factory):
    return user_factory("staff_user", "staff@sync.com", "pass", role="STAFF")

# 3. Authenticated Client Factories
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

# 4. Inventory Data Factories
@pytest.fixture
def sample_warehouse(db):
    from apps.warehouses.models import Warehouse
    return Warehouse.objects.create(
        name="Central Hub", 
        location="Hyderabad",
        capacity=10000
    )

@pytest.fixture
def sample_category(db):
    from apps.categories.models import Category
    return Category.objects.create(name="Electronics")

@pytest.fixture
def sample_product(db, sample_category):
    from apps.products.models import Product
    return Product.objects.create(
        name="Laptop", 
        sku="LP-PRO-15",
        category=sample_category, 
        reorder_level=5,
        unit_price=1200.00
    )

@pytest.fixture
def sample_supplier(db):
    from apps.suppliers.models import Supplier
    return Supplier.objects.create(name="Global Tech Corp", contact_email="sales@gtc.com")

@pytest.fixture
def sample_inventory(db, sample_product, sample_warehouse):
    from apps.inventory.models import Inventory
    return Inventory.objects.create(
        product=sample_product, 
        warehouse=sample_warehouse, 
        quantity_available=100
    )