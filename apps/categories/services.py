import random
import string
from .models import Category
from core.exceptions import DuplicateResourceException

def generate_category_code() -> str:
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"CAT-{random_str}"

def create_category(data: dict) -> Category:
    if 'category_code' not in data or not data['category_code']:
        data['category_code'] = generate_category_code()
        
    if Category.objects.filter(category_code=data['category_code']).exists():
        raise DuplicateResourceException(detail="Category code already exists.", code="DUPLICATE_CODE")
        
    category = Category.objects.create(**data)
    return category

def get_category_tree() -> list:
    root_categories = Category.objects.filter(parent_category__isnull=True).prefetch_related('children')
    return root_categories