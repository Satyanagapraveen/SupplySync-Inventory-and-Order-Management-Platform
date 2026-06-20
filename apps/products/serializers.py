from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    sku=serializers.CharField(required=False,allow_blank=True)
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'description', 'category', 
            'unit_price', 'unit_of_measure', 'reorder_level', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']