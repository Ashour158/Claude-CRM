# crm/system/models/role.py
"""
Role model for permissions
"""
from django.db import models
from crm.core.tenancy.mixins import TenantOwnedModel
from crm.core.tenancy.managers import TenantManager


class Role(TenantOwnedModel):
    """
    Role defines a set of permissions for users within an organization.
    """
    
    # Role identification
    name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Role name"
    )
    code = models.CharField(
        max_length=50,
        help_text="Unique role code"
    )
    description = models.TextField(blank=True)
    
    # Hierarchy
    parent_role = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_roles',
        help_text="Parent role for inheritance"
    )
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_system_role = models.BooleanField(
        default=False,
        help_text="System roles cannot be deleted"
    )
    
    # Manager
    objects = TenantManager()
    
    class Meta:
        db_table = 'crm_role'
        ordering = ['name']
        unique_together = [['organization', 'code']]
        indexes = [
            models.Index(fields=['organization', 'is_active']),
        ]
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.name
