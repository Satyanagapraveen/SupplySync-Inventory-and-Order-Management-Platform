from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework import status

def custom_exception_handler(exc,context):
    response=exception_handler(exc,context)

    if response is not None:
        custom_response_data={
            "timestamp":timezone.now().isoformat(),
            "status":response.status_code,
            "error_code":getattr(exc,'default_code','INVALID_REQUEST'),
            "message":str(exc.detail) if not isinstance(exc.detail,dict) else "Validation Error",
            "path":context['request'].path,
            "errors":[]
        }

        if isinstance(exc.detail,dict):
            custom_response_data['error_code']="VALIDATION_FAILED"
            for field,messages in exc.detail.items():
                custom_response_data['errors'].append({
                    "field":field,
                    "message": messages[0] if isinstance(messages,list) else str(messages)
                })
        response.data=custom_response_data
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