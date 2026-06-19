from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser
from .models import Warehouse
from .serializers import WarehouseSerializer
from .services import create_warehouse, get_warehouse_with_summary
from core.exceptions import InvalidOperationException
import django_filters.rest_framework as filters

class WarehouseListCreateView(generics.ListCreateAPIView):
    queryset = Warehouse.objects.filter(is_active=True)
    serializer_class = WarehouseSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['city', 'state']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        warehouse = create_warehouse(serializer.validated_data)
        response_serializer = self.get_serializer(warehouse)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        warehouse_id = self.kwargs.get('pk')
        data = get_warehouse_with_summary(warehouse_id)
        
        serializer = self.get_serializer(data['warehouse'])
        response_data = serializer.data
        response_data['inventory_summary'] = data['summary']
        
        return Response(response_data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if 'warehouse_code' in request.data and request.data['warehouse_code'] != instance.warehouse_code:
            raise InvalidOperationException(detail="Warehouse code cannot be changed.", code="WAREHOUSE_CODE_IMMUTABLE")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        from apps.inventory.models import Inventory
        
        has_active_inventory = Inventory.objects.filter(
            warehouse=instance, 
            is_deleted=False
        ).filter(quantity_available__gt=0).exists()
        
        if has_active_inventory:
            return Response(
                {"error_code": "WAREHOUSE_HAS_ACTIVE_INVENTORY", "message": "Cannot delete warehouse with active inventory."},
                status=status.HTTP_409_CONFLICT
            )
            
        instance.is_deleted = True
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)