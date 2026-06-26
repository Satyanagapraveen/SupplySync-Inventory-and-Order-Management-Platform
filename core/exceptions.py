from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "timestamp": timezone.now().isoformat(),
            "status": response.status_code,
            "error_code": getattr(exc, 'code', 'VALIDATION_FAILED') if response.status_code != 404 else 'NOT_FOUND',
            "message": str(exc.detail) if not isinstance(exc.detail, dict) else "Validation Error",
            "path": context['request'].path,
            "errors": []
        }

        if isinstance(exc.detail, dict):
            for field, value in exc.detail.items():
                error_payload["errors"].append({
                    "field": field,
                    "message": value[0] if isinstance(value, list) else str(value)
                })

        # WHY: To extract the 'short_items' array and pin it perfectly to the root JSON.
        if hasattr(exc, 'short_items'):
            error_payload['short_items'] = exc.short_items

        response.data = error_payload

    return response

class ResourceNotFoundException(APIException):
    status_code=404
    default_code="RESORCE_NOT_FOUND"

class DuplicateResourceException(APIException):
    status_code=409
    default_code="DUPLICATE_RESOURCE"

class InsufficientInventoryException(APIException):
    status_code=422
    default_code="INSUFFICIENT_INVENTORY"

class InvalidOperationException(APIException):
    status_code=422
    default_code="INVALID_OPERATION"
class PermissionDeniedException(APIException):
    status_code = 422
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'PERMISSION_DENIED'

    def __init__(self, detail=None, code=None):
        if detail is not None:
            self.detail = detail
        if code is not None:
            self.code = code

class InsufficientStockException(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Insufficient stock for the requested order.'
    default_code = 'INSUFFICIENT_STOCK_FOR_ORDER'

    def __init__(self, short_items, detail=None, code=None):
        super().__init__(detail=detail or self.default_detail, code=code or self.default_code)
        # WHAT: Stores the array safely inside the class so the handler can grab it later.
        self.short_items = short_items