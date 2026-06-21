from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsProcurementManagerOrAdmin, IsWarehouseManagerOrAdmin

from .models import PurchaseOrder
from .serializers import PurchaseOrderSerializer, POReceivePayloadSerializer, POCancelPayloadSerializer
from .services import (
    create_purchase_order, submit_purchase_order, 
    approve_purchase_order, receive_purchase_order, cancel_purchase_order
)

class PurchaseOrderListCreateView(generics.ListCreateAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsProcurementManagerOrAdmin()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po = create_purchase_order(serializer.validated_data, request.user.id)
        response_serializer = self.get_serializer(po)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class PurchaseOrderSubmitView(generics.GenericAPIView):
    permission_classes = [IsProcurementManagerOrAdmin]

    def post(self, request, pk, *args, **kwargs):
        po = submit_purchase_order(pk)
        serializer = PurchaseOrderSerializer(po)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PurchaseOrderApproveView(generics.GenericAPIView):
    permission_classes = [IsWarehouseManagerOrAdmin]

    def post(self, request, pk, *args, **kwargs):
        po = approve_purchase_order(pk, request.user.id)
        serializer = PurchaseOrderSerializer(po)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PurchaseOrderReceiveView(generics.GenericAPIView):
    serializer_class = POReceivePayloadSerializer
    permission_classes = [IsWarehouseManagerOrAdmin]

    def post(self, request, pk, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po = receive_purchase_order(pk, serializer.validated_data, request.user.id)
        response_serializer = PurchaseOrderSerializer(po)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

class PurchaseOrderCancelView(generics.GenericAPIView):
    serializer_class = POCancelPayloadSerializer
    permission_classes = [IsProcurementManagerOrAdmin]

    def post(self, request, pk, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po = cancel_purchase_order(pk, serializer.validated_data['reason'])
        response_serializer = PurchaseOrderSerializer(po)
        return Response(response_serializer.data, status=status.HTTP_200_OK)