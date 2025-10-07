# core/prometheus_metrics.py
# Prometheus metrics and monitoring integration

import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import prometheus_client, but make it optional
try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, Info
    from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning("prometheus_client not installed, metrics will be logged only")
    PROMETHEUS_AVAILABLE = False


class MetricsRegistry:
    """
    Central registry for all application metrics.
    """
    
    def __init__(self):
        """Initialize metrics registry."""
        if PROMETHEUS_AVAILABLE:
            self.registry = CollectorRegistry()
        else:
            self.registry = None
        
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize all application metrics."""
        
        if not PROMETHEUS_AVAILABLE:
            return
        
        # Request metrics
        self.http_requests_total = Counter(
            'crm_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'crm_http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint'],
            buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
            registry=self.registry
        )
        
        # Database metrics
        self.db_query_duration_seconds = Histogram(
            'crm_db_query_duration_seconds',
            'Database query latency',
            ['query_type', 'model'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )
        
        self.db_queries_total = Counter(
            'crm_db_queries_total',
            'Total database queries',
            ['query_type', 'model'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits_total = Counter(
            'crm_cache_hits_total',
            'Total cache hits',
            ['cache_type', 'key_prefix'],
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            'crm_cache_misses_total',
            'Total cache misses',
            ['cache_type', 'key_prefix'],
            registry=self.registry
        )
        
        self.cache_operation_duration_seconds = Histogram(
            'crm_cache_operation_duration_seconds',
            'Cache operation latency',
            ['operation', 'cache_type'],
            registry=self.registry
        )
        
        # Workflow metrics
        self.workflow_executions_total = Counter(
            'crm_workflow_executions_total',
            'Total workflow executions',
            ['workflow_type', 'status'],
            registry=self.registry
        )
        
        self.workflow_step_duration_seconds = Histogram(
            'crm_workflow_step_duration_seconds',
            'Workflow step duration',
            ['workflow_type', 'step_type', 'queue'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
            registry=self.registry
        )
        
        # Export metrics
        self.export_operations_total = Counter(
            'crm_export_operations_total',
            'Total export operations',
            ['format', 'status'],
            registry=self.registry
        )
        
        self.export_records_total = Counter(
            'crm_export_records_total',
            'Total records exported',
            ['format'],
            registry=self.registry
        )
        
        self.export_duration_seconds = Histogram(
            'crm_export_duration_seconds',
            'Export operation duration',
            ['format'],
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
            registry=self.registry
        )
        
        # Search metrics
        self.search_queries_total = Counter(
            'crm_search_queries_total',
            'Total search queries',
            ['entity_type', 'cache_hit'],
            registry=self.registry
        )
        
        self.search_duration_seconds = Histogram(
            'crm_search_duration_seconds',
            'Search query duration',
            ['entity_type'],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )
        
        # Report metrics
        self.report_queries_total = Counter(
            'crm_report_queries_total',
            'Total report queries',
            ['report_type', 'cache_hit'],
            registry=self.registry
        )
        
        self.report_duration_seconds = Histogram(
            'crm_report_duration_seconds',
            'Report query duration',
            ['report_type'],
            buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0),
            registry=self.registry
        )
        
        # Sharing rule metrics
        self.sharing_rule_evaluations_total = Counter(
            'crm_sharing_rule_evaluations_total',
            'Total sharing rule evaluations',
            ['object_type', 'cache_hit'],
            registry=self.registry
        )
        
        self.sharing_rule_evaluation_duration_seconds = Histogram(
            'crm_sharing_rule_evaluation_duration_seconds',
            'Sharing rule evaluation duration',
            ['object_type'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
            registry=self.registry
        )
        
        # System metrics
        self.active_users_gauge = Gauge(
            'crm_active_users',
            'Number of active users',
            registry=self.registry
        )
        
        self.active_sessions_gauge = Gauge(
            'crm_active_sessions',
            'Number of active sessions',
            registry=self.registry
        )
        
        # Vector search metrics
        self.vector_search_queries_total = Counter(
            'crm_vector_search_queries_total',
            'Total vector search queries',
            ['backend'],
            registry=self.registry
        )
        
        self.vector_search_duration_seconds = Histogram(
            'crm_vector_search_duration_seconds',
            'Vector search duration',
            ['backend'],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )
        
        # Audit log metrics
        self.audit_log_writes_total = Counter(
            'crm_audit_log_writes_total',
            'Total audit log writes',
            ['action', 'partition'],
            registry=self.registry
        )
        
        self.audit_partition_size_bytes = Gauge(
            'crm_audit_partition_size_bytes',
            'Audit partition size in bytes',
            ['partition'],
            registry=self.registry
        )
    
    def generate_metrics(self) -> bytes:
        """Generate metrics in Prometheus format."""
        if not PROMETHEUS_AVAILABLE or not self.registry:
            return b'# Prometheus client not available\n'
        
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get content type for metrics response."""
        if PROMETHEUS_AVAILABLE:
            return CONTENT_TYPE_LATEST
        return 'text/plain'


# Global metrics registry
metrics_registry = MetricsRegistry()


class MetricsDecorators:
    """
    Decorators for automatic metrics collection.
    """
    
    @staticmethod
    def track_duration(metric_name: str, labels: Optional[Dict[str, str]] = None):
        """
        Decorator to track function execution duration.
        
        Args:
            metric_name: Name of the histogram metric
            labels: Optional labels for the metric
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not PROMETHEUS_AVAILABLE:
                    return func(*args, **kwargs)
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    
                    # Get the metric from registry
                    metric = getattr(metrics_registry, metric_name, None)
                    if metric and labels:
                        metric.labels(**labels).observe(duration)
                    
                    logger.debug(f"{func.__name__} took {duration:.3f}s")
            
            return wrapper
        return decorator
    
    @staticmethod
    def count_calls(metric_name: str, labels: Optional[Dict[str, str]] = None):
        """
        Decorator to count function calls.
        
        Args:
            metric_name: Name of the counter metric
            labels: Optional labels for the metric
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                
                if PROMETHEUS_AVAILABLE:
                    metric = getattr(metrics_registry, metric_name, None)
                    if metric and labels:
                        metric.labels(**labels).inc()
                
                return result
            
            return wrapper
        return decorator


class MetricsMiddleware:
    """
    Django middleware for automatic HTTP metrics collection.
    """
    
    def __init__(self, get_response):
        """Initialize middleware."""
        self.get_response = get_response
    
    def __call__(self, request):
        """Process request and collect metrics."""
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Collect metrics
        if PROMETHEUS_AVAILABLE:
            duration = time.time() - start_time
            
            # Extract endpoint (path without IDs)
            endpoint = self._normalize_path(request.path)
            
            # Record request count
            metrics_registry.http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
            # Record request duration
            metrics_registry.http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
        
        return response
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path by removing IDs."""
        import re
        # Replace UUIDs and numeric IDs with placeholders
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/', '/:uuid/', path)
        path = re.sub(r'/\d+/', '/:id/', path)
        return path


def record_cache_hit(cache_type: str, key_prefix: str) -> None:
    """Record a cache hit."""
    if PROMETHEUS_AVAILABLE:
        metrics_registry.cache_hits_total.labels(
            cache_type=cache_type,
            key_prefix=key_prefix
        ).inc()


def record_cache_miss(cache_type: str, key_prefix: str) -> None:
    """Record a cache miss."""
    if PROMETHEUS_AVAILABLE:
        metrics_registry.cache_misses_total.labels(
            cache_type=cache_type,
            key_prefix=key_prefix
        ).inc()


def record_db_query(query_type: str, model: str, duration: float) -> None:
    """Record database query metrics."""
    if PROMETHEUS_AVAILABLE:
        metrics_registry.db_queries_total.labels(
            query_type=query_type,
            model=model
        ).inc()
        
        metrics_registry.db_query_duration_seconds.labels(
            query_type=query_type,
            model=model
        ).observe(duration)


def record_workflow_execution(workflow_type: str, status: str, duration: float) -> None:
    """Record workflow execution metrics."""
    if PROMETHEUS_AVAILABLE:
        metrics_registry.workflow_executions_total.labels(
            workflow_type=workflow_type,
            status=status
        ).inc()


def record_export_operation(format: str, status: str, record_count: int, duration: float) -> None:
    """Record export operation metrics."""
    if PROMETHEUS_AVAILABLE:
        metrics_registry.export_operations_total.labels(
            format=format,
            status=status
        ).inc()
        
        metrics_registry.export_records_total.labels(
            format=format
        ).inc(record_count)
        
        metrics_registry.export_duration_seconds.labels(
            format=format
        ).observe(duration)


def update_active_users(count: int) -> None:
    """Update active users gauge."""
    if PROMETHEUS_AVAILABLE:
        metrics_registry.active_users_gauge.set(count)


def update_active_sessions(count: int) -> None:
    """Update active sessions gauge."""
    if PROMETHEUS_AVAILABLE:
        metrics_registry.active_sessions_gauge.set(count)
