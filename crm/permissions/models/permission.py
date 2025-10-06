# crm/permissions/models/permission.py
# Permission matrix for role-based access control

from django.db import models
from core.tenant_models import TenantOwnedModel


class Role(TenantOwnedModel):
    """
    Role definition for RBAC system.
    Roles are organization-specific and define sets of permissions.
    """
    
    ROLE_TYPE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('sales_rep', 'Sales Representative'),
        ('viewer', 'Viewer'),
        ('custom', 'Custom Role'),
    ]
    
    name = models.CharField(
        max_length=100,
        help_text="Role name (e.g., 'Sales Manager')"
    )
    role_type = models.CharField(
        max_length=50,
        choices=ROLE_TYPE_CHOICES,
        default='custom',
        db_index=True
    )
    description = models.TextField(blank=True)
    
    # Permissions are managed through RolePermission model
    
    is_active = models.BooleanField(default=True, db_index=True)
    is_system_role = models.BooleanField(
        default=False,
        help_text="System roles cannot be deleted"
    )
    
    class Meta:
        db_table = 'crm_role'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        unique_together = [['organization', 'name']]
        ordering = ['name']
    
    def __str__(self):
        return self.name


class RolePermission(TenantOwnedModel):
    """
    Maps permissions to roles for specific object types.
    Defines what actions a role can perform on which object types.
    """
    
    # Object types that can have permissions
    OBJECT_TYPE_CHOICES = [
        ('account', 'Account'),
        ('contact', 'Contact'),
        ('lead', 'Lead'),
        ('deal', 'Deal'),
        ('opportunity', 'Opportunity'),
        ('custom_field_definition', 'Custom Field Definition'),
        ('activity', 'Activity'),
        ('report', 'Report'),
        ('dashboard', 'Dashboard'),
    ]
    
    # Permission actions
    PERMISSION_CHOICES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('convert', 'Convert (Lead)'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('manage_custom_fields', 'Manage Custom Fields'),
        ('assign', 'Assign to Others'),
        ('share', 'Share'),
    ]
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    
    object_type = models.CharField(
        max_length=50,
        choices=OBJECT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of object this permission applies to"
    )
    
    permission_code = models.CharField(
        max_length=50,
        choices=PERMISSION_CHOICES,
        db_index=True,
        help_text="Permission action"
    )
    
    # Optional: restrict to own records vs all records
    scope = models.CharField(
        max_length=20,
        choices=[
            ('own', 'Own Records Only'),
            ('team', 'Team Records'),
            ('territory', 'Territory Records'),
            ('all', 'All Records'),
        ],
        default='own',
        help_text="Scope of the permission"
    )
    
    is_granted = models.BooleanField(
        default=True,
        help_text="Whether this permission is granted (True) or denied (False)"
    )
    
    class Meta:
        db_table = 'crm_role_permission'
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
        unique_together = [['role', 'object_type', 'permission_code']]
        indexes = [
            models.Index(fields=['organization', 'role', 'object_type']),
            models.Index(fields=['organization', 'object_type', 'permission_code']),
        ]
    
    def __str__(self):
        grant_str = "Allow" if self.is_granted else "Deny"
        return f"{self.role.name}: {grant_str} {self.permission_code} on {self.object_type} ({self.scope})"


class PermissionMatrix:
    """
    Static class for checking permissions.
    This is a stub implementation for Phase 2.
    Full enforcement will be implemented in a later phase.
    """
    
    PERMISSIONS = {
        'VIEW': 'view',
        'CREATE': 'create',
        'EDIT': 'edit',
        'DELETE': 'delete',
        'CONVERT': 'convert',
        'EXPORT': 'export',
        'IMPORT': 'import',
        'MANAGE_CUSTOM_FIELDS': 'manage_custom_fields',
        'ASSIGN': 'assign',
        'SHARE': 'share',
    }
    
    @staticmethod
    def get_user_permissions(user, object_type, organization=None):
        """
        Get all permissions a user has for an object type.
        
        Args:
            user: User instance
            object_type: Type of object (e.g., 'account', 'lead')
            organization: Organization context
            
        Returns:
            list: List of permission codes the user has
        """
        # Stub implementation - returns all permissions for now
        # TODO: Implement actual permission checking based on user's roles
        return list(PermissionMatrix.PERMISSIONS.values())
    
    @staticmethod
    def has_permission(user, object_type, permission_code, obj=None, organization=None):
        """
        Check if a user has a specific permission.
        
        Args:
            user: User instance
            object_type: Type of object
            permission_code: Permission to check
            obj: Optional specific object instance
            organization: Organization context
            
        Returns:
            bool: True if user has permission
        """
        # Stub implementation - returns True for now
        # TODO: Implement actual permission checking
        if user and user.is_superuser:
            return True
        
        # For now, return True for all authenticated users
        return user and user.is_authenticated
    
    @staticmethod
    def get_allowed_actions(user, object_type, obj=None, organization=None):
        """
        Get all allowed actions for a user on an object type.
        
        Args:
            user: User instance
            object_type: Type of object
            obj: Optional specific object instance
            organization: Organization context
            
        Returns:
            list: List of allowed action codes
        """
        permissions = PermissionMatrix.get_user_permissions(user, object_type, organization)
        return permissions
