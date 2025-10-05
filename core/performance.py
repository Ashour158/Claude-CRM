# core/performance.py
# Performance optimization utilities and decorators

import time
import functools
import logging
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework.response import Response
from rest_framework import status
import json
import hashlib

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Performance monitoring utility"""
    
    def __init__(self, name=None):
        self.name = name or 'operation'
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
        if self.duration > 1.0:  # Log slow operations
            logger.warning(f"Slow operation '{self.name}': {self.duration:.2f}s")
        else:
            logger.debug(f"Operation '{self.name}': {self.duration:.2f}s")
    
    def get_duration(self):
        """Get operation duration"""
        if self.duration is None and self.start_time:
            return time.time() - self.start_time
        return self.duration

def performance_monitor(name=None):
    """Decorator for performance monitoring"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with PerformanceMonitor(name or func.__name__):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def cache_result(timeout=300, key_prefix=''):
    """Decorator for caching function results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cached result for {func.__name__}")
            return result
        return wrapper
    return decorator

def database_query_monitor(func):
    """Decorator for monitoring database queries"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        initial_queries = len(connection.queries)
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        final_queries = len(connection.queries)
        query_count = final_queries - initial_queries
        duration = end_time - start_time
        
        if query_count > 10:  # Log queries with high count
            logger.warning(f"High query count in {func.__name__}: {query_count} queries in {duration:.2f}s")
        elif duration > 0.5:  # Log slow queries
            logger.warning(f"Slow query in {func.__name__}: {query_count} queries in {duration:.2f}s")
        else:
            logger.debug(f"Query in {func.__name__}: {query_count} queries in {duration:.2f}s")
        
        return result
    return wrapper

def api_response_cache(timeout=300, vary_on=None):
    """Decorator for caching API responses"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            request = args[0] if args else None
            
            if not request or not hasattr(request, 'method') or request.method != 'GET':
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = f"api_cache:{func.__name__}:{request.path}:{request.GET.urlencode()}"
            if vary_on:
                vary_values = []
                for header in vary_on:
                    vary_values.append(request.META.get(header, ''))
                cache_key += f":{':'.join(vary_values)}"
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug(f"API cache hit for {request.path}")
                return Response(cached_response)
            
            # Execute function and cache response
            response = func(*args, **kwargs)
            if isinstance(response, Response) and response.status_code == 200:
                cache.set(cache_key, response.data, timeout)
                logger.debug(f"Cached API response for {request.path}")
            
            return response
        return wrapper
    return decorator

class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def optimize_queryset(queryset, select_related=None, prefetch_related=None):
        """Optimize queryset with select_related and prefetch_related"""
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        return queryset
    
    @staticmethod
    def get_optimized_accounts(company):
        """Get optimized accounts queryset"""
        return QueryOptimizer.optimize_queryset(
            company.accounts.all(),
            select_related=['owner', 'territory'],
            prefetch_related=['contacts', 'deals']
        )
    
    @staticmethod
    def get_optimized_contacts(company):
        """Get optimized contacts queryset"""
        return QueryOptimizer.optimize_queryset(
            company.contacts.all(),
            select_related=['account', 'owner'],
            prefetch_related=['activities']
        )
    
    @staticmethod
    def get_optimized_deals(company):
        """Get optimized deals queryset"""
        return QueryOptimizer.optimize_queryset(
            company.deals.all(),
            select_related=['account', 'contact', 'owner', 'stage'],
            prefetch_related=['activities', 'products']
        )

class CacheManager:
    """Advanced cache management"""
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all caches for a specific user"""
        cache_keys = [
            f"user_profile:{user_id}",
            f"user_companies:{user_id}",
            f"user_permissions:{user_id}",
        ]
        cache.delete_many(cache_keys)
        logger.info(f"Invalidated cache for user {user_id}")
    
    @staticmethod
    def invalidate_company_cache(company_id):
        """Invalidate all caches for a specific company"""
        cache_keys = [
            f"company_data:{company_id}",
            f"company_users:{company_id}",
            f"company_settings:{company_id}",
        ]
        cache.delete_many(cache_keys)
        logger.info(f"Invalidated cache for company {company_id}")
    
    @staticmethod
    def warm_cache(company_id):
        """Warm up cache with frequently accessed data"""
        from crm.models import Account, Contact, Lead
        from deals.models import Deal
        
        # Cache account count
        account_count = Account.objects.filter(company_id=company_id).count()
        cache.set(f"company_accounts_count:{company_id}", account_count, 3600)
        
        # Cache contact count
        contact_count = Contact.objects.filter(company_id=company_id).count()
        cache.set(f"company_contacts_count:{company_id}", contact_count, 3600)
        
        # Cache lead count
        lead_count = Lead.objects.filter(company_id=company_id).count()
        cache.set(f"company_leads_count:{company_id}", lead_count, 3600)
        
        # Cache deal count
        deal_count = Deal.objects.filter(company_id=company_id).count()
        cache.set(f"company_deals_count:{company_id}", deal_count, 3600)
        
        logger.info(f"Warmed cache for company {company_id}")

class ResponseOptimizer:
    """API response optimization"""
    
    @staticmethod
    def optimize_list_response(queryset, serializer_class, request):
        """Optimize list response with pagination and caching"""
        # Apply pagination
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        page = int(request.GET.get('page', 1))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        # Get total count (cached)
        count_key = f"queryset_count:{hash(str(queryset.query))}"
        total_count = cache.get(count_key)
        if total_count is None:
            total_count = queryset.count()
            cache.set(count_key, total_count, 300)
        
        # Get paginated data
        items = queryset[start:end]
        serializer = serializer_class(items, many=True, context={'request': request})
        
        return {
            'count': total_count,
            'next': f"{request.path}?page={page + 1}&page_size={page_size}" if end < total_count else None,
            'previous': f"{request.path}?page={page - 1}&page_size={page_size}" if page > 1 else None,
            'results': serializer.data
        }
    
    @staticmethod
    def optimize_detail_response(instance, serializer_class, request):
        """Optimize detail response with caching"""
        cache_key = f"detail:{instance.__class__.__name__}:{instance.id}:{instance.updated_at}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        serializer = serializer_class(instance, context={'request': request})
        response_data = serializer.data
        cache.set(cache_key, response_data, 600)  # 10 minutes
        
        return Response(response_data)

class DatabaseOptimizer:
    """Database optimization utilities"""
    
    @staticmethod
    def analyze_slow_queries():
        """Analyze slow database queries"""
        slow_queries = []
        for query in connection.queries:
            if float(query['time']) > 0.1:  # Queries taking more than 100ms
                slow_queries.append({
                    'sql': query['sql'],
                    'time': query['time']
                })
        return slow_queries
    
    @staticmethod
    def get_query_count():
        """Get current query count"""
        return len(connection.queries)
    
    @staticmethod
    def reset_query_count():
        """Reset query count"""
        connection.queries.clear()

class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def get_memory_usage():
        """Get current memory usage"""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    
    @staticmethod
    def optimize_memory():
        """Optimize memory usage"""
        import gc
        gc.collect()
        logger.info("Memory optimization completed")

class PerformanceMetrics:
    """Performance metrics collection"""
    
    def __init__(self):
        self.metrics = {}
    
    def start_timer(self, name):
        """Start a performance timer"""
        self.metrics[name] = {'start': time.time()}
    
    def end_timer(self, name):
        """End a performance timer"""
        if name in self.metrics:
            self.metrics[name]['end'] = time.time()
            self.metrics[name]['duration'] = (
                self.metrics[name]['end'] - self.metrics[name]['start']
            )
    
    def get_metrics(self):
        """Get all performance metrics"""
        return self.metrics
    
    def get_duration(self, name):
        """Get duration for a specific metric"""
        if name in self.metrics and 'duration' in self.metrics[name]:
            return self.metrics[name]['duration']
        return None

# Performance decorators for views
def cache_api_response(timeout=300):
    """Cache API response decorator"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if request.method != 'GET':
                return func(self, request, *args, **kwargs)
            
            cache_key = f"api:{func.__name__}:{request.path}:{request.GET.urlencode()}"
            cached_response = cache.get(cache_key)
            
            if cached_response:
                return Response(cached_response)
            
            response = func(self, request, *args, **kwargs)
            if isinstance(response, Response) and response.status_code == 200:
                cache.set(cache_key, response.data, timeout)
            
            return response
        return wrapper
    return decorator

def optimize_database_queries(select_related=None, prefetch_related=None):
    """Optimize database queries decorator"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Store original queryset
            original_queryset = getattr(self, 'queryset', None)
            
            if original_queryset:
                # Apply optimizations
                if select_related:
                    self.queryset = self.queryset.select_related(*select_related)
                if prefetch_related:
                    self.queryset = self.queryset.prefetch_related(*prefetch_related)
            
            result = func(self, request, *args, **kwargs)
            
            # Restore original queryset
            if original_queryset:
                self.queryset = original_queryset
            
            return result
        return wrapper
    return decorator

def monitor_performance(name=None):
    """Monitor performance decorator"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor_name = name or func.__name__
            with PerformanceMonitor(monitor_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Performance middleware
class PerformanceMiddleware:
    """Performance monitoring middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        response = self.get_response(request)
        
        end_time = time.time()
        duration = end_time - start_time
        query_count = len(connection.queries) - initial_queries
        
        # Log performance metrics
        if duration > 1.0 or query_count > 20:
            logger.warning(f"Slow request: {request.path} - {duration:.2f}s, {query_count} queries")
        
        # Add performance headers
        response['X-Response-Time'] = f"{duration:.3f}s"
        response['X-Query-Count'] = str(query_count)
        
        return response
