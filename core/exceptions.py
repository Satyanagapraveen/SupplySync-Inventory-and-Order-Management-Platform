from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError, NotAuthenticated, PermissionDenied
from django.utils import timezone
from django.http import JsonResponse
from rest_framework import status

def custom_exception_handler(exc, context):
    
    response = exception_handler(exc, context)

    if response is not None:
        
        if isinstance(exc, ValidationError):
            error_code = 'VALIDATION_ERROR'
        elif isinstance(exc, NotAuthenticated):
            error_code = 'NOT_AUTHENTICATED'
        elif isinstance(exc, PermissionDenied):
            error_code = 'PERMISSION_DENIED'
        else:
            error_code = getattr(exc, 'default_code', getattr(exc, 'code', 'UNKNOWN_ERROR'))
            if response.status_code == 404 and error_code == 'UNKNOWN_ERROR':
                error_code = 'NOT_FOUND'

        error_payload = {
            "timestamp": timezone.now().isoformat(),
            "status": response.status_code,
            "error_code": error_code,
            "message": str(exc.detail) if not isinstance(exc.detail, dict) and not isinstance(exc.detail, list) else "Validation Error",
            "path": context['request'].path,
            "errors": []
        }

        if isinstance(exc.detail, dict):
            for field, value in exc.detail.items():
                error_payload["errors"].append({
                    "field": field,
                    "message": value[0] if isinstance(value, list) else str(value)
                })

        if hasattr(exc, 'short_items'):
            error_payload['short_items'] = exc.short_items

        response.data = error_payload
        
        return response

    error_payload = {
        "timestamp": timezone.now().isoformat(),
        "status": 500,
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected server error occurred.",
        "path": context['request'].path,
        "errors": []
    }
    
    return JsonResponse(error_payload, status=500)

class ResourceNotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found.'
    default_code = 'RESOURCE_NOT_FOUND'

class DuplicateResourceException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Resource already exists.'
    default_code = 'DUPLICATE_RESOURCE'

class InsufficientInventoryException(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Insufficient inventory available.'
    default_code = 'INSUFFICIENT_INVENTORY'

class InvalidOperationException(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Invalid operation.'
    default_code = 'INVALID_OPERATION'

class PermissionDeniedException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'PERMISSION_DENIED'


class InsufficientStockException(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Insufficient stock for the requested order.'
    default_code = 'INSUFFICIENT_STOCK_FOR_ORDER'

    def __init__(self, short_items, detail=None, code=None):
        super().__init__(detail=detail or self.default_detail, code=code or self.default_code)
        self.short_items = short_items