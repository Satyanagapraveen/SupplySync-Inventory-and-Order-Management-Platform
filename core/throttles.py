from rest_framework.throttling import SimpleRateThrottle
from rest_framework.exceptions import APIException
from rest_framework import status

class TooManyLoginAttemptsException(APIException):
    status_code=status.HTTP_429_TOO_MANY_REQUESTS
    default_code='TOO_MANY_LOGIN_ATTEMPTS'
    default_detail='Too many failed Login attempts'

class LoginRateLimitThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        ident=self.get_ident(request)
        return f"rate-limit:login:{ident}"
        
    def allow_request(self, request, view):
        self.key = self.get_cache_key(request, view)
        
        if self.key is None:
            return True
            
        attempts = self.cache.get(self.key, 0)
        
        if attempts >= 5:
            raise TooManyLoginAttemptsException()
            
        return True
    
