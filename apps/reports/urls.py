from django.urls import path
from .views import DashboardReportView,InventoryValuationReportView

urlpatterns = [
    path('dashboard/', DashboardReportView.as_view(), name='dashboard-report'),
    path('inventory-valuation/', InventoryValuationReportView.as_view(), name='inventory-valuation-report'),
]