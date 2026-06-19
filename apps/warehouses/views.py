from rest_framework import viewsets 
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser
from .serializers import WarehouseSerializer
from .models import Warehouse

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset=Warehouse.objects.all()
    serializer_class=WarehouseSerializer
    def get_permissions(self):
        if self.action in ['create','update','partial_update','destroy']:
            self.permission_classes=[IsAdminUser]
        else:
            self.permission_classes=[IsAuthenticated]
        return super().get_permissions()
    

