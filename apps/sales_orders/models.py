from django.db import models
from core.models import BaseModel

class SalesOrderStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    PROCESSING = 'PROCESSING', 'Processing'
    DISPATCHED = 'DISPATCHED', 'Dispatched'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELLED = 'CANCELLED', 'Cancelled'
    RETURNED = 'RETURNED', 'Returned'

class SalesOrder(BaseModel):
    order_number = models.CharField(max_length=30, unique=True)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    warehouse = models.ForeignKey('warehouses.Warehouse', on_delete=models.PROTECT)
    status = models.CharField(max_length=30, choices=SalesOrderStatus.choices)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'sales_orders'

    def __str__(self):
        return self.order_number

class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sales_order_items'

    def __str__(self):
        return f"{self.quantity}x {self.product.sku} for {self.sales_order.order_number}"