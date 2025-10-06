# crm/permissions/evaluator.py
"""
Permission evaluator for checking user permissions
"""
from crm.system.models import Role, RolePermission
from core.models import UserCompanyAccess


class PermissionEvaluator:
    """Evaluator for checking permissions"""
    
    @staticmethod
    def get_user_role(user, organization):
        """
        Get user's role in an organization
        
        Args:
            user: User instance
            organization: Company instance
            
        Returns:
            Role instance or None
        """
        try:
            access = UserCompanyAccess.objects.get(
                user=user,
                company=organization,
                is_active=True
            )
            
            # Get role by role name from UserCompanyAccess
            role = Role.objects.for_organization(organization).filter(
                code=access.role,
                is_active=True
            ).first()
            
            return role
        except UserCompanyAccess.DoesNotExist:
            return None
    
    @staticmethod
    def get_allowed_actions(user, organization, resource):
        """
        Get list of actions a user can perform on a resource
        
        Args:
            user: User instance
            organization: Company instance
            resource: Resource type (account, contact, lead, deal, etc.)
            
        Returns:
            List of allowed actions
        """
        # Superusers have all permissions
        if user.is_superuser:
            return ['create', 'read', 'update', 'delete', 'export', 'import']
        
        role = PermissionEvaluator.get_user_role(user, organization)
        if not role:
            return ['read']  # Default: read-only
        
        # Get permissions for this role and resource
        permissions = RolePermission.objects.for_organization(organization).filter(
            role=role,
            resource=resource,
            is_granted=True
        )
        
        allowed_actions = [perm.action for perm in permissions]
        
        # Include inherited permissions from parent roles
        if role.parent_role:
            parent_permissions = RolePermission.objects.for_organization(organization).filter(
                role=role.parent_role,
                resource=resource,
                is_granted=True
            )
            allowed_actions.extend([perm.action for perm in parent_permissions])
        
        return list(set(allowed_actions))  # Remove duplicates
    
    @staticmethod
    def has_permission(user, organization, resource, action):
        """
        Check if user has a specific permission
        
        Args:
            user: User instance
            organization: Company instance
            resource: Resource type
            action: Action to check
            
        Returns:
            Boolean
        """
        allowed_actions = PermissionEvaluator.get_allowed_actions(user, organization, resource)
        return action in allowed_actions
    
    @staticmethod
    def can_access_record(user, organization, record, action='read'):
        """
        Check if user can access a specific record
        
        Args:
            user: User instance
            organization: Company instance
            record: Model instance
            action: Action to check
            
        Returns:
            Boolean
        """
        # Check basic permission first
        resource = record.__class__.__name__.lower()
        if not PermissionEvaluator.has_permission(user, organization, resource, action):
            return False
        
        # Check ownership if record has owner field
        if hasattr(record, 'owner'):
            role = PermissionEvaluator.get_user_role(user, organization)
            if role:
                # Get permission conditions
                permission = RolePermission.objects.for_organization(organization).filter(
                    role=role,
                    resource=resource,
                    action=action,
                    is_granted=True
                ).first()
                
                if permission and permission.conditions.get('own_records_only'):
                    return record.owner == user
        
        return True
