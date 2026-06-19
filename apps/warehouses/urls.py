from django.urls import path
from .views import WarehouseListCreateView, WarehouseDetailView

urlpatterns = [
    path('', WarehouseListCreateView.as_view(), name='warehouse-list'),
    path('<int:pk>/', WarehouseDetailView.as_view(), name='warehouse-detail'),
]