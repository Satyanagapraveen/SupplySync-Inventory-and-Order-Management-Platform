from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')

class IsWarehouseManager(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'WAREHOUSE_MANAGER'])

class IsProcurementManager(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'PROCUREMENT_MANAGER'])

class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)