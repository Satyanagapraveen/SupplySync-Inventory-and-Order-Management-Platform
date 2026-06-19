from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsWarehouseManagerOrAdmin
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsWarehouseManagerOrAdmin]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()