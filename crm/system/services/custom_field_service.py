# crm/system/services/custom_field_service.py
# Custom field service for validation and assignment

from typing import Dict, List, Any, Tuple
from crm.system.models import CustomFieldDefinition


def validate_and_assign(
    entity: Any,
    data: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate custom field data and assign to entity.
    
    Args:
        entity: Entity instance (Account, Contact, Lead, etc.)
        data: Dictionary of custom field code -> value
        
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []
    
    # Get entity type from model name
    entity_type = entity.__class__.__name__.lower()
    
    # Get all custom field definitions for this entity type and organization
    field_defs = CustomFieldDefinition.objects.filter(
        organization=entity.organization,
        entity_type=entity_type,
        is_active=True
    )
    
    # Build a map of code -> definition
    field_map = {field.code: field for field in field_defs}
    
    # Check required fields
    for field_def in field_defs:
        if field_def.is_required:
            if field_def.code not in data or data[field_def.code] in [None, '']:
                errors.append(f"{field_def.name} is required")
    
    # Validate provided values
    for code, value in data.items():
        if code not in field_map:
            errors.append(f"Unknown custom field: {code}")
            continue
        
        field_def = field_map[code]
        is_valid, error_msg = field_def.validate_value(value)
        if not is_valid:
            errors.append(error_msg)
    
    # If validation passed, assign to entity
    if not errors:
        if entity.custom_data is None:
            entity.custom_data = {}
        
        entity.custom_data.update(data)
        # Note: Caller should save the entity
    
    return len(errors) == 0, errors


def resolve_display(entity: Any) -> Dict[str, Any]:
    """
    Resolve custom field values for display with field metadata.
    
    Args:
        entity: Entity instance with custom_data
        
    Returns:
        Dictionary mapping field code to display data (name, value, type, etc.)
    """
    if not entity.custom_data:
        return {}
    
    # Get entity type
    entity_type = entity.__class__.__name__.lower()
    
    # Get all custom field definitions
    field_defs = CustomFieldDefinition.objects.filter(
        organization=entity.organization,
        entity_type=entity_type,
        is_active=True
    ).order_by('ordering')
    
    result = {}
    for field_def in field_defs:
        value = entity.custom_data.get(field_def.code)
        
        # Format value for display
        display_value = value
        if field_def.field_type == 'choice' and field_def.choices:
            # Return choice as-is (could map to label if choices were objects)
            display_value = value
        elif field_def.field_type == 'boolean':
            display_value = bool(value) if value is not None else None
        
        result[field_def.code] = {
            'name': field_def.name,
            'value': value,
            'display_value': display_value,
            'field_type': field_def.field_type,
            'group': field_def.group_name,
            'help_text': field_def.help_text,
        }
    
    return result


def get_custom_fields_for_entity_type(
    organization_id: int,
    entity_type: str
) -> List[CustomFieldDefinition]:
    """
    Get all active custom field definitions for an entity type.
    
    Args:
        organization_id: The organization ID
        entity_type: Type of entity ('account', 'contact', 'lead', etc.)
        
    Returns:
        List of CustomFieldDefinition instances
    """
    return list(
        CustomFieldDefinition.objects.filter(
            organization_id=organization_id,
            entity_type=entity_type,
            is_active=True
        ).order_by('ordering', 'name')
    )
