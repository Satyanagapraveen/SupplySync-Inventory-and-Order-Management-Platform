from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser
from rest_framework import serializers
from .models import Category
from .serializers import CategorySerializer
from rest_framework import viewsets

class CategoryViewSet(viewsets.ModelViewSet):
    queryset=Category.objects.all
    serializer_class=CategorySerializer

    def get_permissions(self):
        if self.action in ['create','update','partial_update','destroy']:
            self.permission_classes=[IsAdminUser]
        else:
            self.permission_classes=[IsAuthenticated]
        return super().get_permissions()