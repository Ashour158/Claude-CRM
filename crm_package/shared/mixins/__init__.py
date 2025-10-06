"""
Shared model and view mixins.
"""

try:
    from django.db import models
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    # Placeholder for non-Django environments
    class models:
        class Model:
            class Meta:
                abstract = True


if DJANGO_AVAILABLE:
    class TimestampMixin(models.Model):
        """
        Mixin to add created_at and updated_at timestamp fields.
        """
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        
        class Meta:
            abstract = True


    class SoftDeleteMixin(models.Model):
        """
        Mixin to add soft delete functionality.
        """
        is_deleted = models.BooleanField(default=False, db_index=True)
        deleted_at = models.DateTimeField(null=True, blank=True)
        
        class Meta:
            abstract = True
        
        def soft_delete(self):
            """Mark the object as deleted."""
            from django.utils import timezone
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()
else:
    # Placeholder classes for non-Django environments
    class TimestampMixin:
        """Placeholder when Django is not available."""
        pass
    
    class SoftDeleteMixin:
        """Placeholder when Django is not available."""
        pass
