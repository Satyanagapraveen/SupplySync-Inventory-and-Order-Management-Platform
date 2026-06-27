from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from core.exceptions import InvalidOperationException
from .models import User

def register_user(data: dict) -> dict:
    user = User.objects.create_user(
        email=data['email'],
        password=data['password'],
        username=data['username'],
        full_name=data['full_name'],
        role=data['role']
    )
    
    refresh = RefreshToken.for_user(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh)
    }

def login_user(email: str, password: str) -> dict | None:
    user = authenticate(email=email, password=password)
    
    if not user:
        return None
        
    user.last_login_at = timezone.now()
    user.save(update_fields=['last_login_at'])
    
    refresh = RefreshToken.for_user(user)
    
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }

def logout_user(refresh_token_str: str) -> None:
    try:
        token = RefreshToken(refresh_token_str)
        token.blacklist()
    except Exception:
        raise InvalidOperationException(detail="Invalid or expired token", code="INVALID_TOKEN")

def change_password(user: User, old_password: str, new_password: str) -> None:
    if not user.check_password(old_password):
        raise InvalidOperationException(detail="Wrong password.", code="INVALID_PASSWORD")
        
    user.set_password(new_password)
    user.save(update_fields=['password'])