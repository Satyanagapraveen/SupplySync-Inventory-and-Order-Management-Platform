import pytest
from django.contrib.auth import get_user_model

# 1. API Client
@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

# 2. Users
@pytest.fixture
def staff_user(db):
    User = get_user_model()
    return User.objects.create_user(username="staff1", email="staff@supplysync.com", password="password123")

@pytest.fixture
def admin_user(db):
    User = get_user_model()
    return User.objects.create_superuser("admin", "admin@sync.com", "pass")

# 3. Inventory Data
@pytest.fixture
def sample_warehouse(db):
    from apps.inventory.models import Warehouse
    return Warehouse.objects.create(name="Central Hub", location="Hyderabad")

@pytest.fixture
def sample_category(db):
    from apps.inventory.models import Category
    return Category.objects.create(name="Electronics")

@pytest.fixture
def sample_product(db, sample_category):
    from apps.inventory.models import Product
    return Product.objects.create(name="Laptop", category=sample_category, reorder_level=5)

@pytest.fixture
def sample_inventory(db, sample_product, sample_warehouse):
    from apps.inventory.models import Inventory
    return Inventory.objects.create(product=sample_product, warehouse=sample_warehouse, stock_level=100)