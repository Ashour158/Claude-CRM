# core/observability.py
# Observability: structured logging, metrics, and tracing for Phase 4+

import json
import time
import logging
import uuid
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

logger = logging.getLogger(__name__)

class StructuredLoggingMiddleware(MiddlewareMixin):
    """Middleware for structured JSON logging with correlation IDs"""
    
    def process_request(self, request):
        """Add correlation ID and timing to request"""
        # Generate or extract correlation ID
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        request.correlation_id = correlation_id
        request.start_time = time.time()
        
        # Extract user and company context
        request.user_id = str(request.user.id) if request.user.is_authenticated else None
        request.org_id = None
        
        if request.user.is_authenticated and hasattr(request, 'active_company'):
            request.org_id = str(request.active_company.id)
        
        return None
    
    def process_response(self, request, response):
        """Log structured request/response data"""
        if not hasattr(request, 'start_time'):
            return response
        
        # Calculate latency
        latency_ms = int((time.time() - request.start_time) * 1000)
        
        # Build structured log entry
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'correlation_id': getattr(request, 'correlation_id', None),
            'user_id': getattr(request, 'user_id', None),
            'org_id': getattr(request, 'org_id', None),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'latency_ms': latency_ms,
            'user_agent': request.headers.get('User-Agent', '')[:100],
            'remote_addr': self._get_client_ip(request),
        }
        
        # Log at appropriate level
        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
        
        # Add correlation ID to response headers
        response['X-Correlation-ID'] = log_data['correlation_id']
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions with full context"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'correlation_id': getattr(request, 'correlation_id', None),
            'user_id': getattr(request, 'user_id', None),
            'org_id': getattr(request, 'org_id', None),
            'method': request.method,
            'path': request.path,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'latency_ms': int((time.time() - request.start_time) * 1000) if hasattr(request, 'start_time') else 0,
        }
        
        logger.exception(json.dumps(log_data))
        return None
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

class PrometheusMetrics:
    """Prometheus metrics collector (stub for Phase 4+)"""
    
    # Metrics storage (in-memory for now, should use prometheus_client in production)
    _metrics = {
        'workflow_runs_total': {},
        'search_query_latency': [],
        'websocket_active_connections': 0,
    }
    
    @classmethod
    def increment_counter(cls, metric_name: str, labels: dict = None):
        """Increment a counter metric"""
        if metric_name not in cls._metrics:
            cls._metrics[metric_name] = {}
        
        label_key = json.dumps(labels or {}, sort_keys=True)
        cls._metrics[metric_name][label_key] = cls._metrics[metric_name].get(label_key, 0) + 1
        
        logger.debug(f"Metric {metric_name}{labels}: {cls._metrics[metric_name][label_key]}")
    
    @classmethod
    def observe_histogram(cls, metric_name: str, value: float, labels: dict = None):
        """Record a histogram observation"""
        if metric_name not in cls._metrics:
            cls._metrics[metric_name] = []
        
        cls._metrics[metric_name].append({
            'value': value,
            'labels': labels or {},
            'timestamp': time.time()
        })
        
        logger.debug(f"Histogram {metric_name}{labels}: {value}")
    
    @classmethod
    def set_gauge(cls, metric_name: str, value: float, labels: dict = None):
        """Set a gauge metric"""
        if metric_name not in cls._metrics:
            cls._metrics[metric_name] = {}
        
        label_key = json.dumps(labels or {}, sort_keys=True)
        cls._metrics[metric_name][label_key] = value
        
        logger.debug(f"Gauge {metric_name}{labels}: {value}")
    
    @classmethod
    def get_metrics(cls) -> dict:
        """Get all metrics (for /metrics endpoint)"""
        return cls._metrics

class TracingInstrumentation:
    """OpenTelemetry-style tracing instrumentation (stub for Phase 4+)"""
    
    @staticmethod
    def trace_function(operation_name: str):
        """Decorator to trace function execution"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                span_id = str(uuid.uuid4())
                
                logger.debug(f"[TRACE] Starting span: {operation_name} (id={span_id})")
                
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    logger.debug(
                        f"[TRACE] Completed span: {operation_name} "
                        f"(id={span_id}, duration={duration:.3f}s)"
                    )
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(
                        f"[TRACE] Failed span: {operation_name} "
                        f"(id={span_id}, duration={duration:.3f}s, error={str(e)})"
                    )
                    raise
            
            return wrapper
        return decorator
    
    @staticmethod
    def create_span(operation_name: str, attributes: dict = None):
        """Create a tracing span context"""
        return TracingSpan(operation_name, attributes or {})

class TracingSpan:
    """Tracing span context manager"""
    
    def __init__(self, operation_name: str, attributes: dict):
        self.operation_name = operation_name
        self.attributes = attributes
        self.span_id = str(uuid.uuid4())
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.debug(
            f"[TRACE] Starting span: {self.operation_name} "
            f"(id={self.span_id}, attrs={self.attributes})"
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type:
            logger.error(
                f"[TRACE] Failed span: {self.operation_name} "
                f"(id={self.span_id}, duration={duration:.3f}s, error={exc_val})"
            )
        else:
            logger.debug(
                f"[TRACE] Completed span: {self.operation_name} "
                f"(id={self.span_id}, duration={duration:.3f}s)"
            )
        
        return False

# Metric helpers for specific use cases

def track_workflow_execution(workflow_name: str, status: str, duration_ms: int):
    """Track workflow execution metrics"""
    PrometheusMetrics.increment_counter(
        'workflow_runs_total',
        {'workflow': workflow_name, 'status': status}
    )
    PrometheusMetrics.observe_histogram(
        'workflow_duration_ms',
        duration_ms,
        {'workflow': workflow_name}
    )

def track_search_query(query_type: str, latency_ms: float):
    """Track search query metrics"""
    PrometheusMetrics.observe_histogram(
        'search_query_latency_ms',
        latency_ms,
        {'type': query_type}
    )

def track_websocket_connections(count: int):
    """Track active WebSocket connections"""
    PrometheusMetrics.set_gauge('websocket_active_connections', count)
