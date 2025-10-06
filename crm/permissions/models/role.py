# crm/permissions/models/role.py
# Role model for permission management

from django.db import models
from crm.tenancy import TenantOwnedModel


class Role(TenantOwnedModel):
    """
    Role model for grouping permissions.
    Each user can have a role that determines their permissions.
    """
    
    name = models.CharField(
        max_length=100,
        help_text="Role name (e.g., 'Admin', 'Sales Rep', 'Viewer')"
    )
    
    code = models.CharField(
        max_length=50,
        help_text="Internal code for the role (e.g., 'admin', 'sales_rep')"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Description of what this role can do"
    )
    
    is_system = models.BooleanField(
        default=False,
        help_text="Whether this is a system-defined role (cannot be deleted)"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True
    )
    
    class Meta:
        db_table = 'crm_roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'code'],
                name='unique_role_code_per_org'
            )
        ]
    
    def __str__(self):
        return self.name
