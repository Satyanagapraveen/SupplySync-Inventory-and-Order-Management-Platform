from django.urls import path
from .views import CategoryListCreateView, CategoryTreeView

urlpatterns = [
    path('', CategoryListCreateView.as_view(), name='category-list'),
    path('tree/', CategoryTreeView.as_view(), name='category-tree'),
]