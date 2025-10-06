# crm/core/tenancy/mixins.py
"""
Tenancy mixins for multi-tenant data isolation
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TenantOwnedModel(models.Model):
    """
    Abstract base model for tenant-owned data.
    Provides organization FK, audit fields, and timestamps.
    """
    organization = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
        db_index=True,
        help_text="Organization that owns this record"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created',
        help_text="User who created this record"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_updated',
        help_text="User who last updated this record"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['organization', 'created_at']),
        ]
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically set created_by and updated_by
        if request context is available
        """
        user = kwargs.pop('user', None)
        if user and user.is_authenticated:
            if not self.pk:  # New object
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)
