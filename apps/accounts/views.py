from rest_framework import generics,status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import RegisterSerializer,LoginSerializer 

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