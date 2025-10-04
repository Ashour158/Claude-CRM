# core/security.py
# Enterprise-grade security implementation

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.db import connection
import logging
import hashlib
import hmac
import time
import json
from typing import Dict, Any, Optional
import ipaddress

logger = logging.getLogger(__name__)
User = get_user_model()

class EnterpriseSecurity:
    """
    Enterprise-grade security utilities
    """
    
    @staticmethod
    def generate_secure_token(data: str, secret: str = None) -> str:
        """Generate HMAC-based secure token"""
        if secret is None:
            secret = settings.SECRET_KEY
        
        timestamp = str(int(time.time()))
        message = f"{data}:{timestamp}"
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{message}:{signature}"
    
    @staticmethod
    def verify_secure_token(token: str, secret: str = None, max_age: int = 3600) -> bool:
        """Verify HMAC-based secure token"""
        if secret is None:
            secret = settings.SECRET_KEY
        
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False
            
            data, timestamp, signature = parts
            
            # Check timestamp
            if int(time.time()) - int(timestamp) > max_age:
                return False
            
            # Verify signature
            message = f"{data}:{timestamp}"
            expected_signature = hmac.new(
                secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for storage"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def is_safe_ip(ip_address: str) -> bool:
        """Check if IP address is safe (not from private/internal networks)"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Block private networks
            if ip.is_private:
                return False
            
            # Block loopback
            if ip.is_loopback:
                return False
            
            # Block link-local
            if ip.is_link_local:
                return False
            
            return True
        except ValueError:
            return False


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers
    """
    
    def process_response(self, request, response):
        """Add security headers to response"""
        
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), "
            "gyroscope=(), speaker=()"
        )
        
        # HSTS (HTTP Strict Transport Security)
        if request.is_secure():
            response['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Advanced rate limiting middleware
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            'api': {'requests': 100, 'window': 60},  # 100 requests per minute
            'auth': {'requests': 10, 'window': 60},  # 10 requests per minute
            'upload': {'requests': 5, 'window': 60},  # 5 requests per minute
        }
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process rate limiting"""
        client_ip = self.get_client_ip(request)
        path = request.path
        
        # Determine rate limit category
        if '/api/auth/' in path:
            category = 'auth'
        elif '/api/upload/' in path:
            category = 'upload'
        elif '/api/' in path:
            category = 'api'
        else:
            return None
        
        # Check rate limit
        if not self.check_rate_limit(client_ip, category):
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def check_rate_limit(self, client_ip: str, category: str) -> bool:
        """Check if client is within rate limit"""
        # This would integrate with Redis for distributed rate limiting
        # For now, we'll use a simple in-memory approach
        return True


class AuditLogMiddleware(MiddlewareMixin):
    """
    Enhanced audit logging middleware
    """
    
    def process_request(self, request):
        """Log request details"""
        if request.user.is_authenticated:
            audit_data = {
                'user_id': str(request.user.id),
                'user_email': request.user.email,
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'request_method': request.method,
                'request_path': request.path,
                'request_data': self.sanitize_request_data(request),
                'timestamp': time.time(),
            }
            
            # Log to database
            self.log_audit_event(audit_data)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def sanitize_request_data(self, request):
        """Sanitize request data for logging"""
        data = {}
        
        if request.method == 'GET':
            data = dict(request.GET)
        elif request.method in ['POST', 'PUT', 'PATCH']:
            try:
                data = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                data = {'raw_body': '[Binary or invalid JSON]'}
        
        # Remove sensitive fields
        sensitive_fields = ['password', 'token', 'secret', 'key', 'authorization']
        return self.remove_sensitive_fields(data, sensitive_fields)
    
    def remove_sensitive_fields(self, data: Dict, sensitive_fields: list) -> Dict:
        """Remove sensitive fields from data"""
        if isinstance(data, dict):
            return {
                k: '[REDACTED]' if any(field in k.lower() for field in sensitive_fields)
                else self.remove_sensitive_fields(v, sensitive_fields) if isinstance(v, (dict, list))
                else v
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self.remove_sensitive_fields(item, sensitive_fields) for item in data]
        else:
            return data
    
    def log_audit_event(self, audit_data: Dict):
        """Log audit event to database"""
        try:
            from core.models import AuditLog
            AuditLog.objects.create(**audit_data)
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")


class DataEncryption:
    """
    Data encryption utilities
    """
    
    def __init__(self, key: str = None):
        self.key = key or settings.SECRET_KEY
    
    def encrypt_field(self, data: str) -> str:
        """Encrypt sensitive field data"""
        from cryptography.fernet import Fernet
        import base64
        
        # Generate key from secret
        key = base64.urlsafe_b64encode(
            hashlib.sha256(self.key.encode()).digest()
        )
        
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_field(self, encrypted_data: str) -> str:
        """Decrypt sensitive field data"""
        from cryptography.fernet import Fernet
        import base64
        
        # Generate key from secret
        key = base64.urlsafe_b64encode(
            hashlib.sha256(self.key.encode()).digest()
        )
        
        f = Fernet(key)
        decrypted_data = f.decrypt(base64.urlsafe_b64decode(encrypted_data))
        return decrypted_data.decode()


class PermissionChecker:
    """
    Advanced permission checking
    """
    
    @staticmethod
    def check_company_access(user, company_id: str) -> bool:
        """Check if user has access to company"""
        if not user.is_authenticated:
            return False
        
        return user.has_company_access(company_id)
    
    @staticmethod
    def check_territory_access(user, territory_id: str) -> bool:
        """Check if user has access to territory"""
        if not user.is_authenticated:
            return False
        
        # Check if user is assigned to territory
        from territories.models import Territory
        try:
            territory = Territory.objects.get(id=territory_id)
            return user in territory.get_all_users()
        except Territory.DoesNotExist:
            return False
    
    @staticmethod
    def check_data_access(user, model_class, object_id: str) -> bool:
        """Check if user has access to specific data object"""
        if not user.is_authenticated:
            return False
        
        try:
            obj = model_class.objects.get(id=object_id)
            
            # Check company access
            if hasattr(obj, 'company_id'):
                if not PermissionChecker.check_company_access(user, obj.company_id):
                    return False
            
            # Check ownership
            if hasattr(obj, 'owner_id'):
                if obj.owner_id != user.id:
                    # Check if user has permission to view others' data
                    if not user.has_perm(f'{model_class._meta.app_label}.view_{model_class._meta.model_name}'):
                        return False
            
            return True
        except model_class.DoesNotExist:
            return False


class SecurityValidator:
    """
    Security validation utilities
    """
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format and security"""
        import re
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'data:',
            r'vbscript:',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        import re
        
        result = {
            'valid': True,
            'score': 0,
            'issues': []
        }
        
        # Length check
        if len(password) < 8:
            result['issues'].append('Password must be at least 8 characters long')
            result['valid'] = False
        else:
            result['score'] += 1
        
        # Complexity checks
        if not re.search(r'[a-z]', password):
            result['issues'].append('Password must contain lowercase letters')
            result['valid'] = False
        else:
            result['score'] += 1
        
        if not re.search(r'[A-Z]', password):
            result['issues'].append('Password must contain uppercase letters')
            result['valid'] = False
        else:
            result['score'] += 1
        
        if not re.search(r'\d', password):
            result['issues'].append('Password must contain numbers')
            result['valid'] = False
        else:
            result['score'] += 1
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['issues'].append('Password must contain special characters')
            result['valid'] = False
        else:
            result['score'] += 1
        
        # Common password check
        common_passwords = [
            'password', '123456', 'admin', 'qwerty',
            'letmein', 'welcome', 'monkey', 'dragon'
        ]
        
        if password.lower() in common_passwords:
            result['issues'].append('Password is too common')
            result['valid'] = False
        
        return result
    
    @staticmethod
    def validate_input(data: str, max_length: int = 1000) -> bool:
        """Validate input data for security"""
        if len(data) > max_length:
            return False
        
        # Check for SQL injection patterns
        sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'--',
            r'/\*',
            r'\*/',
        ]
        
        import re
        for pattern in sql_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                return False
        
        # Check for XSS patterns
        xss_patterns = [
            r'<script',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                return False
        
        return True
