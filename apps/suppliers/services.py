import random
import string
import logging
from django.db.models import QuerySet
from django.core.cache import cache
from core.exceptions import DuplicateResourceException
from core.constants import SUPPLIER_CACHE_TTL
from .models import Supplier

logger = logging.getLogger(__name__)

def generate_supplier_code() -> str:
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SUP-{random_str}"

def get_supplier(supplier_id: int) -> Supplier:
    cache_key = f'suppliers:detail:{supplier_id}'
    
    cached_supplier = cache.get(cache_key)
    if cached_supplier:
        return cached_supplier
        
    supplier = Supplier.objects.get(id=supplier_id)
    cache.set(cache_key, supplier, timeout=SUPPLIER_CACHE_TTL)
    
    return supplier

def invalidate_supplier_cache(supplier_id: int):
    if supplier_id:
        cache.delete(f'suppliers:detail:{supplier_id}')

def create_supplier(data: dict) -> Supplier:
    if 'supplier_code' not in data or not data['supplier_code']:
        data['supplier_code'] = generate_supplier_code()
        
    if Supplier.objects.filter(supplier_code=data['supplier_code']).exists():
        raise DuplicateResourceException(detail="Supplier code already exists.", code="DUPLICATE_SUPPLIER_CODE")
        
    return Supplier.objects.create(**data)

def update_supplier(supplier_id: int, data: dict) -> Supplier:
    supplier = get_supplier(supplier_id)
    
    if 'supplier_code' in data and data['supplier_code'] != supplier.supplier_code:
        data.pop('supplier_code')
        
    for key, value in data.items():
        setattr(supplier, key, value)
        
    supplier.save()
    invalidate_supplier_cache(supplier_id)
    
    return supplier

def delete_supplier(supplier_id: int) -> None:
    supplier = get_supplier(supplier_id)
    supplier.is_active = False
    supplier.is_deleted = True
    supplier.save()
    invalidate_supplier_cache(supplier_id)

def list_suppliers(filters: dict, page: int, page_size: int) -> QuerySet:
    queryset = Supplier.objects.filter(is_active=True, is_deleted=False)
    
    if 'city' in filters and filters['city']:
        queryset = queryset.filter(city__iexact=filters['city'])
    if 'state' in filters and filters['state']:
        queryset = queryset.filter(state__iexact=filters['state'])
        
    start = (page - 1) * page_size
    end = start + page_size
    return queryset[start:end]