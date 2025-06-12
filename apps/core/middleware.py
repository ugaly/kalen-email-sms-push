import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from .models import APILog

User = get_user_model()

class APILoggingMiddleware(MiddlewareMixin):
    """Middleware to log API requests and responses"""
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if not request.path.startswith('/api/'):
            return response
        
        response_time = (time.time() - getattr(request, 'start_time', time.time())) * 1000
        
        request_data = {}
        if hasattr(request, 'data'):
            try:
                request_data = dict(request.data)
                sensitive_fields = ['password', 'token', 'api_key']
                for field in sensitive_fields:
                    if field in request_data:
                        request_data[field] = '***'
            except:
                pass
        
        user = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        try:
            APILog.objects.create(
                endpoint=request.path,
                method=request.method,
                user=user,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_data=request_data,
                response_status=response.status_code,
                response_time=response_time
            )
        except Exception:
            pass
        
        return response
