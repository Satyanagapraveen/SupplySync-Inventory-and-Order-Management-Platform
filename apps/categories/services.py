import random
import string
import logging
from django.core.cache import cache
from core.exceptions import DuplicateResourceException
from core.constants import CATEGORY_CACHE_TTL
from .models import Category

logger = logging.getLogger(__name__)

def generate_category_code() -> str:
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"CAT-{random_str}"

def get_category_tree() -> list:
    cache_key = 'categories:tree'
    
    cached_tree = cache.get(cache_key)
    if cached_tree:
        return cached_tree
        
    tree = list(Category.objects.filter(parent_category__isnull=True, is_deleted=False).prefetch_related('children'))
    
    cache.set(cache_key, tree, timeout=CATEGORY_CACHE_TTL)
    return tree

def invalidate_category_cache():
    cache.delete('categories:tree')

def create_category(data: dict) -> Category:
    if 'category_code' not in data or not data['category_code']:
        data['category_code'] = generate_category_code()
        
    if Category.objects.filter(category_code=data['category_code']).exists():
        raise DuplicateResourceException(detail="Category code already exists.", code="DUPLICATE_CODE")
        
    category = Category.objects.create(**data)
    
    invalidate_category_cache()
    
    return category