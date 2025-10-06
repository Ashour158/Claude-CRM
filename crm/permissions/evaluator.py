# crm/permissions/evaluator.py
# Permission evaluator for checking user permissions

from typing import List, Optional, Set
from core.models import User, Company, UserCompanyAccess
from crm.permissions.models import Role, RolePermission
from crm.permissions.enums import PermissionAction, ObjectType


def get_user_role(user: User, organization: Company) -> Optional[Role]:
    """
    Get the user's role for a specific organization.
    
    Args:
        user: The user
        organization: The organization
        
    Returns:
        Role instance or None if user has no role
    """
    # Get user's company access
    try:
        access = UserCompanyAccess.objects.get(
            user=user,
            company=organization,
            is_active=True
        )
        
        # Map role string to Role object
        # For now, we use the role field from UserCompanyAccess
        # In a full implementation, you'd have a FK to Role
        role_code = access.role
        
        try:
            return Role.objects.get(
                organization=organization,
                code=role_code,
                is_active=True
            )
        except Role.DoesNotExist:
            return None
            
    except UserCompanyAccess.DoesNotExist:
        return None


def get_allowed_actions(
    user: User,
    object_type: str,
    organization: Company,
    obj: Optional[any] = None
) -> Set[str]:
    """
    Get set of allowed actions for a user on an object type.
    
    Args:
        user: The user
        object_type: Type of object (account, contact, etc.)
        organization: The organization
        obj: Optional specific object instance (for ownership checks)
        
    Returns:
        Set of allowed action strings
    """
    # Superusers can do everything
    if user.is_superuser:
        return {action.value for action in PermissionAction}
    
    # Get user's role
    role = get_user_role(user, organization)
    if not role:
        # No role = no permissions (except maybe VIEW for owned records)
        if obj and hasattr(obj, 'owner_id') and obj.owner_id == user.id:
            return {'view'}
        return set()
    
    # Get role permissions
    permissions = RolePermission.objects.filter(
        organization=organization,
        role=role,
        object_type=object_type
    ).values_list('action', flat=True)
    
    allowed_actions = set(permissions)
    
    # Object-level checks
    if obj:
        # Owners get additional permissions
        if hasattr(obj, 'owner_id') and obj.owner_id == user.id:
            allowed_actions.update(['view', 'edit'])
    
    return allowed_actions


def has_permission(
    user: User,
    object_type: str,
    action: str,
    organization: Company,
    obj: Optional[any] = None
) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        user: The user
        object_type: Type of object
        action: Action to check
        organization: The organization
        obj: Optional specific object instance
        
    Returns:
        True if user has permission, False otherwise
    """
    allowed = get_allowed_actions(user, object_type, organization, obj)
    return action in allowed


def can_user_perform_bulk_action(
    user: User,
    object_type: str,
    organization: Company
) -> bool:
    """Check if user can perform bulk actions"""
    return has_permission(user, object_type, 'bulk_update', organization)
