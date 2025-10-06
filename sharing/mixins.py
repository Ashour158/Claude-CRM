# sharing/mixins.py
# DRF mixins for sharing enforcement

from rest_framework import viewsets
from .enforcement import SharingEnforcer
from .metrics import increment_sharing_filter_metric


class SharingEnforcedViewMixin:
    """
    Mixin for DRF ViewSets to enforce sharing rules on querysets.
    
    Usage:
        class MyViewSet(SharingEnforcedViewMixin, viewsets.ModelViewSet):
            sharing_object_type = 'lead'  # Required
            sharing_ownership_field = 'owner'  # Optional, default is 'owner'
    """
    
    sharing_object_type = None  # Must be set in subclass
    sharing_ownership_field = 'owner'  # Can be overridden
    
    def get_queryset(self):
        """
        Override get_queryset to apply sharing enforcement.
        """
        # Get base queryset (from parent or default)
        if hasattr(super(), 'get_queryset'):
            queryset = super().get_queryset()
        else:
            queryset = self.queryset
        
        # Validate configuration
        if not self.sharing_object_type:
            raise ValueError(
                f"{self.__class__.__name__} must define 'sharing_object_type' attribute"
            )
        
        # Get user and company from request
        if not hasattr(self.request, 'user') or not self.request.user.is_authenticated:
            return queryset.none()
        
        user = self.request.user
        
        # Get company from request (set by middleware)
        if not hasattr(self.request, 'active_company'):
            return queryset.none()
        
        company = self.request.active_company
        
        # Increment metrics (optional)
        increment_sharing_filter_metric(self.sharing_object_type)
        
        # Apply sharing enforcement
        return SharingEnforcer.enforce_sharing(
            queryset=queryset,
            user=user,
            company=company,
            object_type=self.sharing_object_type,
            ownership_field=self.sharing_ownership_field
        )
