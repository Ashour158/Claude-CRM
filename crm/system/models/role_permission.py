# crm/system/models/role_permission.py
"""
Role permission model for granular access control
"""
from django.db import models
from crm.core.tenancy.mixins import TenantOwnedModel
from crm.core.tenancy.managers import TenantManager


class RolePermission(TenantOwnedModel):
    """
    RolePermission defines what actions a role can perform on what resources.
    """
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('import', 'Import'),
    ]
    
    RESOURCE_CHOICES = [
        ('account', 'Account'),
        ('contact', 'Contact'),
        ('lead', 'Lead'),
        ('deal', 'Deal'),
        ('activity', 'Activity'),
        ('report', 'Report'),
        ('settings', 'Settings'),
        ('user', 'User'),
    ]
    
    # Permission details
    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        related_name='permissions',
        help_text="Role this permission belongs to"
    )
    resource = models.CharField(
        max_length=50,
        choices=RESOURCE_CHOICES,
        db_index=True,
        help_text="Resource type"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Action that can be performed"
    )
    
    # Scope
    is_granted = models.BooleanField(
        default=True,
        help_text="Whether permission is granted or denied"
    )
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional conditions (e.g., own records only)"
    )
    
    # Manager
    objects = TenantManager()
    
    class Meta:
        db_table = 'crm_role_permission'
        ordering = ['role', 'resource', 'action']
        unique_together = [['organization', 'role', 'resource', 'action']]
        indexes = [
            models.Index(fields=['organization', 'role']),
            models.Index(fields=['resource', 'action']),
        ]
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
    
    def __str__(self):
        grant = "granted" if self.is_granted else "denied"
        return f"{self.role.name}: {self.action} {self.resource} ({grant})"
