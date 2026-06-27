import random
import string
import logging
from django.db import transaction
from django.db.models import Sum
from django.core.cache import cache
from core.constants import WAREHOUSE_CACHE_TTL
from core.exceptions import InvalidOperationException, DuplicateResourceException
from .models import Warehouse

logger = logging.getLogger(__name__)

def generate_warehouse_code() -> str:
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"WH-{random_str}"

def get_warehouse(warehouse_id: int):
    cache_key = f'warehouses:detail:{warehouse_id}'
    
    cached_warehouse = cache.get(cache_key)
    if cached_warehouse:
        return cached_warehouse
        
    warehouse = Warehouse.objects.get(id=warehouse_id)
    cache.set(cache_key, warehouse, timeout=WAREHOUSE_CACHE_TTL)
    
    return warehouse

def get_warehouse_with_summary(warehouse_id: int) -> dict:
    from apps.inventory.models import Inventory
    
    # WHAT: Bypassing direct DB lookup by using our cached function as the base.
    warehouse = get_warehouse(warehouse_id)
    inventory_qs = Inventory.objects.filter(warehouse=warehouse, is_deleted=False)
    
    total_distinct_products = inventory_qs.values('product').distinct().count()
    total_quantity = inventory_qs.aggregate(total=Sum('quantity_available'))['total'] or 0
    
    return {
        "warehouse": warehouse,
        "summary": {
            "total_distinct_products": total_distinct_products,
            "total_quantity_available": total_quantity
        }
    }

def get_all_warehouses():
    cache_key = 'warehouses:list'
    
    cached_list = cache.get(cache_key)
    if cached_list:
        return cached_list
        
    warehouses = list(Warehouse.objects.filter(is_deleted=False))
    cache.set(cache_key, warehouses, timeout=WAREHOUSE_CACHE_TTL)
    
    return warehouses

def invalidate_warehouse_cache(warehouse_id: int = None):
    cache.delete('warehouses:list')
    if warehouse_id:
        cache.delete(f'warehouses:detail:{warehouse_id}')

def create_warehouse(data: dict) -> Warehouse:
    if 'warehouse_code' not in data or not data['warehouse_code']:
        data['warehouse_code'] = generate_warehouse_code()
    
    if Warehouse.objects.filter(warehouse_code=data['warehouse_code']).exists():
        raise DuplicateResourceException(detail="Warehouse code already exists.", code="DUPLICATE_CODE")
        
    warehouse = Warehouse.objects.create(**data)
    
    # Destroys the stale list cache so the new warehouse appears instantly.
    invalidate_warehouse_cache()
    
    return warehouse