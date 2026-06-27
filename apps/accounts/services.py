from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User

def authenticate_user(email: str, password: str) -> User | None:
    user = authenticate(email=email, password=password)
    
    if user:
        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])
        
    return user