from rest_framework import generics, status
from rest_framework.response import Response
from core.permissions import IsAdminUser, IsWarehouseManagerOrAdmin, IsProcurementManagerOrAdmin
from .services import get_dashboard_summary,get_inventory_valuation,get_purchase_order_summary,get_sales_order_summary

class DashboardReportView(generics.GenericAPIView):
    
    permission_classes = [IsAdminUser | IsWarehouseManagerOrAdmin | IsProcurementManagerOrAdmin]

    def get(self, request, *args, **kwargs):
        
        summary_data = get_dashboard_summary()
        
        return Response(summary_data, status=status.HTTP_200_OK)
    
class InventoryValuationReportView(generics.GenericAPIView):
    
    permission_classes = [IsAdminUser | IsWarehouseManagerOrAdmin | IsProcurementManagerOrAdmin]

    def get(self, request, *args, **kwargs):
        
        warehouse_id = request.query_params.get('warehouse_id')
        
        if warehouse_id:
            try:
                warehouse_id = int(warehouse_id)
            except ValueError:
                warehouse_id = None

        valuation_data = get_inventory_valuation(warehouse_id)
        
        return Response(valuation_data, status=status.HTTP_200_OK)
    
class PurchaseOrderSummaryReportView(generics.GenericAPIView):
    
    permission_classes = [IsAdminUser | IsWarehouseManagerOrAdmin | IsProcurementManagerOrAdmin]

    def get(self, request, *args, **kwargs):
        
        start_date = request.query_params.get('start_date')
        
        end_date = request.query_params.get('end_date')
        
        supplier_id = request.query_params.get('supplier_id')
        
        status_filter = request.query_params.get('status')

        if supplier_id:
            try:
                supplier_id = int(supplier_id)
            except ValueError:
                supplier_id = None

        summary_data = get_purchase_order_summary(
            start_date=start_date,
            end_date=end_date,
            supplier_id=supplier_id,
            status=status_filter
        )
        
        return Response(summary_data, status=status.HTTP_200_OK)
    
class SalesOrderSummaryReportView(generics.GenericAPIView):
    
    permission_classes = [IsAdminUser | IsWarehouseManagerOrAdmin | IsProcurementManagerOrAdmin]

    def get(self, request, *args, **kwargs):
        
        start_date = request.query_params.get('start_date')
        
        end_date = request.query_params.get('end_date')
        
        warehouse_id = request.query_params.get('warehouse_id')
        
        status_filter = request.query_params.get('status')

        if warehouse_id:
            try:
                warehouse_id = int(warehouse_id)
            except ValueError:
                warehouse_id = None

        summary_data = get_sales_order_summary(
            start_date=start_date,
            end_date=end_date,
            warehouse_id=warehouse_id,
            status=status_filter
        )
        
        return Response(summary_data, status=status.HTTP_200_OK)