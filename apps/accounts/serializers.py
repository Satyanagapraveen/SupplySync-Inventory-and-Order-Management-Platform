from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate 
from .validators import validate_password_strength
from .models import User
from django.utils import timezone

class RegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True,validators=[validate_password_strength])
    access_token=serializers.SerializerMethodField()
    refresh_token=serializers.SerializerMethodField()

    class Meta:
        model= User
        fields=['id','username','email','password','full_name','role','access_token','refresh_token']

    def create(self,validated_data):
        user=User.objects.create_user(**validated_data)
        return user
    def get_access_token(self,obj):
        refresh=RefreshToken.for_user(obj)
        return str(refresh.access_token)
    
    def get_refresh_token(self,obj):
        refresh=RefreshToken.for_user(obj)
        return str(refresh)
    
class LoginSerializer(serializers.Serializer):
    email=serializers.EmailField()
    password=serializers.CharField(write_only=True)
    def validate(self, attrs):
        email=attrs.get('email')
        password=attrs.get('password')
        user=authenticate(request=self.context.get('request'),email=email,password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password",code='authorization')
        user.last_login_at=timezone.now()
        user.save(update_fields=['last_login_at'])
        refresh=RefreshToken.for_user(user)
        return{
            'access_token':str(refresh.access_token),
            'refresh_token':str(refresh),
            'user_id':user.id,
            'username':user.username,
            'role':user.role
        }

