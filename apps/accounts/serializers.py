from rest_framework import serializers
from .validators import validate_password_strength

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password_strength])
    full_name = serializers.CharField(max_length=150, required=True)
    role = serializers.CharField(max_length=30, required=True)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password_strength])