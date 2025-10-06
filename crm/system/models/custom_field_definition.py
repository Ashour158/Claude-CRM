# crm/system/models/custom_field_definition.py
"""
Custom field definition model
"""
from django.db import models
from crm.core.tenancy.mixins import TenantOwnedModel
from crm.core.tenancy.managers import TenantManager


class CustomFieldDefinition(TenantOwnedModel):
    """
    Defines custom fields that can be added to entities.
    Actual values are stored in JSON fields on the entity models.
    """
    
    FIELD_TYPE_CHOICES = [
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('number', 'Number'),
        ('decimal', 'Decimal'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('boolean', 'Boolean'),
        ('choice', 'Single Choice'),
        ('multichoice', 'Multiple Choice'),
        ('url', 'URL'),
        ('email', 'Email'),
    ]
    
    ENTITY_TYPE_CHOICES = [
        ('account', 'Account'),
        ('contact', 'Contact'),
        ('lead', 'Lead'),
        ('deal', 'Deal'),
    ]
    
    # Field identification
    name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Internal field name (used as key)"
    )
    label = models.CharField(
        max_length=255,
        help_text="Display label"
    )
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        default='text'
    )
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES,
        db_index=True,
        help_text="Which entity this field applies to"
    )
    
    # Field configuration
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    default_value = models.TextField(blank=True)
    help_text = models.TextField(blank=True)
    
    # For choice fields
    choices = models.JSONField(
        default=list,
        blank=True,
        help_text="List of choices for choice/multichoice fields"
    )
    
    # Validation rules (JSON)
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Validation rules (min, max, regex, etc.)"
    )
    
    # Display settings
    display_order = models.IntegerField(default=0, help_text="Display order")
    is_visible = models.BooleanField(default=True)
    is_editable = models.BooleanField(default=True)
    is_searchable = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Manager
    objects = TenantManager()
    
    class Meta:
        db_table = 'crm_custom_field_definition'
        ordering = ['entity_type', 'display_order', 'label']
        unique_together = [['organization', 'entity_type', 'name']]
        indexes = [
            models.Index(fields=['organization', 'entity_type', 'is_active']),
        ]
        verbose_name = 'Custom Field Definition'
        verbose_name_plural = 'Custom Field Definitions'
    
    def __str__(self):
        return f"{self.label} ({self.entity_type})"
