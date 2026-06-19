from rest_framework import serializers
from .models import Warehouse

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model=Warehouse
        fields=['id','warehouse_code','name','location','city','state','pincode','capacity','is_active','created_at','updated_at']
        read_only_fields=['id','created_at','updated_at']
