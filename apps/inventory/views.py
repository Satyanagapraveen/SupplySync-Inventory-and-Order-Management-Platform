from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsWarehouseManagerOrAdminOrStaff, IsWarehouseManagerOrAdmin
from .models import Inventory
from .serializers import AdjustInventorySerializer, TransferInventorySerializer, InventorySerializer
from .services import adjust_inventory, transfer_inventory, get_low_stock_alerts

class InventoryAdjustView(generics.GenericAPIView):
    serializer_class = AdjustInventorySerializer
    permission_classes = [IsWarehouseManagerOrAdminOrStaff]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tx_record = adjust_inventory(serializer.validated_data, request.user.id)
        return Response(
            {"detail": "Inventory adjusted successfully.", "reference_id": tx_record.reference_id},
            status=status.HTTP_200_OK
        )

class InventoryTransferView(generics.GenericAPIView):
    serializer_class = TransferInventorySerializer
    permission_classes = [IsWarehouseManagerOrAdminOrStaff]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = transfer_inventory(serializer.validated_data, request.user.id)
        return Response(
            {"detail": "Inventory transferred successfully.", "reference_id": result['outbound'].reference_id},
            status=status.HTTP_200_OK
        )

class LowStockAlertView(generics.GenericAPIView):
    permission_classes = [IsWarehouseManagerOrAdmin]

    def get(self, request, *args, **kwargs):
        alerts = get_low_stock_alerts()
        return Response(alerts, status=status.HTTP_200_OK)

class WarehouseInventoryView(generics.ListAPIView):
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        warehouse_id = self.kwargs.get('warehouse_id')
        return Inventory.objects.filter(warehouse_id=warehouse_id, is_deleted=False)