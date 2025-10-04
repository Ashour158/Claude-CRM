# core/cache.py
# Enterprise-grade caching strategy

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.conf import settings
import json
import hashlib
from typing import Any, Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class EnterpriseCache:
    """
    Enterprise-grade caching with multiple strategies
    """
    
    # Cache key prefixes
    USER_PREFIX = "user"
    COMPANY_PREFIX = "company"
    CRM_PREFIX = "crm"
    SALES_PREFIX = "sales"
    ANALYTICS_PREFIX = "analytics"
    
    # Cache TTL (Time To Live) in seconds
    TTL_SHORT = 300      # 5 minutes
    TTL_MEDIUM = 1800    # 30 minutes
    TTL_LONG = 3600      # 1 hour
    TTL_VERY_LONG = 86400  # 24 hours
    
    @classmethod
    def generate_cache_key(cls, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key"""
        key_parts = [prefix] + [str(arg) for arg in args]
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
        
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @classmethod
    def get_user_cache(cls, user_id: str, cache_type: str = "profile") -> Optional[Any]:
        """Get user-related cached data"""
        key = cls.generate_cache_key(cls.USER_PREFIX, user_id, cache_type)
        return cache.get(key)
    
    @classmethod
    def set_user_cache(cls, user_id: str, data: Any, cache_type: str = "profile", ttl: int = TTL_MEDIUM) -> bool:
        """Set user-related cached data"""
        key = cls.generate_cache_key(cls.USER_PREFIX, user_id, cache_type)
        try:
            cache.set(key, data, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set user cache: {e}")
            return False
    
    @classmethod
    def get_company_cache(cls, company_id: str, cache_type: str = "settings") -> Optional[Any]:
        """Get company-related cached data"""
        key = cls.generate_cache_key(cls.COMPANY_PREFIX, company_id, cache_type)
        return cache.get(key)
    
    @classmethod
    def set_company_cache(cls, company_id: str, data: Any, cache_type: str = "settings", ttl: int = TTL_LONG) -> bool:
        """Set company-related cached data"""
        key = cls.generate_cache_key(cls.COMPANY_PREFIX, company_id, cache_type)
        try:
            cache.set(key, data, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set company cache: {e}")
            return False
    
    @classmethod
    def get_crm_cache(cls, company_id: str, entity_type: str, entity_id: str = None) -> Optional[Any]:
        """Get CRM-related cached data"""
        key = cls.generate_cache_key(cls.CRM_PREFIX, company_id, entity_type, entity_id or "list")
        return cache.get(key)
    
    @classmethod
    def set_crm_cache(cls, company_id: str, entity_type: str, data: Any, entity_id: str = None, ttl: int = TTL_MEDIUM) -> bool:
        """Set CRM-related cached data"""
        key = cls.generate_cache_key(cls.CRM_PREFIX, company_id, entity_type, entity_id or "list")
        try:
            cache.set(key, data, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set CRM cache: {e}")
            return False
    
    @classmethod
    def get_analytics_cache(cls, company_id: str, report_type: str, filters: Dict = None) -> Optional[Any]:
        """Get analytics cached data"""
        key = cls.generate_cache_key(cls.ANALYTICS_PREFIX, company_id, report_type, filters or {})
        return cache.get(key)
    
    @classmethod
    def set_analytics_cache(cls, company_id: str, report_type: str, data: Any, filters: Dict = None, ttl: int = TTL_LONG) -> bool:
        """Set analytics cached data"""
        key = cls.generate_cache_key(cls.ANALYTICS_PREFIX, company_id, report_type, filters or {})
        try:
            cache.set(key, data, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set analytics cache: {e}")
            return False
    
    @classmethod
    def invalidate_user_cache(cls, user_id: str) -> bool:
        """Invalidate all user-related cache"""
        try:
            # Get all keys with user prefix
            pattern = f"{cls.USER_PREFIX}:*:{user_id}:*"
            cache.delete_many(cache.keys(pattern))
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {e}")
            return False
    
    @classmethod
    def invalidate_company_cache(cls, company_id: str) -> bool:
        """Invalidate all company-related cache"""
        try:
            # Get all keys with company prefix
            pattern = f"{cls.COMPANY_PREFIX}:*:{company_id}:*"
            cache.delete_many(cache.keys(pattern))
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate company cache: {e}")
            return False
    
    @classmethod
    def invalidate_crm_cache(cls, company_id: str, entity_type: str = None) -> bool:
        """Invalidate CRM-related cache"""
        try:
            if entity_type:
                pattern = f"{cls.CRM_PREFIX}:*:{company_id}:{entity_type}:*"
            else:
                pattern = f"{cls.CRM_PREFIX}:*:{company_id}:*"
            cache.delete_many(cache.keys(pattern))
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate CRM cache: {e}")
            return False
    
    @classmethod
    def get_cache_stats(cls) -> Dict:
        """Get cache statistics"""
        try:
            # This would depend on your cache backend
            # For Redis, you could use redis-cli info
            return {
                "cache_backend": settings.CACHES['default']['BACKEND'],
                "cache_location": settings.CACHES['default'].get('LOCATION', 'N/A'),
                "cache_timeout": settings.CACHES['default'].get('TIMEOUT', 'N/A'),
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


class CacheMiddleware:
    """
    Middleware for automatic caching of responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if response should be cached
        if self.should_cache(request):
            cache_key = self.get_cache_key(request)
            cached_response = cache.get(cache_key)
            
            if cached_response:
                return cached_response
        
        response = self.get_response(request)
        
        # Cache the response if appropriate
        if self.should_cache(request) and response.status_code == 200:
            cache_key = self.get_cache_key(request)
            cache.set(cache_key, response, EnterpriseCache.TTL_MEDIUM)
        
        return response
    
    def should_cache(self, request):
        """Determine if request should be cached"""
        # Don't cache POST, PUT, DELETE requests
        if request.method not in ['GET']:
            return False
        
        # Don't cache authenticated user-specific data
        if request.user.is_authenticated and 'user' in request.path:
            return False
        
        # Cache public data and company-level data
        return True
    
    def get_cache_key(self, request):
        """Generate cache key for request"""
        path = request.path
        query_params = request.GET.urlencode()
        company_id = getattr(request, 'active_company_id', None)
        
        key_parts = [path]
        if query_params:
            key_parts.append(query_params)
        if company_id:
            key_parts.append(f"company:{company_id}")
        
        return EnterpriseCache.generate_cache_key("response", *key_parts)


class CacheInvalidationMixin:
    """
    Mixin for automatic cache invalidation on model changes
    """
    
    def save(self, *args, **kwargs):
        """Override save to invalidate cache"""
        super().save(*args, **kwargs)
        self.invalidate_related_cache()
    
    def delete(self, *args, **kwargs):
        """Override delete to invalidate cache"""
        self.invalidate_related_cache()
        super().delete(*args, **kwargs)
    
    def invalidate_related_cache(self):
        """Invalidate cache related to this model"""
        # Override in subclasses
        pass


# Cache decorators
def cache_result(ttl=300, key_prefix="default"):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = EnterpriseCache.generate_cache_key(
                key_prefix, 
                func.__name__, 
                *args, 
                **kwargs
            )
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def invalidate_cache_on_change(model_class, cache_keys_func):
    """Decorator to invalidate cache when model changes"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate related cache
            if hasattr(result, 'company_id'):
                EnterpriseCache.invalidate_company_cache(result.company_id)
            
            return result
        
        return wrapper
    return decorator
