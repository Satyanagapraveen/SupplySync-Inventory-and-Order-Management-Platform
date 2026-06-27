from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from core.throttles import LoginRateLimitThrottle
from core.exceptions import InvalidOperationException
from .serializers import RegisterSerializer, LoginSerializer, LogoutSerializer, ChangePasswordSerializer
from .services import authenticate_user

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    throttle_classes = [LoginRateLimitThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ip_address = get_client_ip(request)
        cache_key = f"rate-limit:login:{ip_address}"
        
        user = authenticate_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )        
        
        if not user:
            cache.add(cache_key, 0, timeout=900)
            cache.incr(cache_key)
            raise InvalidOperationException(detail="Invalid credentials", code="INVALID_CREDENTIALS")
            
        cache.delete(cache_key)
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    
class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data['refresh_token'])
            token.blacklist()
            return Response({"detail": "Successfully Logged out."}, status=status.HTTP_200_OK)
        except Exception:
            raise InvalidOperationException(detail="Invalid or expired token", code="INVALID_TOKEN")

class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def get_object(self):
        return self.request.user
        
    def put(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not self.object.check_password(serializer.validated_data.get("old_password")):
            raise InvalidOperationException(detail="Wrong password.", code="INVALID_PASSWORD")

        self.object.set_password(serializer.validated_data.get("new_password"))
        self.object.save()
        
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)