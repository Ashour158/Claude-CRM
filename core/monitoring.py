# core/monitoring.py
# Advanced monitoring and logging system

import logging
import time
import json
import psutil
import os
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.db import connection
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta

User = get_user_model()
logger = logging.getLogger(__name__)

class SystemMetrics:
    """System metrics collection"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.lock = threading.Lock()
    
    def record_metric(self, name, value, timestamp=None):
        """Record a metric value"""
        if timestamp is None:
            timestamp = timezone.now()
        
        with self.lock:
            self.metrics[name].append({
                'value': value,
                'timestamp': timestamp,
                'timestamp_iso': timestamp.isoformat()
            })
            
            # Keep only last 1000 entries per metric
            if len(self.metrics[name]) > 1000:
                self.metrics[name] = self.metrics[name][-1000:]
    
    def get_metric(self, name, minutes=60):
        """Get metric values for the last N minutes"""
        cutoff = timezone.now() - timedelta(minutes=minutes)
        
        with self.lock:
            return [
                entry for entry in self.metrics.get(name, [])
                if entry['timestamp'] >= cutoff
            ]
    
    def get_metric_summary(self, name, minutes=60):
        """Get metric summary statistics"""
        values = self.get_metric(name, minutes)
        if not values:
            return None
        
        numeric_values = [entry['value'] for entry in values if isinstance(entry['value'], (int, float))]
        if not numeric_values:
            return None
        
        return {
            'count': len(numeric_values),
            'min': min(numeric_values),
            'max': max(numeric_values),
            'avg': sum(numeric_values) / len(numeric_values),
            'latest': values[-1]['value'] if values else None
        }

class PerformanceMonitor:
    """Performance monitoring system"""
    
    def __init__(self):
        self.metrics = SystemMetrics()
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
    
    def record_request(self, path, method, duration, status_code, user_id=None):
        """Record API request metrics"""
        self.request_count += 1
        
        # Record response time
        self.metrics.record_metric('response_time', duration)
        
        # Record request count by endpoint
        endpoint = f"{method} {path}"
        self.metrics.record_metric('endpoint_requests', endpoint)
        
        # Record status codes
        self.metrics.record_metric('status_codes', status_code)
        
        # Record user activity
        if user_id:
            self.metrics.record_metric('user_activity', user_id)
        
        # Record slow requests
        if duration > 1.0:
            self.metrics.record_metric('slow_requests', {
                'path': path,
                'method': method,
                'duration': duration,
                'user_id': user_id
            })
    
    def record_error(self, error_type, error_message, path=None, user_id=None):
        """Record error metrics"""
        self.error_count += 1
        
        self.metrics.record_metric('errors', {
            'type': error_type,
            'message': error_message,
            'path': path,
            'user_id': user_id,
            'timestamp': timezone.now().isoformat()
        })
    
    def record_database_query(self, query, duration):
        """Record database query metrics"""
        self.metrics.record_metric('db_query_time', duration)
        self.metrics.record_metric('db_query_count', 1)
        
        # Record slow queries
        if duration > 0.1:
            self.metrics.record_metric('slow_queries', {
                'query': query[:200],  # Truncate long queries
                'duration': duration
            })
    
    def get_system_stats(self):
        """Get current system statistics"""
        # Memory usage
        memory = psutil.virtual_memory()
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Database connections
        db_connections = len(connection.queries) if hasattr(connection, 'queries') else 0
        
        # Cache stats
        cache_stats = self.get_cache_stats()
        
        return {
            'uptime': time.time() - self.start_time,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            },
            'cpu': {
                'percent': cpu_percent
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            },
            'database': {
                'connections': db_connections
            },
            'cache': cache_stats
        }
    
    def get_cache_stats(self):
        """Get cache statistics"""
        try:
            # Test cache connectivity
            cache.set('health_check', 'ok', 10)
            cache_working = cache.get('health_check') == 'ok'
            
            return {
                'working': cache_working,
                'backend': settings.CACHES['default']['BACKEND']
            }
        except Exception as e:
            return {
                'working': False,
                'error': str(e)
            }
    
    def get_performance_summary(self, minutes=60):
        """Get performance summary for the last N minutes"""
        response_times = self.metrics.get_metric('response_time', minutes)
        errors = self.metrics.get_metric('errors', minutes)
        slow_requests = self.metrics.get_metric('slow_requests', minutes)
        
        return {
            'response_time': self.metrics.get_metric_summary('response_time', minutes),
            'error_count': len(errors),
            'slow_request_count': len(slow_requests),
            'top_endpoints': self.get_top_endpoints(minutes),
            'error_types': self.get_error_types(errors)
        }
    
    def get_top_endpoints(self, minutes=60):
        """Get top endpoints by request count"""
        endpoint_requests = self.metrics.get_metric('endpoint_requests', minutes)
        endpoint_counts = defaultdict(int)
        
        for entry in endpoint_requests:
            endpoint_counts[entry['value']] += 1
        
        return sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def get_error_types(self, errors):
        """Get error type distribution"""
        error_types = defaultdict(int)
        
        for entry in errors:
            if isinstance(entry['value'], dict):
                error_type = entry['value'].get('type', 'unknown')
                error_types[error_type] += 1
        
        return dict(error_types)

class HealthChecker:
    """System health checking"""
    
    def __init__(self):
        self.checks = {}
        self.register_default_checks()
    
    def register_default_checks(self):
        """Register default health checks"""
        self.register_check('database', self.check_database)
        self.register_check('cache', self.check_cache)
        self.register_check('disk_space', self.check_disk_space)
        self.register_check('memory', self.check_memory)
        self.register_check('external_services', self.check_external_services)
    
    def register_check(self, name, check_function):
        """Register a health check"""
        self.checks[name] = check_function
    
    def check_database(self):
        """Check database connectivity"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return {
                    'status': 'healthy' if result else 'unhealthy',
                    'message': 'Database connection successful' if result else 'Database query failed'
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Database error: {str(e)}'
            }
    
    def check_cache(self):
        """Check cache connectivity"""
        try:
            cache.set('health_check', 'ok', 10)
            result = cache.get('health_check')
            return {
                'status': 'healthy' if result == 'ok' else 'unhealthy',
                'message': 'Cache connection successful' if result == 'ok' else 'Cache test failed'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Cache error: {str(e)}'
            }
    
    def check_disk_space(self):
        """Check disk space"""
        try:
            disk = psutil.disk_usage('/')
            free_percent = (disk.free / disk.total) * 100
            
            if free_percent < 10:
                status = 'critical'
                message = f'Low disk space: {free_percent:.1f}% free'
            elif free_percent < 20:
                status = 'warning'
                message = f'Disk space warning: {free_percent:.1f}% free'
            else:
                status = 'healthy'
                message = f'Disk space OK: {free_percent:.1f}% free'
            
            return {
                'status': status,
                'message': message,
                'free_percent': free_percent
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Disk space check failed: {str(e)}'
            }
    
    def check_memory(self):
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                status = 'critical'
                message = f'High memory usage: {memory.percent:.1f}%'
            elif memory.percent > 80:
                status = 'warning'
                message = f'Memory usage warning: {memory.percent:.1f}%'
            else:
                status = 'healthy'
                message = f'Memory usage OK: {memory.percent:.1f}%'
            
            return {
                'status': status,
                'message': message,
                'usage_percent': memory.percent
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Memory check failed: {str(e)}'
            }
    
    def check_external_services(self):
        """Check external services"""
        # This would check external APIs, email services, etc.
        return {
            'status': 'healthy',
            'message': 'External services check not implemented'
        }
    
    def run_all_checks(self):
        """Run all health checks"""
        results = {}
        overall_status = 'healthy'
        
        for name, check_function in self.checks.items():
            try:
                result = check_function()
                results[name] = result
                
                if result['status'] == 'critical':
                    overall_status = 'critical'
                elif result['status'] == 'warning' and overall_status == 'healthy':
                    overall_status = 'warning'
                elif result['status'] == 'unhealthy':
                    overall_status = 'unhealthy'
            except Exception as e:
                results[name] = {
                    'status': 'unhealthy',
                    'message': f'Check failed: {str(e)}'
                }
                overall_status = 'unhealthy'
        
        return {
            'overall_status': overall_status,
            'checks': results,
            'timestamp': timezone.now().isoformat()
        }

class AuditLogger:
    """Enhanced audit logging"""
    
    def __init__(self):
        self.audit_logger = logging.getLogger('audit')
        self.audit_logger.setLevel(logging.INFO)
    
    def log_user_action(self, user, action, resource, details=None):
        """Log user action"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'user_email': user.email if user else None,
            'action': action,
            'resource': resource,
            'details': details or {}
        }
        
        self.audit_logger.info(f"User action: {json.dumps(log_data)}")
    
    def log_data_access(self, user, resource, action, ip_address=None):
        """Log data access"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'user_email': user.email if user else None,
            'resource': resource,
            'action': action,
            'ip_address': ip_address
        }
        
        self.audit_logger.info(f"Data access: {json.dumps(log_data)}")
    
    def log_security_event(self, event_type, user, details=None):
        """Log security event"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'event_type': event_type,
            'user_id': user.id if user else None,
            'user_email': user.email if user else None,
            'details': details or {}
        }
        
        self.audit_logger.warning(f"Security event: {json.dumps(log_data)}")
    
    def log_system_event(self, event_type, details=None):
        """Log system event"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'event_type': event_type,
            'details': details or {}
        }
        
        self.audit_logger.info(f"System event: {json.dumps(log_data)}")

class AlertManager:
    """Alert management system"""
    
    def __init__(self):
        self.alerts = deque(maxlen=1000)  # Keep last 1000 alerts
        self.alert_thresholds = {
            'response_time': 2.0,  # seconds
            'error_rate': 0.1,  # 10%
            'memory_usage': 90,  # percent
            'disk_usage': 90,  # percent
            'cpu_usage': 90,  # percent
        }
    
    def check_alerts(self, metrics):
        """Check for alert conditions"""
        alerts = []
        
        # Check response time
        if 'response_time' in metrics:
            avg_response_time = metrics['response_time'].get('avg', 0)
            if avg_response_time > self.alert_thresholds['response_time']:
                alerts.append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': f'High response time: {avg_response_time:.2f}s',
                    'threshold': self.alert_thresholds['response_time']
                })
        
        # Check error rate
        if 'error_count' in metrics and 'request_count' in metrics:
            error_rate = metrics['error_count'] / max(metrics['request_count'], 1)
            if error_rate > self.alert_thresholds['error_rate']:
                alerts.append({
                    'type': 'error',
                    'severity': 'critical',
                    'message': f'High error rate: {error_rate:.2%}',
                    'threshold': self.alert_thresholds['error_rate']
                })
        
        # Check system resources
        system_stats = metrics.get('system_stats', {})
        
        if 'memory' in system_stats:
            memory_percent = system_stats['memory']['percent']
            if memory_percent > self.alert_thresholds['memory_usage']:
                alerts.append({
                    'type': 'resource',
                    'severity': 'critical',
                    'message': f'High memory usage: {memory_percent:.1f}%',
                    'threshold': self.alert_thresholds['memory_usage']
                })
        
        if 'disk' in system_stats:
            disk_percent = system_stats['disk']['percent']
            if disk_percent > self.alert_thresholds['disk_usage']:
                alerts.append({
                    'type': 'resource',
                    'severity': 'critical',
                    'message': f'High disk usage: {disk_percent:.1f}%',
                    'threshold': self.alert_thresholds['disk_usage']
                })
        
        # Store alerts
        for alert in alerts:
            alert['timestamp'] = timezone.now().isoformat()
            self.alerts.append(alert)
        
        return alerts
    
    def get_recent_alerts(self, minutes=60):
        """Get recent alerts"""
        cutoff = timezone.now() - timedelta(minutes=minutes)
        recent_alerts = []
        
        for alert in self.alerts:
            alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
            if alert_time >= cutoff:
                recent_alerts.append(alert)
        
        return recent_alerts

# Global instances
performance_monitor = PerformanceMonitor()
health_checker = HealthChecker()
audit_logger = AuditLogger()
alert_manager = AlertManager()

# Monitoring middleware
class MonitoringMiddleware:
    """Monitoring middleware for request tracking"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        performance_monitor.record_request(
            path=request.path,
            method=request.method,
            duration=duration,
            status_code=response.status_code,
            user_id=request.user.id if request.user.is_authenticated else None
        )
        
        # Add monitoring headers
        response['X-Response-Time'] = f"{duration:.3f}s"
        response['X-Request-ID'] = f"req_{int(time.time() * 1000)}"
        
        return response
