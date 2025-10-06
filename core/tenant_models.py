# core/tenant_models.py
# Enhanced tenant-aware base models with row-level scoping

from django.db import models
from django.contrib.auth import get_user_model
from contextvars import ContextVar
import uuid

# Context variable to store current organization/company
current_organization = ContextVar('current_organization', default=None)

User = get_user_model()


class TenantQuerySet(models.QuerySet):
    """
    QuerySet that automatically filters by organization context.
    Provides transparent multi-tenancy at the row level.
    """
    
    def filter_by_organization(self, organization=None):
        """Filter queryset by organization, using context if not provided"""
        if organization is None:
            organization = current_organization.get()
        
        if organization is None:
            # If no organization context, return empty queryset for safety
            return self.none()
        
        return self.filter(organization=organization)


class TenantManager(models.Manager):
    """
    Manager that uses TenantQuerySet and automatically applies
    organization filtering based on context.
    """
    
    def get_queryset(self):
        """Return queryset filtered by current organization context"""
        qs = TenantQuerySet(self.model, using=self._db)
        organization = current_organization.get()
        
        if organization is not None:
            return qs.filter(organization=organization)
        
        return qs
    
    def all_tenants(self):
        """Return all objects across all tenants (admin use only)"""
        return TenantQuerySet(self.model, using=self._db)


class TenantOwnedModel(models.Model):
    """
    Abstract base model for row-level multi-tenancy.
    All models inheriting from this will be automatically scoped to an organization.
    
    Provides:
    - organization field (FK to Company/Organization)
    - created_by, updated_by user tracking
    - created_at, updated_at timestamps
    - Automatic organization-based filtering via custom manager
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Multi-tenancy
    organization = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
        help_text="Organization this record belongs to"
    )
    
    # Audit fields
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
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use tenant-aware manager
    objects = TenantManager()
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['organization', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        """Ensure organization is set before saving"""
        if not self.organization_id:
            org = current_organization.get()
            if org:
                self.organization = org
            # If still no organization and this is not a new record being created 
            # with explicit org set, raise error
            elif not self.pk:
                raise ValueError(
                    f"Cannot save {self.__class__.__name__} without organization context. "
                    "Set organization explicitly or ensure organization context is set."
                )
        
        super().save(*args, **kwargs)


def set_current_organization(organization):
    """Set the current organization context"""
    current_organization.set(organization)


def get_current_organization():
    """Get the current organization context"""
    return current_organization.get()


def clear_current_organization():
    """Clear the current organization context"""
    current_organization.set(None)
