# core/security_enhanced.py
# Enhanced security utilities and middleware

import hashlib
import hmac
import secrets
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.response import Response
import ipaddress
import re
import json

logger = logging.getLogger(__name__)
User = get_user_model()

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Enhanced security headers middleware"""
    
    def process_response(self, request, response):
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response['Content-Security-Policy'] = csp
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # HSTS (only in production)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response

class RateLimitMiddleware(MiddlewareMixin):
    """Enhanced rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            'api': {'limit': 100, 'window': 60},  # 100 requests per minute
            'auth': {'limit': 10, 'window': 60},  # 10 requests per minute
            'upload': {'limit': 20, 'window': 60},  # 20 requests per minute
            'search': {'limit': 50, 'window': 60},  # 50 requests per minute
        }
    
    def process_request(self, request):
        if not getattr(settings, 'RATE_LIMIT_ENABLED', True):
            return None
        
        # Get client identifier
        client_id = self.get_client_id(request)
        endpoint_type = self.get_endpoint_type(request.path)
        
        if not endpoint_type:
            return None
        
        # Check rate limit
        if self.is_rate_limited(client_id, endpoint_type):
            logger.warning(f"Rate limit exceeded for {client_id} on {request.path}")
            return HttpResponseForbidden(
                json.dumps({
                    'error': 'Rate limit exceeded',
                    'details': 'Too many requests. Please try again later.',
                    'retry_after': 60
                }),
                content_type='application/json',
                status=429
            )
        
        return None
    
    def get_client_id(self, request):
        """Get unique client identifier"""
        # Try to get real IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Use user ID if authenticated, otherwise IP
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        else:
            return f"ip:{ip}"
    
    def get_endpoint_type(self, path):
        """Determine endpoint type for rate limiting"""
        if path.startswith('/api/core/auth/'):
            return 'auth'
        elif path.startswith('/api/') and 'upload' in path:
            return 'upload'
        elif path.startswith('/api/') and 'search' in path:
            return 'search'
        elif path.startswith('/api/'):
            return 'api'
        return None
    
    def is_rate_limited(self, client_id, endpoint_type):
        """Check if client is rate limited"""
        rate_limit = self.rate_limits.get(endpoint_type)
        if not rate_limit:
            return False
        
        cache_key = f"rate_limit:{endpoint_type}:{client_id}"
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= rate_limit['limit']:
            return True
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, rate_limit['window'])
        return False

class IPWhitelistMiddleware(MiddlewareMixin):
    """IP whitelist middleware for admin access"""
    
    def process_request(self, request):
        # Only apply to admin and sensitive endpoints
        if not (request.path.startswith('/admin/') or 
                request.path.startswith('/api/core/') or
                request.path.startswith('/api/system-config/')):
            return None
        
        client_ip = self.get_client_ip(request)
        whitelist = getattr(settings, 'IP_WHITELIST', [])
        
        if whitelist and not self.is_ip_allowed(client_ip, whitelist):
            logger.warning(f"Blocked IP {client_ip} from accessing {request.path}")
            return HttpResponseForbidden("Access denied from this IP address")
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    def is_ip_allowed(self, ip, whitelist):
        """Check if IP is in whitelist"""
        try:
            client_ip = ipaddress.ip_address(ip)
            for allowed_ip in whitelist:
                if client_ip in ipaddress.ip_network(allowed_ip, strict=False):
                    return True
        except ValueError:
            pass
        return False

class DataSanitizationMiddleware(MiddlewareMixin):
    """Data sanitization middleware"""
    
    def process_request(self, request):
        # Sanitize request data
        if hasattr(request, 'data'):
            self.sanitize_data(request.data)
        
        return None
    
    def sanitize_data(self, data):
        """Sanitize request data"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = self.sanitize_string(value)
                elif isinstance(value, dict):
                    self.sanitize_data(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self.sanitize_data(item)
    
    def sanitize_string(self, value):
        """Sanitize string value"""
        # Remove potential XSS vectors
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
        value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
        
        # Limit length
        if len(value) > 10000:
            value = value[:10000]
        
        return value

class AuditSecurityMiddleware(MiddlewareMixin):
    """Security audit middleware"""
    
    def process_request(self, request):
        # Log security-relevant requests
        if self.is_security_relevant(request):
            self.log_security_event(request)
        
        return None
    
    def is_security_relevant(self, request):
        """Check if request is security-relevant"""
        security_paths = [
            '/admin/',
            '/api/core/auth/',
            '/api/system-config/',
            '/api/integrations/',
        ]
        
        return any(request.path.startswith(path) for path in security_paths)
    
    def log_security_event(self, request):
        """Log security event"""
        event_data = {
            'timestamp': timezone.now().isoformat(),
            'user': request.user.id if request.user.is_authenticated else None,
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'path': request.path,
            'method': request.method,
            'referer': request.META.get('HTTP_REFERER', ''),
        }
        
        logger.info(f"Security event: {json.dumps(event_data)}")
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

class EncryptionUtils:
    """Encryption utilities for sensitive data"""
    
    @staticmethod
    def encrypt_field(value, key=None):
        """Encrypt sensitive field value"""
        if not value:
            return value
        
        if not key:
            key = getattr(settings, 'ENCRYPTION_KEY', 'default-key')
        
        # Use HMAC for encryption
        encrypted = hmac.new(
            key.encode(),
            str(value).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return encrypted
    
    @staticmethod
    def hash_password(password):
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{hashed.hex()}"
    
    @staticmethod
    def verify_password(password, hashed):
        """Verify password against hash"""
        try:
            salt, hash_value = hashed.split(':')
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hmac.compare_digest(hash_value, new_hash.hex())
        except ValueError:
            return False

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format"""
        pattern = r'^\+?1?\d{9,15}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def validate_url(url):
        """Validate URL format"""
        pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
        return re.match(pattern, url) is not None

class PermissionChecker:
    """Enhanced permission checking"""
    
    @staticmethod
    def check_company_access(user, company):
        """Check if user has access to company"""
        if user.is_superuser:
            return True
        
        try:
            access = UserCompanyAccess.objects.get(
                user=user,
                company=company,
                is_active=True
            )
            return True
        except UserCompanyAccess.DoesNotExist:
            return False
    
    @staticmethod
    def check_object_permission(user, obj, action='view'):
        """Check if user has permission for object action"""
        if user.is_superuser:
            return True
        
        # Check company access
        if hasattr(obj, 'company'):
            if not PermissionChecker.check_company_access(user, obj.company):
                return False
        
        # Check ownership
        if hasattr(obj, 'owner'):
            if obj.owner == user:
                return True
        
        # Check role-based permissions
        if hasattr(obj, 'company'):
            try:
                access = UserCompanyAccess.objects.get(
                    user=user,
                    company=obj.company,
                    is_active=True
                )
                role = access.role
                
                # Define role permissions
                role_permissions = {
                    'admin': ['view', 'add', 'change', 'delete'],
                    'manager': ['view', 'add', 'change'],
                    'user': ['view']
                }
                
                return action in role_permissions.get(role, [])
            except UserCompanyAccess.DoesNotExist:
                return False
        
        return False

class SecurityAuditLogger:
    """Security audit logging"""
    
    @staticmethod
    def log_login_attempt(user, success, ip_address, user_agent):
        """Log login attempt"""
        event_data = {
            'event_type': 'login_attempt',
            'user_id': user.id if user else None,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Security audit: {json.dumps(event_data)}")
    
    @staticmethod
    def log_permission_denied(user, resource, action, ip_address):
        """Log permission denied event"""
        event_data = {
            'event_type': 'permission_denied',
            'user_id': user.id if user else None,
            'resource': resource,
            'action': action,
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.warning(f"Security audit: {json.dumps(event_data)}")
    
    @staticmethod
    def log_data_access(user, resource, action, ip_address):
        """Log data access event"""
        event_data = {
            'event_type': 'data_access',
            'user_id': user.id if user else None,
            'resource': resource,
            'action': action,
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Security audit: {json.dumps(event_data)}")

class SecurityHeaders:
    """Security headers configuration"""
    
    @staticmethod
    def get_csp_header():
        """Get Content Security Policy header"""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    
    @staticmethod
    def get_security_headers():
        """Get all security headers"""
        return {
            'Content-Security-Policy': SecurityHeaders.get_csp_header(),
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        }
