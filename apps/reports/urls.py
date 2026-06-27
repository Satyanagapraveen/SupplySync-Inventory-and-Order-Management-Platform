from django.urls import path
from .views import DashboardReportView,InventoryValuationReportView,PurchaseOrderSummaryReportView

urlpatterns = [
    path('dashboard/', DashboardReportView.as_view(), name='dashboard-report'),
    path('inventory-valuation/', InventoryValuationReportView.as_view(), name='inventory-valuation-report'),
    path('purchase-orders/summary/', PurchaseOrderSummaryReportView.as_view(), name='purchase-order-summary-report'),
]