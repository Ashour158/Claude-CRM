"""
Tenancy Model Mixins

This module provides abstract base models for tenant-owned entities in a
row-level multi-tenancy architecture.

Usage:
    class MyModel(TenantOwnedModel):
        name = models.CharField(max_length=255)
        # organization field is automatically added
"""

import uuid
try:
    from django.db import models
    DJANGO_AVAILABLE = True
except ImportError:
    # Allow import without Django for testing/documentation
    DJANGO_AVAILABLE = False
    models = None
from typing import Optional

from .context import get_current_organization_id


if DJANGO_AVAILABLE:
    ModelBase = models.Model
else:
    # Placeholder for non-Django environments
    class ModelBase:
        class Meta:
            abstract = True


class TenantOwnedModel(ModelBase):
    """
    Abstract base model for tenant-owned entities (row-level tenancy).
    
    This model adds an organization foreign key and provides automatic filtering
    based on the current tenant context. Use this for any model that should be
    isolated by organization/company.
    
    Note: This is scaffolding. The actual Company/Organization model reference
    should be updated once models are migrated.
    
    Fields:
        organization: Foreign key to the owning organization
    
    Methods:
        get_queryset_for_organization: Class method to get filtered queryset
    """
    
    # Placeholder - will be updated to reference actual Company model
    # organization = models.ForeignKey(
    #     'core.Company',
    #     on_delete=models.CASCADE,
    #     related_name='%(app_label)s_%(class)s_set',
    #     db_index=True,
    #     help_text="Organization that owns this record"
    # )
    
    class Meta:
        abstract = True
        # Ensure organization is indexed for query performance
        # indexes = [
        #     models.Index(fields=['organization']),
        # ]
    
    @classmethod
    def get_queryset_for_organization(cls, organization_id: uuid.UUID):
        """
        Get a queryset filtered by organization.
        
        Args:
            organization_id: The organization UUID to filter by
            
        Returns:
            QuerySet: Filtered queryset for the organization
        """
        # This will be implemented once the organization field is added
        # return cls.objects.filter(organization_id=organization_id)
        return cls.objects.all()  # Placeholder
    
    @classmethod
    def get_queryset_for_current_organization(cls):
        """
        Get a queryset filtered by the current organization from context.
        
        Returns:
            QuerySet: Filtered queryset for current organization, or all if no context
        """
        org_id = get_current_organization_id()
        if org_id:
            return cls.get_queryset_for_organization(org_id)
        return cls.objects.all()
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically set organization from context if not set.
        """
        # Future implementation:
        # if not self.organization_id:
        #     org_id = get_current_organization_id()
        #     if org_id:
        #         self.organization_id = org_id
        super().save(*args, **kwargs)
