# crm/tenancy.py
# Multi-tenant context management and queryset filtering

from contextlib import contextmanager
from contextvars import ContextVar
from django.db import models
from django.core.exceptions import ValidationError

# Context variable to store the current organization
_current_org: ContextVar = ContextVar('current_org', default=None)


def set_current_org(organization):
    """Set the current organization for the request context"""
    _current_org.set(organization)


def get_current_org():
    """Get the current organization from the request context"""
    return _current_org.get()


def clear_current_org():
    """Clear the current organization context"""
    _current_org.set(None)


@contextmanager
def org_context(organization):
    """Context manager for setting organization temporarily"""
    token = _current_org.set(organization)
    try:
        yield organization
    finally:
        _current_org.reset(token)


class TenantQuerySet(models.QuerySet):
    """QuerySet that automatically filters by current organization"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_org_filter()
    
    def _apply_org_filter(self):
        """Apply organization filter if context is set"""
        org = get_current_org()
        if org and not self._has_org_filter():
            # Only apply filter if not already filtered by organization
            return self.filter(organization=org)
        return self
    
    def _has_org_filter(self):
        """Check if queryset already has organization filter"""
        # Check if organization is in the query's where clause
        if self.query.where:
            for child in self.query.where.children:
                if hasattr(child, 'lhs') and hasattr(child.lhs, 'target'):
                    if child.lhs.target.name == 'organization':
                        return True
        return False
    
    def all_orgs(self):
        """Return queryset without organization filtering (requires elevated permissions)"""
        # This should be used sparingly and only with proper permission checks
        return super().all()


class TenantManager(models.Manager):
    """Manager that uses TenantQuerySet"""
    
    def get_queryset(self):
        """Return TenantQuerySet instead of regular QuerySet"""
        qs = TenantQuerySet(self.model, using=self._db)
        org = get_current_org()
        if org:
            return qs.filter(organization=org)
        return qs
    
    def all_orgs(self):
        """Get all objects across all organizations (requires elevated permissions)"""
        return super().get_queryset()


class TenantOwnedModel(models.Model):
    """
    Abstract base model for tenant-owned data.
    Extends CompanyIsolatedModel with enhanced tenancy features.
    """
    
    organization = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        db_column='company_id',  # Keep backward compatibility
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = TenantManager()
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['organization', 'created_at']),
        ]
    
    def save(self, *args, **kwargs):
        """Override save to ensure organization is set and validate cross-org operations"""
        # Auto-set organization from context if not set
        if not self.organization_id:
            org = get_current_org()
            if org:
                self.organization = org
            elif not self.pk:  # Only raise for new objects
                raise ValidationError(
                    "Organization must be set either explicitly or via context"
                )
        
        # Validate that we're not accidentally changing organization
        if self.pk:
            org = get_current_org()
            if org and self.organization_id != org.id:
                raise ValidationError(
                    f"Cannot save object from organization {self.organization_id} "
                    f"while in context of organization {org.id}"
                )
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete to validate organization context"""
        org = get_current_org()
        if org and self.organization_id != org.id:
            raise ValidationError(
                f"Cannot delete object from organization {self.organization_id} "
                f"while in context of organization {org.id}"
            )
        return super().delete(*args, **kwargs)
