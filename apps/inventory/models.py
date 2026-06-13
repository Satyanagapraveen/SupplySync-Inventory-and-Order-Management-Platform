from django.db import models
from core.models import BaseModel
class TransactionType(models.TextChoices):
    INBOUND = 'INBOUND','inbound'
    OUTBOUND ='OUTBOUND','outound'
    ADJUSTMENT = 'ADJUSTMENT', 'adjustment'
    TRANSFER = 'TRANSFER', 'transfer'
    DAMAGE_REPORT = 'DAMAGE_REPORT', 'Damage Report'

class Inventory(BaseModel):
    product=models.ForeignKey('products.Product',on_delete=models.PROTECT)
    warehouse=models.ForeignKey('warehouses.Warehouse',on_delete=models.PROTECT)
    quantity_available=models.IntegerField(default=0)
    quantity_reserved=models.IntegerField(default=0)
    quantity_damaged=models.IntegerField(default=0)

    class Meta:
        db_table='inventory'
        unique_together=[('product' , 'warehouse')]

        def __str__(self):
             return f"{self.product.sku} at { self.warehouse.warehouse_code}"

class InventoryTransaction(models.Model):
    product=models.ForeignKey('products.Product', on_delete=models.PROTECT)
    warehouse=models.ForeignKey('warehouses.Warehouse',on_delete=models.PROTECT)
    transaction_type=models.CharField(max_length=30)
    quantity=models.IntegerField()
    reference_id=models.CharField(max_length=100)
    performed_by=models.ForeignKey('accounts.User',on_delete=models.PROTECT)
    notes=models.TextField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table='inventory_transactions'

        def __str__(self):
            return f"{self.transaction_type} - { self.quantity} of { self.product.sku}"
        
