# core/performance_optimization.py
# Performance optimization utilities and middleware

import time
import logging
from django.core.cache import cache
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Prefetch, select_related, prefetch_related
from django.http import JsonResponse
from django.utils import timezone
import json
import hashlib

logger = logging.getLogger('performance')

class PerformanceMiddleware(MiddlewareMixin):
    """Middleware to track and optimize performance"""
    
    def process_request(self, request):
        """Track request start time"""
        request.start_time = time.time()
        request.query_count = len(connection.queries)
        return None
    
    def process_response(self, request, response):
        """Track request performance and add headers"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            query_count = len(connection.queries) - getattr(request, 'query_count', 0)
            
            # Add performance headers
            response['X-Response-Time'] = f"{duration:.3f}s"
            response['X-Query-Count'] = str(query_count)
            
            # Log slow requests
            if duration > 1.0:  # 1 second threshold
                logger.warning(f"Slow request: {request.path} took {duration:.3f}s ({query_count} queries)")
            
            # Log high query count
            if query_count > 20:  # 20 queries threshold
                logger.warning(f"High query count: {request.path} executed {query_count} queries")
        
        return response

class QueryOptimizationMixin:
    """Mixin for query optimization in views"""
    
    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related"""
        queryset = super().get_queryset()
        
        # Add select_related for foreign keys
        if hasattr(self, 'select_related_fields'):
            queryset = queryset.select_related(*self.select_related_fields)
        
        # Add prefetch_related for many-to-many and reverse foreign keys
        if hasattr(self, 'prefetch_related_fields'):
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)
        
        return queryset
    
    def get_serializer_context(self):
        """Add optimization context to serializer"""
        context = super().get_serializer_context()
        context['optimize_queries'] = True
        return context

class CacheOptimizationMixin:
    """Mixin for cache optimization"""
    
    cache_timeout = 300  # 5 minutes default
    cache_key_prefix = 'crm'
    
    def get_cache_key(self, *args, **kwargs):
        """Generate cache key"""
        key_data = f"{self.cache_key_prefix}:{self.__class__.__name__}:{args}:{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cached_data(self, cache_key, data_func, *args, **kwargs):
        """Get data from cache or generate if not cached"""
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            logger.info(f"Cache hit for key: {cache_key}")
            return cached_data
        
        logger.info(f"Cache miss for key: {cache_key}")
        data = data_func(*args, **kwargs)
        cache.set(cache_key, data, self.cache_timeout)
        return data
    
    def invalidate_cache(self, cache_key):
        """Invalidate cache key"""
        cache.delete(cache_key)
        logger.info(f"Cache invalidated for key: {cache_key}")

class DatabaseOptimization:
    """Database optimization utilities"""
    
    @staticmethod
    def optimize_queryset(queryset, select_related_fields=None, prefetch_related_fields=None):
        """Optimize queryset with select_related and prefetch_related"""
        if select_related_fields:
            queryset = queryset.select_related(*select_related_fields)
        
        if prefetch_related_fields:
            queryset = queryset.prefetch_related(*prefetch_related_fields)
        
        return queryset
    
    @staticmethod
    def get_optimized_accounts():
        """Get optimized accounts queryset"""
        from crm.models import Account
        return Account.objects.select_related('territory', 'owner').prefetch_related(
            'contacts', 'deals', 'activities'
        )
    
    @staticmethod
    def get_optimized_contacts():
        """Get optimized contacts queryset"""
        from crm.models import Contact
        return Contact.objects.select_related('account', 'owner').prefetch_related(
            'activities', 'deals'
        )
    
    @staticmethod
    def get_optimized_deals():
        """Get optimized deals queryset"""
        from deals.models import Deal
        return Deal.objects.select_related(
            'account', 'contact', 'stage', 'owner'
        ).prefetch_related('activities')
    
    @staticmethod
    def get_optimized_activities():
        """Get optimized activities queryset"""
        from activities.models import Activity
        return Activity.objects.select_related(
            'account', 'contact', 'lead', 'deal', 'owner'
        )

class ResponseOptimization:
    """Response optimization utilities"""
    
    @staticmethod
    def optimize_pagination(queryset, page_size=20, max_page_size=100):
        """Optimize pagination"""
        page_size = min(page_size, max_page_size)
        paginator = Paginator(queryset, page_size)
        return paginator
    
    @staticmethod
    def compress_response_data(data):
        """Compress response data"""
        if isinstance(data, dict):
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Remove empty strings
            data = {k: v for k, v in data.items() if v != ''}
        
        return data
    
    @staticmethod
    def add_performance_headers(response, start_time, query_count):
        """Add performance headers to response"""
        duration = time.time() - start_time
        response['X-Response-Time'] = f"{duration:.3f}s"
        response['X-Query-Count'] = str(query_count)
        response['X-Cache-Status'] = 'MISS'  # Will be overridden by cache middleware
        
        return response

class CacheStrategy:
    """Cache strategy implementation"""
    
    @staticmethod
    def get_user_cache_key(user_id, company_id, cache_type):
        """Generate user-specific cache key"""
        return f"user:{user_id}:company:{company_id}:{cache_type}"
    
    @staticmethod
    def get_company_cache_key(company_id, cache_type):
        """Generate company-specific cache key"""
        return f"company:{company_id}:{cache_type}"
    
    @staticmethod
    def invalidate_user_cache(user_id, company_id):
        """Invalidate all user cache"""
        cache_pattern = f"user:{user_id}:company:{company_id}:*"
        # Note: This is a simplified version. In production, you'd use Redis SCAN
        logger.info(f"Invalidating cache for user {user_id} in company {company_id}")
    
    @staticmethod
    def invalidate_company_cache(company_id):
        """Invalidate all company cache"""
        cache_pattern = f"company:{company_id}:*"
        # Note: This is a simplified version. In production, you'd use Redis SCAN
        logger.info(f"Invalidating cache for company {company_id}")

class PerformanceMonitoring:
    """Performance monitoring utilities"""
    
    @staticmethod
    def log_slow_query(query, duration, threshold=0.1):
        """Log slow database queries"""
        if duration > threshold:
            logger.warning(f"Slow query ({duration:.3f}s): {query}")
    
    @staticmethod
    def log_high_memory_usage(memory_usage, threshold=100):
        """Log high memory usage"""
        if memory_usage > threshold:
            logger.warning(f"High memory usage: {memory_usage}MB")
    
    @staticmethod
    def log_cache_performance(cache_key, hit, duration):
        """Log cache performance"""
        status = "HIT" if hit else "MISS"
        logger.info(f"Cache {status}: {cache_key} ({duration:.3f}s)")
    
    @staticmethod
    def get_performance_metrics():
        """Get current performance metrics"""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': timezone.now().isoformat()
        }

class QueryAnalysis:
    """Query analysis utilities"""
    
    @staticmethod
    def analyze_queries():
        """Analyze database queries"""
        queries = connection.queries
        total_time = sum(float(q['time']) for q in queries)
        
        return {
            'total_queries': len(queries),
            'total_time': total_time,
            'average_time': total_time / len(queries) if queries else 0,
            'slow_queries': [q for q in queries if float(q['time']) > 0.1]
        }
    
    @staticmethod
    def get_duplicate_queries():
        """Find duplicate queries"""
        queries = connection.queries
        query_counts = {}
        
        for query in queries:
            sql = query['sql']
            if sql in query_counts:
                query_counts[sql] += 1
            else:
                query_counts[sql] = 1
        
        return {sql: count for sql, count in query_counts.items() if count > 1}

class MemoryOptimization:
    """Memory optimization utilities"""
    
    @staticmethod
    def optimize_queryset_memory(queryset, batch_size=1000):
        """Process queryset in batches to optimize memory"""
        total_count = queryset.count()
        
        for i in range(0, total_count, batch_size):
            batch = queryset[i:i + batch_size]
            yield batch
    
    @staticmethod
    def clear_queryset_cache(queryset):
        """Clear queryset cache"""
        if hasattr(queryset, '_result_cache'):
            queryset._result_cache = None
    
    @staticmethod
    def optimize_serializer_data(serializer_data):
        """Optimize serializer data for memory"""
        if isinstance(serializer_data, list):
            # Process list in chunks
            chunk_size = 100
            for i in range(0, len(serializer_data), chunk_size):
                yield serializer_data[i:i + chunk_size]
        else:
            yield serializer_data

class APIOptimization:
    """API optimization utilities"""
    
    @staticmethod
    def optimize_api_response(data, fields=None, exclude=None):
        """Optimize API response data"""
        if fields:
            if isinstance(data, list):
                data = [{k: v for k, v in item.items() if k in fields} for item in data]
            elif isinstance(data, dict):
                data = {k: v for k, v in data.items() if k in fields}
        
        if exclude:
            if isinstance(data, list):
                data = [{k: v for k, v in item.items() if k not in exclude} for item in data]
            elif isinstance(data, dict):
                data = {k: v for k, v in data.items() if k not in exclude}
        
        return data
    
    @staticmethod
    def add_performance_headers(response, metrics):
        """Add performance headers to API response"""
        response['X-Response-Time'] = f"{metrics.get('response_time', 0):.3f}s"
        response['X-Query-Count'] = str(metrics.get('query_count', 0))
        response['X-Cache-Status'] = metrics.get('cache_status', 'MISS')
        response['X-Memory-Usage'] = f"{metrics.get('memory_usage', 0):.2f}MB"
        
        return response

# Performance decorators
def monitor_performance(func):
    """Decorator to monitor function performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        result = func(*args, **kwargs)
        
        duration = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_usage = end_memory - start_memory
        
        logger.info(f"Function {func.__name__} executed in {duration:.3f}s using {memory_usage:.2f}MB")
        
        return result
    
    return wrapper

def cache_result(timeout=300):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
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

# Initialize performance monitoring
import psutil
