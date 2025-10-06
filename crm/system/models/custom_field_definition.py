# crm/system/models/custom_field_definition.py
# Custom field definition model

from django.db import models
from crm.tenancy import TenantOwnedModel
from core.models import User


class CustomFieldDefinition(TenantOwnedModel):
    """
    Defines custom fields that can be added to tenant entities.
    Values are stored in the entity's custom_data JSONField.
    """
    
    FIELD_TYPE_CHOICES = [
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('number', 'Number'),
        ('decimal', 'Decimal'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('boolean', 'Boolean'),
        ('choice', 'Choice'),
        ('multichoice', 'Multi Choice'),
        ('url', 'URL'),
        ('email', 'Email'),
        ('phone', 'Phone'),
    ]
    
    ENTITY_TYPE_CHOICES = [
        ('account', 'Account'),
        ('contact', 'Contact'),
        ('lead', 'Lead'),
        ('deal', 'Deal'),
        ('product', 'Product'),
    ]
    
    # Basic Information
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPE_CHOICES,
        db_index=True,
        help_text="Type of entity this field applies to"
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Display name of the field"
    )
    
    code = models.CharField(
        max_length=100,
        help_text="Internal code/key for the field (used in custom_data JSON)"
    )
    
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        default='text'
    )
    
    # Configuration
    is_required = models.BooleanField(
        default=False,
        help_text="Whether this field is required"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this field is currently active"
    )
    
    # For choice fields
    choices = models.JSONField(
        null=True,
        blank=True,
        help_text="List of choices for choice/multichoice fields"
    )
    
    # Display settings
    ordering = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    group_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Group name for organizing fields in UI"
    )
    
    help_text = models.TextField(
        blank=True,
        help_text="Help text displayed to users"
    )
    
    # Validation
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON object with validation rules (min, max, pattern, etc.)"
    )
    
    # Default value
    default_value = models.TextField(
        blank=True,
        help_text="Default value for the field"
    )
    
    class Meta:
        db_table = 'crm_custom_field_definitions'
        verbose_name = 'Custom Field Definition'
        verbose_name_plural = 'Custom Field Definitions'
        ordering = ['entity_type', 'ordering', 'name']
        indexes = [
            models.Index(fields=['organization', 'entity_type', 'is_active']),
            models.Index(fields=['organization', 'entity_type', 'code']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'entity_type', 'code'],
                name='unique_field_code_per_entity'
            )
        ]
    
    def __str__(self):
        return f"{self.name} ({self.entity_type})"
    
    def validate_value(self, value):
        """
        Validate a value against this field's rules.
        
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        # Required check
        if self.is_required and (value is None or value == ''):
            return False, f"{self.name} is required"
        
        # Skip validation if value is empty and not required
        if value is None or value == '':
            return True, None
        
        # Type-specific validation
        if self.field_type == 'number':
            try:
                int_value = int(value)
                rules = self.validation_rules or {}
                if 'min' in rules and int_value < rules['min']:
                    return False, f"{self.name} must be at least {rules['min']}"
                if 'max' in rules and int_value > rules['max']:
                    return False, f"{self.name} must be at most {rules['max']}"
            except (ValueError, TypeError):
                return False, f"{self.name} must be a valid number"
        
        elif self.field_type == 'decimal':
            try:
                float(value)
            except (ValueError, TypeError):
                return False, f"{self.name} must be a valid decimal number"
        
        elif self.field_type == 'email':
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(value)
            except ValidationError:
                return False, f"{self.name} must be a valid email address"
        
        elif self.field_type in ['choice', 'multichoice']:
            if not self.choices:
                return True, None
            
            if self.field_type == 'choice':
                if value not in self.choices:
                    return False, f"{self.name} must be one of: {', '.join(self.choices)}"
            else:
                # multichoice - value should be a list
                if not isinstance(value, list):
                    return False, f"{self.name} must be a list of choices"
                invalid = [v for v in value if v not in self.choices]
                if invalid:
                    return False, f"Invalid choices for {self.name}: {', '.join(invalid)}"
        
        return True, None
