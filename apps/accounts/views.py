from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from core.throttles import LoginRateLimitThrottle
from core.exceptions import InvalidOperationException
from .serializers import RegisterSerializer, LoginSerializer, LogoutSerializer, ChangePasswordSerializer
from .services import register_user, login_user, logout_user, change_password

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

class RegisterView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        response_data = register_user(serializer.validated_data)
        
        return Response(response_data, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    throttle_classes = [LoginRateLimitThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ip_address = get_client_ip(request)
        cache_key = f"rate-limit:login:{ip_address}"
        
        response_data = login_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )        
        
        if not response_data:
            cache.add(cache_key, 0, timeout=900)
            cache.incr(cache_key)
            raise InvalidOperationException(detail="Invalid credentials", code="INVALID_CREDENTIALS")
            
        cache.delete(cache_key)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        logout_user(serializer.validated_data['refresh_token'])
        
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)

class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
        
    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change_password(
            user=request.user,
            old_password=serializer.validated_data['old_password'],
            new_password=serializer.validated_data['new_password']
        )
        
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)