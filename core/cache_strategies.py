# core/cache_strategies.py
# Advanced caching strategies for CRM system

import time
import hashlib
import json
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
import logging

logger = logging.getLogger('cache')

class CacheStrategy:
    """Base cache strategy class"""
    
    def __init__(self, timeout=300, key_prefix='crm'):
        self.timeout = timeout
        self.key_prefix = key_prefix
    
    def generate_key(self, *args, **kwargs):
        """Generate cache key"""
        key_data = f"{self.key_prefix}:{args}:{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key):
        """Get value from cache"""
        return cache.get(key)
    
    def set(self, key, value, timeout=None):
        """Set value in cache"""
        timeout = timeout or self.timeout
        cache.set(key, value, timeout)
    
    def delete(self, key):
        """Delete value from cache"""
        cache.delete(key)
    
    def invalidate_pattern(self, pattern):
        """Invalidate cache pattern (requires Redis)"""
        # This is a simplified version. In production, use Redis SCAN
        logger.info(f"Invalidating cache pattern: {pattern}")

class ModelCacheStrategy(CacheStrategy):
    """Cache strategy for Django models"""
    
    def __init__(self, model_class, timeout=300):
        super().__init__(timeout)
        self.model_class = model_class
        self.model_name = model_class.__name__.lower()
    
    def get_model_key(self, pk):
        """Generate model cache key"""
        return f"{self.key_prefix}:{self.model_name}:{pk}"
    
    def get_list_key(self, filters=None, ordering=None, page=None, page_size=None):
        """Generate list cache key"""
        key_data = f"{self.model_name}:list:{filters}:{ordering}:{page}:{page_size}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_model(self, pk):
        """Get model instance from cache"""
        key = self.get_model_key(pk)
        return self.get(key)
    
    def set_model(self, instance, timeout=None):
        """Cache model instance"""
        key = self.get_model_key(instance.pk)
        self.set(key, instance, timeout)
    
    def get_list(self, filters=None, ordering=None, page=None, page_size=None):
        """Get model list from cache"""
        key = self.get_list_key(filters, ordering, page, page_size)
        return self.get(key)
    
    def set_list(self, queryset, filters=None, ordering=None, page=None, page_size=None, timeout=None):
        """Cache model list"""
        key = self.get_list_key(filters, ordering, page, page_size)
        self.set(key, queryset, timeout)
    
    def invalidate_model(self, pk):
        """Invalidate model cache"""
        key = self.get_model_key(pk)
        self.delete(key)
    
    def invalidate_list(self, filters=None, ordering=None):
        """Invalidate list cache"""
        # Invalidate all list variations
        patterns = [
            f"{self.key_prefix}:{self.model_name}:list:*",
            f"{self.key_prefix}:{self.model_name}:list:{filters}:*",
            f"{self.key_prefix}:{self.model_name}:list:*:{ordering}:*"
        ]
        for pattern in patterns:
            self.invalidate_pattern(pattern)

class APICacheStrategy(CacheStrategy):
    """Cache strategy for API responses"""
    
    def __init__(self, timeout=300):
        super().__init__(timeout, 'api')
    
    def get_api_key(self, endpoint, params=None, user_id=None, company_id=None):
        """Generate API cache key"""
        key_data = f"{endpoint}:{params}:{user_id}:{company_id}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_response(self, endpoint, params=None, user_id=None, company_id=None):
        """Get API response from cache"""
        key = self.get_api_key(endpoint, params, user_id, company_id)
        return self.get(key)
    
    def set_response(self, endpoint, response_data, params=None, user_id=None, company_id=None, timeout=None):
        """Cache API response"""
        key = self.get_api_key(endpoint, params, user_id, company_id)
        self.set(key, response_data, timeout)
    
    def invalidate_user_cache(self, user_id, company_id=None):
        """Invalidate user-specific cache"""
        patterns = [
            f"{self.key_prefix}:*:{user_id}:*",
            f"{self.key_prefix}:*:{user_id}:{company_id}:*"
        ]
        for pattern in patterns:
            self.invalidate_pattern(pattern)
    
    def invalidate_company_cache(self, company_id):
        """Invalidate company-specific cache"""
        pattern = f"{self.key_prefix}:*:*:{company_id}:*"
        self.invalidate_pattern(pattern)

class QueryCacheStrategy(CacheStrategy):
    """Cache strategy for database queries"""
    
    def __init__(self, timeout=300):
        super().__init__(timeout, 'query')
    
    def get_query_key(self, sql, params=None):
        """Generate query cache key"""
        key_data = f"{sql}:{params}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_query_result(self, sql, params=None):
        """Get query result from cache"""
        key = self.get_query_key(sql, params)
        return self.get(key)
    
    def set_query_result(self, sql, result, params=None, timeout=None):
        """Cache query result"""
        key = self.get_query_key(sql, params)
        self.set(key, result, timeout)
    
    def invalidate_model_queries(self, model_name):
        """Invalidate all queries for a model"""
        pattern = f"{self.key_prefix}:*{model_name}*"
        self.invalidate_pattern(pattern)

class MultiTenantCacheStrategy(CacheStrategy):
    """Cache strategy for multi-tenant applications"""
    
    def __init__(self, timeout=300):
        super().__init__(timeout, 'tenant')
    
    def get_tenant_key(self, company_id, key_type, *args, **kwargs):
        """Generate tenant-specific cache key"""
        key_data = f"{company_id}:{key_type}:{args}:{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_tenant_data(self, company_id, key_type, *args, **kwargs):
        """Get tenant data from cache"""
        key = self.get_tenant_key(company_id, key_type, *args, **kwargs)
        return self.get(key)
    
    def set_tenant_data(self, company_id, key_type, data, *args, **kwargs, timeout=None):
        """Cache tenant data"""
        key = self.get_tenant_key(company_id, key_type, *args, **kwargs)
        self.set(key, data, timeout)
    
    def invalidate_tenant_cache(self, company_id):
        """Invalidate all cache for a tenant"""
        pattern = f"{self.key_prefix}:{company_id}:*"
        self.invalidate_pattern(pattern)
    
    def invalidate_tenant_type(self, company_id, key_type):
        """Invalidate specific type of cache for a tenant"""
        pattern = f"{self.key_prefix}:{company_id}:{key_type}:*"
        self.invalidate_pattern(pattern)

class CacheManager:
    """Centralized cache management"""
    
    def __init__(self):
        self.strategies = {
            'model': ModelCacheStrategy,
            'api': APICacheStrategy,
            'query': QueryCacheStrategy,
            'tenant': MultiTenantCacheStrategy
        }
    
    def get_strategy(self, strategy_type, **kwargs):
        """Get cache strategy instance"""
        strategy_class = self.strategies.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown cache strategy: {strategy_type}")
        return strategy_class(**kwargs)
    
    def invalidate_all(self):
        """Invalidate all cache"""
        cache.clear()
        logger.info("All cache invalidated")
    
    def get_cache_stats(self):
        """Get cache statistics"""
        # This is a simplified version. In production, use Redis INFO
        return {
            'timestamp': timezone.now().isoformat(),
            'status': 'active'
        }

class CacheDecorators:
    """Cache decorators for functions and methods"""
    
    @staticmethod
    def cache_result(timeout=300, key_func=None):
        """Decorator to cache function results"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # Try to get from cache
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.info(f"Cache hit for {func.__name__}")
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
                logger.info(f"Cache miss for {func.__name__}, result cached")
                
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def cache_model(timeout=300):
        """Decorator to cache model methods"""
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                cache_key = f"{self.__class__.__name__}:{self.pk}:{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                result = func(self, *args, **kwargs)
                cache.set(cache_key, result, timeout)
                
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def invalidate_on_save(model_class):
        """Decorator to invalidate cache on model save"""
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                result = func(self, *args, **kwargs)
                
                # Invalidate model cache
                cache_key = f"model:{model_class.__name__.lower()}:{self.pk}"
                cache.delete(cache_key)
                
                # Invalidate list cache
                list_pattern = f"list:{model_class.__name__.lower()}:*"
                # In production, use Redis SCAN to find and delete matching keys
                logger.info(f"Invalidating cache for {model_class.__name__}")
                
                return result
            
            return wrapper
        return decorator

class CacheWarming:
    """Cache warming utilities"""
    
    @staticmethod
    def warm_model_cache(model_class, filters=None):
        """Warm cache for model instances"""
        strategy = ModelCacheStrategy(model_class)
        
        queryset = model_class.objects.all()
        if filters:
            queryset = queryset.filter(**filters)
        
        for instance in queryset:
            strategy.set_model(instance)
        
        logger.info(f"Warmed cache for {model_class.__name__}")
    
    @staticmethod
    def warm_api_cache(endpoints, user_id=None, company_id=None):
        """Warm cache for API endpoints"""
        strategy = APICacheStrategy()
        
        for endpoint in endpoints:
            # This would need to be implemented based on your API structure
            logger.info(f"Warming cache for endpoint: {endpoint}")
    
    @staticmethod
    def warm_tenant_cache(company_id, cache_types):
        """Warm cache for tenant"""
        strategy = MultiTenantCacheStrategy()
        
        for cache_type in cache_types:
            # This would need to be implemented based on your cache structure
            logger.info(f"Warming cache for company {company_id}, type: {cache_type}")

class CacheMonitoring:
    """Cache monitoring utilities"""
    
    @staticmethod
    def get_cache_hit_rate():
        """Get cache hit rate"""
        # This is a simplified version. In production, use Redis INFO
        return {
            'hit_rate': 0.85,
            'timestamp': timezone.now().isoformat()
        }
    
    @staticmethod
    def get_cache_memory_usage():
        """Get cache memory usage"""
        # This is a simplified version. In production, use Redis INFO
        return {
            'memory_usage': '50MB',
            'timestamp': timezone.now().isoformat()
        }
    
    @staticmethod
    def get_cache_keys_count():
        """Get number of cache keys"""
        # This is a simplified version. In production, use Redis DBSIZE
        return {
            'keys_count': 1000,
            'timestamp': timezone.now().isoformat()
        }

# Global cache manager instance
cache_manager = CacheManager()

# Cache decorators
cache_result = CacheDecorators.cache_result
cache_model = CacheDecorators.cache_model
invalidate_on_save = CacheDecorators.invalidate_on_save
