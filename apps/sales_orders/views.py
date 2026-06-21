from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SalesOrder
from .serializers import SalesOrderSerializer, SOCancelPayloadSerializer
from .services import create_sales_order, dispatch_sales_order, deliver_sales_order, cancel_sales_order

class SalesOrderListCreateView(generics.ListCreateAPIView):
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Bypassing DRF nested extraction logic just like we did for POs
        clean_data = serializer.validated_data
        clean_data['items'] = request.data.get('items', [])
        
        so = create_sales_order(clean_data, request.user.id)
        response_serializer = self.get_serializer(so)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class SalesOrderDispatchView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk, *args, **kwargs):
        so = dispatch_sales_order(pk)
        serializer = SalesOrderSerializer(so)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SalesOrderDeliverView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk, *args, **kwargs):
        so = deliver_sales_order(pk)
        serializer = SalesOrderSerializer(so)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SalesOrderCancelView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SOCancelPayloadSerializer
    
    def post(self, request, pk, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        so = cancel_sales_order(pk, serializer.validated_data['reason'])
        serializer = SalesOrderSerializer(so)
        return Response(serializer.data, status=status.HTTP_200_OK)