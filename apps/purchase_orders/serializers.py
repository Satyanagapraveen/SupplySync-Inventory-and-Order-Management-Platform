from rest_framework import serializers
from .models import PurchaseOrder,PurchaseOrderItem
from apps.suppliers.models import Supplier
from apps.warehouses.models import Warehouse
class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=PurchaseOrderItem
        fields=['id','product','quantity_ordered','quantity_received','unit_price','total_price']
        read_only_fileds=['id','quantity_recieved','total_price']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all(), required=True)
    warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all(), required=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    po_number = serializers.CharField(required=False, allow_blank=True)
    class Meta:
        model=PurchaseOrder
        fields=[
            'id','po_number','supplier','warehouse','status',
            'total_amount','items',
            'created_by','approved_by','created_at','updated_at'
        ]
        read_only_fields=['id','status','total_amount','created_by','approved_by','created_at','updated_at']

class POReceiveItemSerializer(serializers.Serializer):
    po_item_id = serializers.IntegerField(required=True)
    quantity_received = serializers.IntegerField(min_value=1, required=True)

class POReceivePayloadSerializer(serializers.Serializer):
    items = POReceiveItemSerializer(many=True, required=True)
    actual_delivery_date = serializers.DateField(required=True)

class POCancelPayloadSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, min_length=5)