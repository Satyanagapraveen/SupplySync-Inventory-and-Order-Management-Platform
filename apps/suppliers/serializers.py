from rest_framework import serializers
from .models import Supplier

class SupplierSerializer(serializers.ModelSerializer):
    # THE FIX: Allow the client to omit the supplier_code for auto-generation
    supplier_code = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Supplier
        fields = [
            'id', 'supplier_code', 'name', 'contact_person', 'email', 
            'phone', 'address', 'city', 'state', 'pincode', 'gstin', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']