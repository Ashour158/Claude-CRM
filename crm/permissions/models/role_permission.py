# crm/permissions/models/role_permission.py
# Role permission model

from django.db import models
from crm.tenancy import TenantOwnedModel
from .role import Role


class RolePermission(TenantOwnedModel):
    """
    Maps roles to specific permissions on object types.
    """
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    
    object_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Type of object (account, contact, lead, etc.)"
    )
    
    action = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Action allowed (view, edit, delete, etc.)"
    )
    
    # Optional: field-level restrictions (for future use)
    field_restrictions = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON object defining field-level restrictions"
    )
    
    class Meta:
        db_table = 'crm_role_permissions'
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
        ordering = ['role', 'object_type', 'action']
        indexes = [
            models.Index(fields=['organization', 'role', 'object_type']),
            models.Index(fields=['organization', 'object_type', 'action']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'role', 'object_type', 'action'],
                name='unique_role_permission'
            )
        ]
    
    def __str__(self):
        return f"{self.role.name} - {self.object_type}.{self.action}"
