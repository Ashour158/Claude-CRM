# core/middleware.py
# Complete middleware for multi-tenancy and company access

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

try:
    from .models import Company, UserCompanyAccess, AuditLog
    User = get_user_model()
except ImportError:
    # Handle import errors gracefully
    Company = None
    UserCompanyAccess = None
    User = None
    AuditLog = None

class MultiTenantMiddleware(MiddlewareMixin):
    """Middleware to handle multi-tenant context"""
    
    def process_request(self, request):
        # Set company context from user's company access
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                if UserCompanyAccess and Company:
                    company_access = UserCompanyAccess.objects.filter(
                        user=request.user,
                        is_active=True
                    ).first()
                    if company_access:
                        request.company = company_access.company
                    else:
                        request.company = None
                else:
                    request.company = None
            except Exception as e:
                logger.error(f"Error in MultiTenantMiddleware: {e}")
                request.company = None
        else:
            request.company = None
        
        return None

class CompanyAccessMiddleware(MiddlewareMixin):
    """Middleware to check company access permissions"""
    
    def process_request(self, request):
        # Skip for admin and API endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/api/'):
            return None
        
        # Check if user has access to the company
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request, 'company') and request.company:
                try:
                    if UserCompanyAccess:
                        company_access = UserCompanyAccess.objects.filter(
                            user=request.user,
                            company=request.company,
                            is_active=True
                        ).exists()
                        
                        if not company_access:
                            return HttpResponseForbidden("Access denied to this company")
                except Exception as e:
                    logger.error(f"Error in CompanyAccessMiddleware: {e}")
                    return HttpResponseForbidden("Access denied")
        
        return None

class SessionCleanupMiddleware(MiddlewareMixin):
    """Middleware to clean up expired sessions"""
    
    def process_request(self, request):
        # Clean up expired sessions
        try:
            from django.contrib.sessions.models import Session
            Session.objects.filter(expire_date__lt=timezone.now()).delete()
        except Exception as e:
            logger.error(f"Error in SessionCleanupMiddleware: {e}")
        
        return None

class PermissionCheckMiddleware(MiddlewareMixin):
    """Middleware to check user permissions"""
    
    def process_request(self, request):
        # Check user permissions
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Add permission checks here if needed
            pass
        
        return None

class AuditLogMiddleware(MiddlewareMixin):
    """Middleware to log user actions for audit purposes"""
    
    def process_request(self, request):
        # Log request details for audit
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                if AuditLog:
                    # Log the request
                    AuditLog.objects.create(
                        action='view',
                        user=request.user,
                        company=getattr(request, 'company', None),
                        object_type=request.path,
                        details={
                            'method': request.method,
                            'path': request.path,
                            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        },
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
            except Exception as e:
                # Silently fail if audit logging fails
                logger.error(f"Error in AuditLogMiddleware: {e}")
        
        return None
