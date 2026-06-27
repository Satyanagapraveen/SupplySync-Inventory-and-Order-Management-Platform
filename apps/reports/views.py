from rest_framework import generics, status
from rest_framework.response import Response
from core.permissions import IsAdminUser, IsWarehouseManagerOrAdmin, IsProcurementManagerOrAdmin
from .services import get_dashboard_summary,get_inventory_valuation

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