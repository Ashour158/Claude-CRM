# crm/custom_fields/models/custom_field.py
# Custom field definition and management

from django.db import models
from django.core.exceptions import ValidationError
from core.tenant_models import TenantOwnedModel


class CustomFieldDefinition(TenantOwnedModel):
    """
    Defines custom fields that can be added to entities (Account, Contact, Lead, etc.)
    Phase 1: JSON-based storage approach where values are stored in custom_data field.
    """
    
    FIELD_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
        ('boolean', 'Yes/No'),
        ('select', 'Dropdown'),
        ('multi_select', 'Multi-Select'),
        ('url', 'URL'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('textarea', 'Text Area'),
    ]
    
    ENTITY_TYPE_CHOICES = [
        ('account', 'Account'),
        ('contact', 'Contact'),
        ('lead', 'Lead'),
        ('deal', 'Deal'),
        ('opportunity', 'Opportunity'),
    ]
    
    # Field identification
    name = models.CharField(
        max_length=100,
        help_text="Display name of the custom field"
    )
    code = models.CharField(
        max_length=100,
        help_text="Internal code/key for the field (e.g., 'preferred_color')"
    )
    
    # Field configuration
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        help_text="Data type of the field"
    )
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPE_CHOICES,
        db_index=True,
        help_text="Which entity this field applies to"
    )
    
    # Validation
    is_required = models.BooleanField(
        default=False,
        help_text="Whether this field must have a value"
    )
    
    # For select/multi_select types
    choices = models.JSONField(
        default=list,
        blank=True,
        help_text="List of choices for select fields, e.g., ['Option 1', 'Option 2']"
    )
    
    # Additional configuration
    default_value = models.TextField(
        blank=True,
        help_text="Default value for this field"
    )
    help_text = models.TextField(
        blank=True,
        help_text="Help text shown to users"
    )
    placeholder = models.CharField(
        max_length=255,
        blank=True,
        help_text="Placeholder text for input fields"
    )
    
    # Display configuration
    display_order = models.IntegerField(
        default=0,
        help_text="Order in which fields are displayed"
    )
    field_group = models.CharField(
        max_length=100,
        blank=True,
        help_text="Group/section this field belongs to"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this field is currently active"
    )
    
    class Meta:
        db_table = 'crm_custom_field_definition'
        verbose_name = 'Custom Field Definition'
        verbose_name_plural = 'Custom Field Definitions'
        ordering = ['entity_type', 'display_order', 'name']
        unique_together = [['organization', 'entity_type', 'code']]
        indexes = [
            models.Index(fields=['organization', 'entity_type', 'is_active']),
            models.Index(fields=['organization', 'code']),
        ]
    
    def __str__(self):
        return f"{self.entity_type}.{self.code} ({self.name})"
    
    def clean(self):
        """Validate the custom field definition"""
        super().clean()
        
        # Validate choices for select fields
        if self.field_type in ['select', 'multi_select']:
            if not self.choices or not isinstance(self.choices, list):
                raise ValidationError({
                    'choices': 'Select and multi-select fields must have a list of choices'
                })
            if len(self.choices) < 1:
                raise ValidationError({
                    'choices': 'Select and multi-select fields must have at least one choice'
                })
        
        # Validate code format (alphanumeric and underscores only)
        import re
        if not re.match(r'^[a-z0-9_]+$', self.code):
            raise ValidationError({
                'code': 'Code must contain only lowercase letters, numbers, and underscores'
            })
    
    def validate_value(self, value):
        """
        Validate a value against this field definition.
        
        Args:
            value: The value to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        # Required field check
        if self.is_required and (value is None or value == ''):
            raise ValidationError(f"{self.name} is required")
        
        # If not required and no value, it's valid
        if value is None or value == '':
            return True
        
        # Type-specific validation
        if self.field_type == 'number':
            try:
                float(value)
            except (ValueError, TypeError):
                raise ValidationError(f"{self.name} must be a number")
        
        elif self.field_type == 'boolean':
            if not isinstance(value, bool):
                raise ValidationError(f"{self.name} must be true or false")
        
        elif self.field_type == 'select':
            if value not in self.choices:
                raise ValidationError(f"{self.name} must be one of: {', '.join(self.choices)}")
        
        elif self.field_type == 'multi_select':
            if not isinstance(value, list):
                raise ValidationError(f"{self.name} must be a list")
            for v in value:
                if v not in self.choices:
                    raise ValidationError(f"Invalid choice in {self.name}: {v}")
        
        elif self.field_type == 'email':
            from django.core.validators import validate_email
            try:
                validate_email(value)
            except ValidationError:
                raise ValidationError(f"{self.name} must be a valid email address")
        
        elif self.field_type == 'url':
            from django.core.validators import URLValidator
            validator = URLValidator()
            try:
                validator(value)
            except ValidationError:
                raise ValidationError(f"{self.name} must be a valid URL")
        
        return True
