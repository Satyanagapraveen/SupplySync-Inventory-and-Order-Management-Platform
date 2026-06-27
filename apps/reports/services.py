from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from core.constants import DASHBOARD_CACHE_TTL
from apps.warehouses.models import Warehouse
from apps.products.models import Product
from apps.suppliers.models import Supplier
from apps.inventory.models import Inventory, InventoryTransaction
from apps.purchase_orders.models import PurchaseOrder
from apps.sales_orders.models import SalesOrder
from django.db.models import Count

def get_dashboard_summary() -> dict:
    
    cache_key = 'reports:dashboard'
    
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data

    total_warehouses = Warehouse.objects.filter(is_active=True, is_deleted=False).count()
    
    total_products = Product.objects.filter(is_active=True, is_deleted=False).count()
    
    total_suppliers = Supplier.objects.filter(is_active=True, is_deleted=False).count()

    inventory_value_agg = Inventory.objects.filter(is_deleted=False).annotate(
        line_value=ExpressionWrapper(
            F('quantity_available') * F('product__unit_price'), 
            output_field=DecimalField()
        )
    ).aggregate(total=Sum('line_value'))
    
    total_inventory_value = inventory_value_agg['total'] or 0.00

    open_purchase_orders = PurchaseOrder.objects.filter(
        status__in=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'PARTIALLY_RECEIVED']
    ).count()

    pending_sales_orders = SalesOrder.objects.filter(
        status__in=['PENDING', 'CONFIRMED']
    ).count()

    low_stock_count = 0
    
    inventories = Inventory.objects.filter(is_deleted=False).select_related('product')
    
    for inv in inventories:
        if inv.quantity_available <= inv.product.reorder_level:
            low_stock_count += 1

    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    top_selling = list(
        InventoryTransaction.objects.filter(
            transaction_type='OUTBOUND',
            created_at__gte=thirty_days_ago
        ).values(
            'product_id', 'product__sku', 'product__name'
        ).annotate(
            total_dispatched=Sum('quantity')
        ).order_by('-total_dispatched')[:5]
    )

    recent_tx = list(
        InventoryTransaction.objects.all().order_by('-created_at')[:10].values(
            'id', 'product_id', 'warehouse_id', 'transaction_type', 'quantity', 'created_at'
        )
    )

    result = {
        "total_warehouses": total_warehouses,
        "total_products": total_products,
        "total_suppliers": total_suppliers,
        "total_inventory_value": str(total_inventory_value),
        "open_purchase_orders": open_purchase_orders,
        "pending_sales_orders": pending_sales_orders,
        "low_stock_product_count": low_stock_count,
        "top_selling_products": top_selling,
        "recent_transactions": recent_tx
    }

    cache.set(cache_key, result, timeout=DASHBOARD_CACHE_TTL)
    
    return result

def get_inventory_valuation(warehouse_id: int = None) -> dict:
    warehouses_query = Warehouse.objects.filter(is_active=True, is_deleted=False)
    
    if warehouse_id:
        warehouses_query = warehouses_query.filter(id=warehouse_id)

    grand_total_value = 0.00
    warehouse_reports = []

    for warehouse in warehouses_query:
        inventory_records = Inventory.objects.filter(
            warehouse=warehouse,
            is_deleted=False
        ).select_related('product')

        products_list = []
        warehouse_total = 0.00

        for inv in inventory_records:
            line_value = float(inv.quantity_available) * float(inv.product.unit_price)
            warehouse_total += line_value

            products_list.append({
                "sku": inv.product.sku,
                "product_name": inv.product.name,
                "quantity_available": inv.quantity_available,
                "unit_price": str(inv.product.unit_price),
                "total_value": str(round(line_value, 2))
            })

        grand_total_value += warehouse_total

        warehouse_reports.append({
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "warehouse_total_value": str(round(warehouse_total, 2)),
            "products": products_list
        })

    return {
        "grand_total_value": str(round(grand_total_value, 2)),
        "warehouses": warehouse_reports
    }

def get_purchase_order_summary(start_date: str = None, end_date: str = None, supplier_id: int = None, status: str = None) -> dict:
    
    qs = PurchaseOrder.objects.filter(is_deleted=False)
    
    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
        
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)
        
    if supplier_id:
        qs = qs.filter(supplier_id=supplier_id)
        
    if status:
        qs = qs.filter(status=status)

    total_orders = qs.count()

    value_agg = qs.aggregate(total=Sum('total_amount'))
    
    total_value = value_agg['total'] or 0.00

    breakdown_by_status = list(
        qs.values('status')
        .annotate(
            count=Count('id'), 
            total_value=Sum('total_amount')
        )
        .order_by('status')
    )

    top_suppliers = list(
        qs.values('supplier_id', 'supplier__name')
        .annotate(
            total_value=Sum('total_amount')
        )
        .order_by('-total_value')[:5]
    )

    return {
        "total_orders": total_orders,
        "total_value": str(round(total_value, 2)),
        "breakdown_by_status": breakdown_by_status,
        "top_suppliers": top_suppliers
    }