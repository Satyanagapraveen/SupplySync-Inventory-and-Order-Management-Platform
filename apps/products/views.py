from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsWarehouseManagerOrAdmin
import django_filters.rest_framework as filters

from .models import Product
from .serializers import ProductSerializer
from .filters import ProductFilter
from .services import create_product, get_product_with_inventory

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsWarehouseManagerOrAdmin()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = create_product(serializer.validated_data)
        response_serializer = self.get_serializer(product)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsWarehouseManagerOrAdmin()]
        return [IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        product_id = self.kwargs.get('pk')
        data = get_product_with_inventory(product_id)
        
        serializer = self.get_serializer(data['product'])
        response_data = serializer.data
        response_data['inventory_by_warehouse'] = data['inventory_by_warehouse']
        
        return Response(response_data)