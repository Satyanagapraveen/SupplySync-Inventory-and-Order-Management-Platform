from rest_framework import generics, status
from rest_framework.response import Response
from core.permissions import IsAdminUser, IsWarehouseManagerOrAdmin, IsProcurementManagerOrAdmin
from .services import get_dashboard_summary

class DashboardReportView(generics.GenericAPIView):
    
    permission_classes = [IsAdminUser | IsWarehouseManagerOrAdmin | IsProcurementManagerOrAdmin]

    def get(self, request, *args, **kwargs):
        
        summary_data = get_dashboard_summary()
        
        return Response(summary_data, status=status.HTTP_200_OK)