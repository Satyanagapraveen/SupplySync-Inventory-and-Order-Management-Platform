from rest_framework import serializers
from .models import PurchaseOrder,PurchaseOrderItem

class PurchaseOrderItemSerializer(serializers.Serializer):
    class Meta:
        model=PurchaseOrderItem
        fields=['id','product','quantity_ordered','quantity_recieved','unit_price']
        read_only_fileds=['id','quantity_recieved']

class PurchaseOrderSerializer(serializers.Serializer):
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