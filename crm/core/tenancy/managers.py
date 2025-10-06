# crm/core/tenancy/managers.py
"""
Custom managers and querysets for tenant-scoped data
"""
from django.db import models


class TenantQuerySet(models.QuerySet):
    """
    Custom QuerySet that enforces organization scoping
    """
    
    def for_organization(self, organization):
        """
        Filter queryset to a specific organization
        """
        if organization:
            return self.filter(organization=organization)
        return self.none()
    
    def for_user_organizations(self, user):
        """
        Filter queryset to organizations accessible by user
        """
        if not user or not user.is_authenticated:
            return self.none()
        
        from core.models import UserCompanyAccess
        org_ids = UserCompanyAccess.objects.filter(
            user=user,
            is_active=True
        ).values_list('company_id', flat=True)
        
        return self.filter(organization_id__in=org_ids)
    
    def created_by_user(self, user):
        """
        Filter to records created by specific user
        """
        return self.filter(created_by=user)
    
    def updated_recently(self, days=7):
        """
        Filter to records updated in the last N days
        """
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(updated_at__gte=cutoff)


class TenantManager(models.Manager):
    """
    Custom Manager that returns TenantQuerySet
    """
    
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)
    
    def for_organization(self, organization):
        return self.get_queryset().for_organization(organization)
    
    def for_user_organizations(self, user):
        return self.get_queryset().for_user_organizations(user)
    
    def created_by_user(self, user):
        return self.get_queryset().created_by_user(user)
    
    def updated_recently(self, days=7):
        return self.get_queryset().updated_recently(days)
