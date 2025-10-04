# core/middleware.py
# Middleware for multi-tenant context and Row-Level Security

from django.db import connection
from django.http import JsonResponse
from core.models import UserCompanyAccess, Company

class MultiTenantMiddleware:
    """
    Middleware to handle multi-tenant context.
    Sets the active company for the current request and configures
    PostgreSQL session variables for Row-Level Security.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for non-authenticated requests
        if not request.user.is_authenticated:
            response = self.get_response(request)
            return response
        
        # Get active company from session
        active_company_id = request.session.get('active_company_id')
        
        # If no active company in session, set it to user's primary company
        if not active_company_id:
            access = UserCompanyAccess.objects.filter(
                user=request.user,
                is_active=True,
                is_primary=True
            ).select_related('company').first()
            
            if access:
                active_company_id = str(access.company.id)
                request.session['active_company_id'] = active_company_id
        
        # Set company context for Row-Level Security
        if active_company_id:
            try:
                # Verify user has access to this company
                has_access = UserCompanyAccess.objects.filter(
                    user=request.user,
                    company_id=active_company_id,
                    is_active=True
                ).exists()
                
                if not has_access and not request.user.is_superadmin:
                    # User doesn't have access to this company
                    return JsonResponse({
                        'error': 'Access denied to this company.'
                    }, status=403)
                
                # Set PostgreSQL session variables for RLS
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SET LOCAL app.current_user_id = %s",
                        [str(request.user.id)]
                    )
                    cursor.execute(
                        "SET LOCAL app.current_company_id = %s",
                        [active_company_id]
                    )
                
                # Add company to request for easy access
                request.active_company = Company.objects.get(id=active_company_id)
                
            except Company.DoesNotExist:
                pass
        
        response = self.get_response(request)
        return response


class CompanyAccessMiddleware:
    """
    Middleware to inject company context into models being saved.
    This ensures all company-isolated models have the company field set.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Store active company in thread-local storage
        # This can be accessed by models during save()
        if hasattr(request, 'active_company'):
            from threading import local
            _thread_locals = local()
            _thread_locals.company = request.active_company
        
        response = self.get_response(request)
        return response


class SessionCleanupMiddleware:
    """
    Middleware to cleanup expired sessions periodically.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.cleanup_counter = 0
    
    def __call__(self, request):
        # Cleanup expired sessions every 100 requests
        self.cleanup_counter += 1
        if self.cleanup_counter >= 100:
            from core.models import UserSession
            UserSession.cleanup_expired()
            self.cleanup_counter = 0
        
        response = self.get_response(request)
        return response


class PermissionCheckMiddleware:
    """
    Middleware to check user permissions for the active company.
    Adds permission context to the request.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request, 'active_company'):
            # Get user's permissions for active company
            access = UserCompanyAccess.objects.filter(
                user=request.user,
                company=request.active_company,
                is_active=True
            ).first()
            
            if access:
                request.permissions = {
                    'role': access.role,
                    'can_create': access.can_create,
                    'can_read': access.can_read,
                    'can_update': access.can_update,
                    'can_delete': access.can_delete,
                    'can_export': access.can_export,
                }
            else:
                request.permissions = {
                    'role': 'viewer',
                    'can_create': False,
                    'can_read': True,
                    'can_update': False,
                    'can_delete': False,
                    'can_export': False,
                }
        
        response = self.get_response(request)
        return response


class AuditLogMiddleware:
    """
    Middleware to log important actions for audit trail.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Store request details that might be needed for audit logs
        if request.user.is_authenticated:
            request.audit_context = {
                'user_id': str(request.user.id),
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'company_id': request.session.get('active_company_id'),
            }
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip