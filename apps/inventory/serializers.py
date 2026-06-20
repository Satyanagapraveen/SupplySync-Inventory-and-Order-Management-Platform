from rest_framework import serializers

class AdjustInventorySerializer(serializers.Serializer):
    product_id=serializers.IntegerField(required=True)
    warehouse_id=serializers.IntegerField(required=True)
    transaction_type=serializers.ChoiceField(choices=['INBOUND','OUTBOUND','DAMAGE_REPORT','ADJUSTMENT'] )
    quantity=serializers.IntegerField(required=True)
    notes=serializers.CharField(required=False,allow_blank=True)

class TransferInventorySerializer(serializers.Serializer):
    product_id=serializers.IntegerField(required=True)
    source_warehouse_id=serializers.IntegerField(required=True)
    destination_warehouse_id=serializers.IntegerField(required=True)
    quantity=serializers.IntegerField(required=True)
    notes=serializers.CharField(required=False,allow_blank=True)

from .models import Inventory

class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'product_name', 'sku', 'warehouse', 
            'quantity_available', 'quantity_reserved', 'quantity_damaged'
        ]
