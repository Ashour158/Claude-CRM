# core/permissions.py
# DRF Permission classes for Phase 3 enforcement

import logging
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from core.security_enhanced import PermissionChecker

logger = logging.getLogger(__name__)


class CRMPermission(permissions.BasePermission):
    """
    Base permission class that enforces object_type and action-based permissions.
    Maps HTTP verbs to actions and integrates with existing permission evaluator.
    """
    
    # Map HTTP methods to permission actions
    METHOD_ACTION_MAP = {
        'GET': 'view',
        'HEAD': 'view',
        'OPTIONS': 'view',
        'POST': 'create',
        'PUT': 'update',
        'PATCH': 'update',
        'DELETE': 'delete',
    }
    
    def has_permission(self, request, view):
        """
        Check if user has permission for the request.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers always have permission
        if request.user.is_superuser:
            return True
        
        # Determine object type from view
        object_type = self._get_object_type(view)
        if not object_type:
            logger.warning(f"Could not determine object type for view {view.__class__.__name__}")
            return True  # Allow if we can't determine (fail-open for now)
        
        # Determine action from HTTP method
        action = self.METHOD_ACTION_MAP.get(request.method, 'view')
        
        # Check permission using existing evaluator
        has_perm = self._check_permission(request.user, object_type, action)
        
        if not has_perm:
            # Log denied action
            self._log_denied_action(request, object_type, action)
            
        return has_perm
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission for specific object.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers always have permission
        if request.user.is_superuser:
            return True
        
        # Determine action from HTTP method
        action = self.METHOD_ACTION_MAP.get(request.method, 'view')
        
        # Check object-level permission
        has_perm = PermissionChecker.check_object_permission(
            request.user,
            obj,
            action
        )
        
        if not has_perm:
            # Log denied action
            object_type = obj.__class__.__name__.lower()
            self._log_denied_action(request, object_type, action, obj.id if hasattr(obj, 'id') else None)
        
        return has_perm
    
    def _get_object_type(self, view):
        """Extract object type from view."""
        # Try to get from view's queryset model
        if hasattr(view, 'queryset') and view.queryset is not None:
            return view.queryset.model.__name__.lower()
        
        # Try to get from serializer
        if hasattr(view, 'get_serializer_class'):
            try:
                serializer_class = view.get_serializer_class()
                if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'model'):
                    return serializer_class.Meta.model.__name__.lower()
            except:
                pass
        
        return None
    
    def _check_permission(self, user, object_type: str, action: str) -> bool:
        """
        Check permission using existing permission evaluator.
        Integrates with core.security_enhanced.PermissionChecker.
        """
        # For now, use simplified check
        # In a full implementation, this would integrate with a permission
        # evaluation system that checks against role-based permissions
        
        # Check if user has company access
        if not hasattr(user, 'company_access'):
            return False
        
        company_access = user.company_access.filter(is_active=True).first()
        if not company_access:
            return False
        
        role = company_access.role
        
        # Define role-based permissions
        role_permissions = {
            'admin': ['view', 'create', 'update', 'delete'],
            'manager': ['view', 'create', 'update'],
            'user': ['view', 'create'],
            'read_only': ['view'],
        }
        
        allowed_actions = role_permissions.get(role, ['view'])
        return action in allowed_actions
    
    def _log_denied_action(self, request, object_type: str, action: str, object_id=None):
        """Log denied permission action."""
        logger.warning(
            f"Permission denied: user={request.user.email} "
            f"action={action} object_type={object_type} "
            f"object_id={object_id} path={request.path}",
            extra={
                'user_id': request.user.id,
                'user_email': request.user.email,
                'object_type': object_type,
                'action': action,
                'object_id': object_id,
                'path': request.path,
                'method': request.method,
            }
        )
    
    @staticmethod
    def create_403_response(message: str = None, details: dict = None):
        """
        Create structured 403 error response.
        
        Returns:
            PermissionDenied exception with structured payload
        """
        error_data = {
            'error': 'permission_denied',
            'message': message or 'You do not have permission to perform this action',
        }
        
        if details:
            error_data['details'] = details
        
        raise PermissionDenied(detail=error_data)


class AccountPermission(CRMPermission):
    """Permission class for Account operations."""
    pass


class ContactPermission(CRMPermission):
    """Permission class for Contact operations."""
    pass


class LeadPermission(CRMPermission):
    """Permission class for Lead operations."""
    pass


class DealPermission(CRMPermission):
    """Permission class for Deal operations."""
    pass


class SavedViewPermission(CRMPermission):
    """
    Permission class for SavedListView operations.
    Users can only manage their own private views or shared views if they're managers/admins.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check permission for specific saved view."""
        # Call parent check first
        has_base_perm = super().has_object_permission(request, view, obj)
        if not has_base_perm:
            return False
        
        # For private views, only owner or admins can access
        if obj.is_private:
            if obj.owner == request.user or request.user.is_superuser:
                return True
            
            # Check if user is admin/manager
            company_access = request.user.company_access.filter(
                company=obj.organization,
                is_active=True
            ).first()
            if company_access and company_access.role in ['admin', 'manager']:
                return True
            
            return False
        
        # For shared views, any user in the organization can view
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # For modifications, only owner or admins
        if obj.owner == request.user or request.user.is_superuser:
            return True
        
        company_access = request.user.company_access.filter(
            company=obj.organization,
            is_active=True
        ).first()
        return company_access and company_access.role in ['admin', 'manager']
