import random
import string
from .models import Product
from core.exceptions import DuplicateResourceException

def generate_sku(category_code: str) -> str:
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"SKU-{category_code}-{random_str}"

def create_product(data: dict) -> Product:
    if 'sku' not in data or not data['sku']:
        category = data.get('category')
        data['sku'] = generate_sku(category.category_code)
        
    if Product.objects.filter(sku=data['sku']).exists():
        raise DuplicateResourceException(detail="SKU already exists.", code="DUPLICATE_SKU")
        
    product = Product.objects.create(**data)
    return product

def get_product_with_inventory(product_id: int) -> dict:
    from apps.inventory.models import Inventory
    
    product = Product.objects.get(id=product_id)
    inventory_records = Inventory.objects.filter(product=product, is_deleted=False).select_related('warehouse')
    
    inventory_by_warehouse = []
    for inv in inventory_records:
        inventory_by_warehouse.append({
            "warehouse_id": inv.warehouse.id,
            "warehouse_name": inv.warehouse.name,
            "quantity_available": inv.quantity_available,
            "quantity_reserved": inv.quantity_reserved
        })
        
    return {
        "product": product,
        "inventory_by_warehouse": inventory_by_warehouse
    }
import logging
from django.core.cache import cache
from core.constants import PRODUCT_CACHE_TTL
from .models import Product

logger = logging.getLogger(__name__)

def get_product_with_inventory(product_id: int) -> dict:
    cache_key = f'products:detail:{product_id}'
    
    cached = cache.get(cache_key)
    if cached:
        return cached
        
    product = Product.objects.get(id=product_id)
    
    result = {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "inventory_data": "aggregate_logic_here"
    }
    
    cache.set(cache_key, result, timeout=PRODUCT_CACHE_TTL)
    return result

def get_all_products():
    cache_key = 'products:list'
    
    cached_list = cache.get(cache_key)
    if cached_list:
        return cached_list
        
    products = list(Product.objects.filter(is_deleted=False))
    
    cache.set(cache_key, products, timeout=PRODUCT_CACHE_TTL)
    return products

def invalidate_product_cache(product_id: int = None):
    cache.delete('products:list')
    
    if product_id:
        cache.delete(f'products:detail:{product_id}')