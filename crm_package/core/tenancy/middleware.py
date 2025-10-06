"""
Tenancy Middleware (Placeholder)

This middleware will extract organization/tenant information from requests
and set it in the context for row-level security enforcement.

IMPORTANT: This middleware is NOT enabled in settings.py yet. It's scaffolding
for future implementation. Enable it only after models have been migrated to
use TenantOwnedModel.

Future implementation will:
1. Extract organization ID from X-Org-ID header or user profile
2. Validate user has access to the organization
3. Set organization context for the request lifecycle
4. Apply automatic filtering to tenant-owned querysets
"""

from typing import Callable
import logging
import uuid

try:
    from django.http import HttpRequest, HttpResponse, JsonResponse
    DJANGO_AVAILABLE = True
except ImportError:
    # Allow import without Django for testing/documentation
    DJANGO_AVAILABLE = False
    HttpRequest = None
    HttpResponse = None
    JsonResponse = None

from .context import set_current_organization_id, clear_current_organization

logger = logging.getLogger(__name__)


class TenancyMiddleware:
    """
    Middleware to handle multi-tenant context (row-level tenancy).
    
    This is a placeholder implementation. To enable:
    1. Add 'crm_package.core.tenancy.middleware.TenancyMiddleware' to MIDDLEWARE in settings
    2. Ensure all tenant-owned models inherit from TenantOwnedModel
    3. Update selectors to use tenant-aware filtering
    """
    
    def __init__(self, get_response: Callable) -> None:
        if not DJANGO_AVAILABLE:
            raise RuntimeError("Django is required to use TenancyMiddleware")
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process request and set tenant context.
        
        Args:
            request: The incoming HTTP request
            
        Returns:
            HttpResponse: The response from the view
        """
        # Clear any existing organization context
        clear_current_organization()
        
        # Skip for unauthenticated requests
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        try:
            # Option 1: Get organization from X-Org-ID header
            org_id_header = request.headers.get('X-Org-ID')
            
            if org_id_header:
                try:
                    org_id = uuid.UUID(org_id_header)
                    # TODO: Validate user has access to this organization
                    # access = UserCompanyAccess.objects.filter(
                    #     user=request.user,
                    #     company_id=org_id,
                    #     is_active=True
                    # ).exists()
                    # if not access:
                    #     return JsonResponse({'error': 'Access denied to organization'}, status=403)
                    
                    set_current_organization_id(org_id)
                    request.organization_id = org_id
                except ValueError:
                    logger.warning(f"Invalid organization ID format in header: {org_id_header}")
            
            # Option 2: Get from session (active_company_id)
            elif hasattr(request, 'session') and 'active_company_id' in request.session:
                try:
                    org_id = uuid.UUID(request.session['active_company_id'])
                    set_current_organization_id(org_id)
                    request.organization_id = org_id
                except (ValueError, KeyError):
                    pass
            
            # Option 3: Get user's primary organization
            # else:
            #     TODO: Query UserCompanyAccess for primary organization
            #     access = UserCompanyAccess.objects.filter(
            #         user=request.user,
            #         is_active=True,
            #         is_primary=True
            #     ).first()
            #     if access:
            #         set_current_organization_id(access.company_id)
            #         request.organization_id = access.company_id
            
        except Exception as e:
            logger.error(f"Error setting tenant context: {e}")
        
        response = self.get_response(request)
        
        # Clear context after request
        clear_current_organization()
        
        return response
