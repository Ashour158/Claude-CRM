# core/models_saved_views.py
# Saved Views for persistent list filtering

from django.db import models
from django.core.exceptions import ValidationError
from core.models import CompanyIsolatedModel, User
import json


def validate_saved_view_definition(value):
    """
    Validate saved view definition structure.
    """
    if not isinstance(value, dict):
        raise ValidationError("Definition must be a dictionary")
    
    # Validate filters
    filters = value.get('filters', [])
    if not isinstance(filters, list):
        raise ValidationError("Filters must be a list")
    
    for filter_def in filters:
        if not isinstance(filter_def, dict):
            raise ValidationError("Each filter must be a dictionary")
        if 'field' not in filter_def or 'operator' not in filter_def:
            raise ValidationError("Each filter must have 'field' and 'operator'")
    
    # Validate columns
    columns = value.get('columns', [])
    if not isinstance(columns, list):
        raise ValidationError("Columns must be a list")
    
    # Validate sort
    sort = value.get('sort', [])
    if not isinstance(sort, list):
        raise ValidationError("Sort must be a list")
    
    for sort_def in sort:
        if not isinstance(sort_def, dict):
            raise ValidationError("Each sort must be a dictionary")
        if 'field' not in sort_def or 'direction' not in sort_def:
            raise ValidationError("Each sort must have 'field' and 'direction'")
        if sort_def['direction'] not in ['asc', 'desc']:
            raise ValidationError("Sort direction must be 'asc' or 'desc'")


class SavedListView(CompanyIsolatedModel):
    """
    Persistent saved views for list filtering and display.
    Supports filters, column selection, and sorting.
    """
    
    ENTITY_TYPE_CHOICES = [
        ('account', 'Account'),
        ('contact', 'Contact'),
        ('lead', 'Lead'),
        ('deal', 'Deal'),
        ('activity', 'Activity'),
        ('task', 'Task'),
        ('quote', 'Quote'),
        ('order', 'Order'),
        ('invoice', 'Invoice'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPE_CHOICES,
        db_index=True
    )
    
    # View Definition (JSON)
    definition = models.JSONField(
        validators=[validate_saved_view_definition],
        help_text="View definition with filters, columns, and sorting"
    )
    
    # Ownership
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_views',
        null=True,
        blank=True,
        help_text="Owner if private view, null if global"
    )
    is_private = models.BooleanField(
        default=True,
        help_text="Private views only visible to owner, global views visible to all"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Default view for this entity type"
    )
    
    class Meta:
        db_table = 'saved_list_views'
        verbose_name = 'Saved List View'
        verbose_name_plural = 'Saved List Views'
        ordering = ['entity_type', 'name']
        indexes = [
            models.Index(fields=['company', 'entity_type', 'is_private']),
            models.Index(fields=['company', 'entity_type', 'owner']),
        ]
        # Unique constraint: organization + entity_type + name + (owner or null for global)
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'entity_type', 'name', 'owner'],
                condition=models.Q(owner__isnull=False),
                name='unique_private_view_name'
            ),
            models.UniqueConstraint(
                fields=['company', 'entity_type', 'name'],
                condition=models.Q(owner__isnull=True),
                name='unique_global_view_name'
            ),
        ]
    
    def __str__(self):
        scope = "Private" if self.is_private else "Global"
        return f"{self.name} ({self.entity_type}) - {scope}"
    
    def apply_filters(self, queryset):
        """
        Apply this view's filters to a queryset.
        """
        from django.db.models import Q
        
        filters = self.definition.get('filters', [])
        
        for filter_def in filters:
            field = filter_def.get('field')
            operator = filter_def.get('operator')
            value = filter_def.get('value')
            
            if not field or not operator:
                continue
            
            # Build Q object based on operator
            lookup = self._get_lookup_expression(field, operator)
            if lookup and value is not None:
                queryset = queryset.filter(**{lookup: value})
        
        return queryset
    
    def apply_sorting(self, queryset):
        """
        Apply this view's sorting to a queryset.
        """
        sort_fields = []
        sorts = self.definition.get('sort', [])
        
        for sort_def in sorts:
            field = sort_def.get('field')
            direction = sort_def.get('direction', 'asc')
            
            if field:
                sort_field = field if direction == 'asc' else f'-{field}'
                sort_fields.append(sort_field)
        
        if sort_fields:
            queryset = queryset.order_by(*sort_fields)
        
        return queryset
    
    def get_columns(self):
        """
        Get list of columns to display.
        """
        return self.definition.get('columns', [])
    
    def _get_lookup_expression(self, field, operator):
        """
        Convert operator to Django lookup expression.
        """
        operator_map = {
            'equals': field,
            'not_equals': field,  # Handle with exclude
            'contains': f'{field}__icontains',
            'not_contains': f'{field}__icontains',  # Handle with exclude
            'starts_with': f'{field}__istartswith',
            'ends_with': f'{field}__iendswith',
            'gt': f'{field}__gt',
            'gte': f'{field}__gte',
            'lt': f'{field}__lt',
            'lte': f'{field}__lte',
            'in': f'{field}__in',
            'not_in': f'{field}__in',  # Handle with exclude
            'is_null': f'{field}__isnull',
            'is_not_null': f'{field}__isnull',  # Handle with exclude
        }
        
        return operator_map.get(operator)
