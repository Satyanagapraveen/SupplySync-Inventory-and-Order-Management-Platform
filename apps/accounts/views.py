from rest_framework import generics,status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from .serializers import RegisterSerializer,LoginSerializer,LogoutSerializer,ChangePasswordSerializer
from rest_framework_simplejwt import tokens,token_blacklist
class RegisterView(generics.CreateAPIView):
    permission_classes=[AllowAny]
    serializer_class=RegisterSerializer

class LoginView(generics.CreateAPIView):
    permission_classes=[AllowAny]
    serializer_class=LoginSerializer

    def post(self,*args,**kwargs):
        serializer=self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_Exception=True)
        return Response(serializer.validated_data,status=status.HTTP_200_OK)
    
class LogoutView(generics.GenericAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=LogoutSerializer
    def post(self,request,*args, **kwargs):
        serializer=self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_Exception=True)
        try:
            token=RefreshToken(serializer.validated_data['refresh_token'])
            token.blacklist()
            return Response({"detail":"Successfully Logged out!."},status=status.HTTP_200_OK)
        except Exception:
         raise Response({"detail":"Invalid or expired token"},status=status.HTTP_400_BAD_REQUEST)
class ChangePasswordView(generics.GenericAPIView):
    permisssion_classes=[IsAuthenticated]
    serializer=ChangePasswordSerializer
    def get_object(self):
        return self.request.user
    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not self.object.check_password(serializer.validated_data.get("old_password")):
            return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)

        self.object.set_password(serializer.validated_data.get("new_password"))
        self.object.save()
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)

        

