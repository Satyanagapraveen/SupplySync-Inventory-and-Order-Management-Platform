from rest_framework import serializers
from .models import SalesOrder, SalesOrderItem

class SalesOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderItem
        fields = ['id', 'product', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['id', 'total_price']

class SalesOrderSerializer(serializers.ModelSerializer):
    # WHAT: The Output Lens for the child items.
    items = SalesOrderItemSerializer(many=True, read_only=True)
     #Bypasses DRF required validation so the service can generate it if needed.
    order_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'customer_name', 'warehouse', 'status',
            'total_amount', 'items', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'total_amount', 'created_by', 'created_at', 'updated_at']

class SOCancelPayloadSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, min_length=5)