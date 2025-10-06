# crm/system/services/custom_field_service.py
"""
Custom field service for validation and management
"""
from crm.system.models import CustomFieldDefinition
import re
from decimal import Decimal
from datetime import datetime


class CustomFieldService:
    """Service for custom field operations"""
    
    @staticmethod
    def validate_and_assign(entity_type, custom_fields_data, organization):
        """
        Validate custom field values against definitions
        
        Args:
            entity_type: Type of entity (account, contact, lead, deal)
            custom_fields_data: Dict of field_name: value
            organization: Company instance
            
        Returns:
            Tuple (is_valid, validated_data, errors)
        """
        errors = {}
        validated_data = {}
        
        # Get all active custom field definitions for this entity type
        definitions = CustomFieldDefinition.objects.for_organization(organization).filter(
            entity_type=entity_type,
            is_active=True
        )
        
        definition_map = {d.name: d for d in definitions}
        
        # Check required fields
        for definition in definitions:
            if definition.is_required and definition.name not in custom_fields_data:
                errors[definition.name] = f"{definition.label} is required"
        
        # Validate each provided field
        for field_name, value in custom_fields_data.items():
            if field_name not in definition_map:
                # Unknown field - skip or warn
                continue
            
            definition = definition_map[field_name]
            is_valid, error = CustomFieldService._validate_field_value(definition, value)
            
            if not is_valid:
                errors[field_name] = error
            else:
                validated_data[field_name] = value
        
        return len(errors) == 0, validated_data, errors
    
    @staticmethod
    def _validate_field_value(definition, value):
        """
        Validate a single field value
        
        Args:
            definition: CustomFieldDefinition instance
            value: Value to validate
            
        Returns:
            Tuple (is_valid, error_message)
        """
        field_type = definition.field_type
        
        # Type-specific validation
        if field_type == 'number':
            try:
                int(value)
            except (ValueError, TypeError):
                return False, "Must be a valid number"
        
        elif field_type == 'decimal':
            try:
                Decimal(str(value))
            except:
                return False, "Must be a valid decimal"
        
        elif field_type == 'email':
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str(value)):
                return False, "Must be a valid email address"
        
        elif field_type == 'url':
            if not str(value).startswith(('http://', 'https://')):
                return False, "Must be a valid URL"
        
        elif field_type == 'choice':
            if definition.choices and value not in definition.choices:
                return False, f"Must be one of: {', '.join(definition.choices)}"
        
        elif field_type == 'multichoice':
            if not isinstance(value, list):
                return False, "Must be a list of choices"
            if definition.choices:
                for v in value:
                    if v not in definition.choices:
                        return False, f"Invalid choice: {v}"
        
        elif field_type == 'boolean':
            if not isinstance(value, bool):
                return False, "Must be true or false"
        
        # Validation rules
        rules = definition.validation_rules
        if rules:
            if 'min' in rules and value < rules['min']:
                return False, f"Must be at least {rules['min']}"
            if 'max' in rules and value > rules['max']:
                return False, f"Must be at most {rules['max']}"
            if 'regex' in rules and not re.match(rules['regex'], str(value)):
                return False, f"Does not match required pattern"
        
        return True, ""
    
    @staticmethod
    def resolve_display(entity_type, custom_fields_data, organization):
        """
        Resolve custom field values to display labels
        
        Args:
            entity_type: Type of entity
            custom_fields_data: Dict of field_name: value
            organization: Company instance
            
        Returns:
            Dict of field_label: display_value
        """
        definitions = CustomFieldDefinition.objects.for_organization(organization).filter(
            entity_type=entity_type,
            is_active=True
        )
        
        display_data = {}
        definition_map = {d.name: d for d in definitions}
        
        for field_name, value in custom_fields_data.items():
            if field_name in definition_map:
                definition = definition_map[field_name]
                display_data[definition.label] = value
        
        return display_data
