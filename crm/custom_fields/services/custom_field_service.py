# crm/custom_fields/services/custom_field_service.py
# Service layer for managing custom field values

from django.core.exceptions import ValidationError
from crm.custom_fields.models import CustomFieldDefinition


class CustomFieldService:
    """
    Service for reading, validating, and writing custom field values.
    Phase 1: Works with JSON-based custom_data field on entities.
    """
    
    @staticmethod
    def get_field_definitions(organization, entity_type, active_only=True):
        """
        Get all custom field definitions for an entity type.
        
        Args:
            organization: Organization instance
            entity_type: Type of entity ('account', 'contact', 'lead', etc.)
            active_only: If True, only return active fields
            
        Returns:
            QuerySet of CustomFieldDefinition
        """
        queryset = CustomFieldDefinition.objects.filter(
            organization=organization,
            entity_type=entity_type
        )
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('display_order', 'name')
    
    @staticmethod
    def get_custom_data(entity, include_definitions=False):
        """
        Get custom field data from an entity.
        
        Args:
            entity: The entity instance (Account, Contact, Lead, etc.)
            include_definitions: If True, include field definitions
            
        Returns:
            dict: Custom field values, optionally with definitions
        """
        custom_data = entity.custom_data if hasattr(entity, 'custom_data') else {}
        
        if not include_definitions:
            return custom_data
        
        # Get field definitions
        entity_type = entity.__class__.__name__.lower()
        definitions = CustomFieldService.get_field_definitions(
            entity.organization,
            entity_type
        )
        
        # Build result with definitions
        result = {}
        for definition in definitions:
            result[definition.code] = {
                'definition': {
                    'name': definition.name,
                    'field_type': definition.field_type,
                    'is_required': definition.is_required,
                    'choices': definition.choices if definition.field_type in ['select', 'multi_select'] else None,
                    'help_text': definition.help_text,
                },
                'value': custom_data.get(definition.code)
            }
        
        return result
    
    @staticmethod
    def set_custom_field(entity, field_code, value, validate=True):
        """
        Set a custom field value on an entity.
        
        Args:
            entity: The entity instance
            field_code: The custom field code
            value: The value to set
            validate: If True, validate the value
            
        Raises:
            ValidationError: If validation fails
        """
        entity_type = entity.__class__.__name__.lower()
        
        if validate:
            # Get field definition
            try:
                definition = CustomFieldDefinition.objects.get(
                    organization=entity.organization,
                    entity_type=entity_type,
                    code=field_code,
                    is_active=True
                )
                definition.validate_value(value)
            except CustomFieldDefinition.DoesNotExist:
                raise ValidationError(f"Custom field '{field_code}' does not exist for {entity_type}")
        
        # Ensure custom_data is initialized
        if not hasattr(entity, 'custom_data') or entity.custom_data is None:
            entity.custom_data = {}
        
        # Set the value
        entity.custom_data[field_code] = value
    
    @staticmethod
    def set_custom_fields(entity, field_values, validate=True, save=False):
        """
        Set multiple custom field values on an entity.
        
        Args:
            entity: The entity instance
            field_values: Dict of {field_code: value}
            validate: If True, validate all values
            save: If True, save the entity after setting values
            
        Raises:
            ValidationError: If validation fails for any field
        """
        errors = {}
        
        for field_code, value in field_values.items():
            try:
                CustomFieldService.set_custom_field(entity, field_code, value, validate=validate)
            except ValidationError as e:
                errors[field_code] = str(e)
        
        if errors:
            raise ValidationError(errors)
        
        if save:
            entity.save(update_fields=['custom_data', 'updated_at'])
    
    @staticmethod
    def get_custom_field(entity, field_code, default=None):
        """
        Get a custom field value from an entity.
        
        Args:
            entity: The entity instance
            field_code: The custom field code
            default: Default value if field is not set
            
        Returns:
            The field value or default
        """
        if not hasattr(entity, 'custom_data') or entity.custom_data is None:
            return default
        
        return entity.custom_data.get(field_code, default)
    
    @staticmethod
    def validate_all_custom_fields(entity):
        """
        Validate all custom field values on an entity.
        
        Args:
            entity: The entity instance
            
        Raises:
            ValidationError: If any validation fails
        """
        if not hasattr(entity, 'custom_data') or not entity.custom_data:
            # Check for required fields
            entity_type = entity.__class__.__name__.lower()
            required_fields = CustomFieldDefinition.objects.filter(
                organization=entity.organization,
                entity_type=entity_type,
                is_required=True,
                is_active=True
            )
            
            if required_fields.exists():
                errors = {}
                for field in required_fields:
                    errors[field.code] = f"{field.name} is required"
                raise ValidationError(errors)
            
            return
        
        entity_type = entity.__class__.__name__.lower()
        definitions = CustomFieldService.get_field_definitions(
            entity.organization,
            entity_type
        )
        
        errors = {}
        for definition in definitions:
            value = entity.custom_data.get(definition.code)
            try:
                definition.validate_value(value)
            except ValidationError as e:
                errors[definition.code] = str(e)
        
        if errors:
            raise ValidationError(errors)
