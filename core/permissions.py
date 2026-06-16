from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    message = "Administrator access is required to perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')

class IsWarehouseManagerOrAdmin(BasePermission):
    message = "Warehouse Manager or Administrator access is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'WAREHOUSE_MANAGER'])

class IsProcurementManagerOrAdmin(BasePermission):
    message = "Procurement Manager or Administrator access is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'PROCUREMENT_MANAGER'])

class IsWarehouseManagerOrAdminOrStaff(BasePermission):
    message = "Staff, Warehouse Manager, or Administrator access is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'WAREHOUSE_MANAGER', 'STAFF'])

class IsOwnerOrAdmin(BasePermission):
    message = "You do not have permission to access or modify this specific record."

    def has_object_permission(self, request, view, obj):
        if not bool(request.user and request.user.is_authenticated):
            return False
            
        if request.user.role == 'ADMIN':
            return True
            
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
            
        if hasattr(obj, 'performed_by') and obj.performed_by == request.user:
            return True
            
        return False