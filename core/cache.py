# core/cache.py
# Cache middleware and utilities

from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.utils.cache import get_cache_key
from django.http import HttpResponse
import hashlib
import json

class CacheMiddleware(MiddlewareMixin):
    """Middleware for caching responses"""
    
    def process_request(self, request):
        # Only cache GET requests
        if request.method != 'GET':
            return None
        
        # Skip caching for admin and API endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/api/'):
            return None
        
        # Generate cache key
        cache_key = self.generate_cache_key(request)
        cached_response = cache.get(cache_key)
        
        if cached_response:
            return HttpResponse(
                cached_response['content'],
                status=cached_response['status'],
                content_type=cached_response['content_type']
            )
        
        # Store request for later processing
        request._cache_key = cache_key
        
        return None
    
    def process_response(self, request, response):
        # Only cache successful responses
        if (hasattr(request, '_cache_key') and 
            response.status_code == 200 and 
            request.method == 'GET'):
            
            cache.set(
                request._cache_key,
                {
                    'content': response.content,
                    'status': response.status_code,
                    'content_type': response.get('Content-Type', 'text/html')
                },
                300  # 5 minutes
            )
        
        return response
    
    def generate_cache_key(self, request):
        """Generate cache key for request"""
        key_data = {
            'path': request.path,
            'query': request.GET.urlencode(),
            'user': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            'company': getattr(request, 'company', None).id if hasattr(request, 'company') and request.company else None
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return f"cache_{hashlib.md5(key_string.encode()).hexdigest()}"