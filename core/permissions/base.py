# core/permissions/base.py
# Permission enforcement layer for Phase 3

from rest_framework.permissions import BasePermission
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ObjectTypePermission(BasePermission):
    """
    Permission class that checks if a user has permission for a specific object type and action.
    Maps HTTP methods to actions and checks against the user's role permissions.
    """
    
    # Map HTTP methods to action names
    METHOD_ACTION_MAP = {
        'GET': 'view',
        'POST': 'add',
        'PUT': 'change',
        'PATCH': 'change',
        'DELETE': 'delete',
    }
    
    def has_permission(self, request, view):
        """
        Check if user has permission for the view's object type.
        """
        # Superusers have all permissions
        if request.user and request.user.is_superuser:
            return True
        
        # Get object type from view
        object_type = self.get_object_type(view)
        if not object_type:
            # If no object type is defined, default to allow
            return True
        
        # Get action from HTTP method
        action = self.METHOD_ACTION_MAP.get(request.method, 'view')
        
        # Check permission
        has_perm = self.check_permission(request.user, object_type, action, request)
        
        if not has_perm:
            self.log_permission_denial(request.user, object_type, action, request)
        
        return has_perm
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission for a specific object instance.
        """
        # Superusers have all permissions
        if request.user and request.user.is_superuser:
            return True
        
        # Get object type from view or object
        object_type = self.get_object_type(view)
        if not object_type:
            return True
        
        # Get action from HTTP method
        action = self.METHOD_ACTION_MAP.get(request.method, 'view')
        
        # Check permission
        has_perm = self.check_object_permission(request.user, obj, action, request)
        
        if not has_perm:
            self.log_permission_denial(request.user, object_type, action, request, obj)
        
        return has_perm
    
    def get_object_type(self, view):
        """
        Extract object type from view.
        Can be overridden by view by setting object_type attribute.
        """
        if hasattr(view, 'object_type'):
            return view.object_type
        
        # Try to infer from model
        if hasattr(view, 'queryset') and view.queryset is not None:
            return view.queryset.model.__name__.lower()
        
        if hasattr(view, 'model'):
            return view.model.__name__.lower()
        
        return None
    
    def check_permission(self, user, object_type, action, request):
        """
        Check if user has permission for object_type and action.
        Override this method to implement custom permission logic.
        """
        if not user or not user.is_authenticated:
            return False
        
        # Check if user has company access
        if not hasattr(request, 'company') or not request.company:
            return False
        
        # Get user's role for this company
        from core.models import UserCompanyAccess
        try:
            access = UserCompanyAccess.objects.get(
                user=user,
                company=request.company,
                is_active=True
            )
            role = access.role
        except UserCompanyAccess.DoesNotExist:
            return False
        
        # Define role-based permissions
        # Admin has full access
        if role == 'admin':
            return True
        
        # Manager can view, add, and change but not delete
        if role == 'manager':
            return action in ['view', 'add', 'change']
        
        # Regular user can only view
        if role == 'user':
            return action == 'view'
        
        # Sales rep has special permissions for their assigned records
        if role == 'sales_rep':
            return action in ['view', 'add', 'change']
        
        return False
    
    def check_object_permission(self, user, obj, action, request):
        """
        Check if user has permission for a specific object instance.
        This can include ownership checks, etc.
        """
        # First check general permission
        if not self.check_permission(user, obj.__class__.__name__.lower(), action, request):
            return False
        
        # Check ownership for non-admins
        if hasattr(obj, 'owner') and obj.owner:
            # Owner has full access to their own records
            if obj.owner == user:
                return True
            
            # Others need manager or admin role for non-view actions
            if action != 'view':
                from core.models import UserCompanyAccess
                try:
                    access = UserCompanyAccess.objects.get(
                        user=user,
                        company=request.company,
                        is_active=True
                    )
                    return access.role in ['admin', 'manager']
                except UserCompanyAccess.DoesNotExist:
                    return False
        
        return True
    
    def log_permission_denial(self, user, object_type, action, request, obj=None):
        """
        Log permission denial for security auditing.
        """
        user_id = user.id if user else None
        user_email = user.email if user and hasattr(user, 'email') else 'anonymous'
        ip_address = self.get_client_ip(request)
        
        log_data = {
            'event': 'permission_denied',
            'user_id': str(user_id),
            'user_email': user_email,
            'object_type': object_type,
            'action': action,
            'ip_address': ip_address,
            'path': request.path,
            'method': request.method,
        }
        
        if obj:
            log_data['object_id'] = getattr(obj, 'id', None)
        
        logger.warning(f"Permission denied: {log_data}")
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ActionPermission(ObjectTypePermission):
    """
    Permission class that allows specifying custom actions beyond CRUD.
    """
    
    def has_permission(self, request, view):
        """
        Check permission for custom actions.
        """
        # Check if this is a custom action
        if hasattr(view, 'action') and view.action:
            action = view.action
            object_type = self.get_object_type(view)
            
            if object_type:
                has_perm = self.check_action_permission(
                    request.user, object_type, action, request
                )
                
                if not has_perm:
                    self.log_permission_denial(request.user, object_type, action, request)
                
                return has_perm
        
        # Fall back to standard permission check
        return super().has_permission(request, view)
    
    def check_action_permission(self, user, object_type, action, request):
        """
        Check permission for custom actions.
        Can be overridden for action-specific logic.
        """
        # Map common actions to basic permissions
        view_actions = ['list', 'retrieve', 'pipeline', 'forecast', 'board']
        change_actions = ['update', 'partial_update', 'change_stage', 'move']
        create_actions = ['create']
        delete_actions = ['destroy', 'delete']
        
        if action in view_actions:
            return self.check_permission(user, object_type, 'view', request)
        elif action in change_actions:
            return self.check_permission(user, object_type, 'change', request)
        elif action in create_actions:
            return self.check_permission(user, object_type, 'add', request)
        elif action in delete_actions:
            return self.check_permission(user, object_type, 'delete', request)
        
        # Default to view permission for unknown actions
        return self.check_permission(user, object_type, 'view', request)
