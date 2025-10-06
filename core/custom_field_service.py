# core/custom_field_service.py
# Custom field service with dual-write support for Phase 3

import logging
from typing import Dict, Any, Optional
from django.conf import settings
from django.db import transaction
from decimal import Decimal
from datetime import date, datetime

logger = logging.getLogger(__name__)


class CustomFieldService:
    """
    Service for managing custom field values with dual-write support.
    Writes to both JSON (existing) and relational (new) storage.
    """
    
    def __init__(self):
        self.dual_write_enabled = getattr(
            settings,
            'CUSTOM_FIELDS_DUAL_WRITE',
            False
        )
    
    def set_custom_field_value(
        self,
        entity,
        custom_field_id: str,
        custom_field_name: str,
        custom_field_type: str,
        value: Any,
        company
    ):
        """
        Set a custom field value using dual-write if enabled.
        
        Args:
            entity: The entity object (Deal, Account, etc.)
            custom_field_id: UUID of the CustomField
            custom_field_name: Name of the custom field
            custom_field_type: Type of the custom field (text, number, date, etc.)
            value: Value to set
            company: Company/organization
        """
        with transaction.atomic():
            # Write to JSON (existing behavior)
            self._write_to_json(entity, custom_field_name, value)
            
            # Write to relational if dual-write is enabled
            if self.dual_write_enabled:
                self._write_to_relational(
                    entity,
                    custom_field_id,
                    custom_field_name,
                    custom_field_type,
                    value,
                    company
                )
    
    def get_custom_field_value(
        self,
        entity,
        custom_field_name: str,
        prefer_relational: bool = False
    ) -> Any:
        """
        Get a custom field value.
        
        Args:
            entity: The entity object
            custom_field_name: Name of the custom field
            prefer_relational: If True and dual-write enabled, read from relational
        
        Returns:
            The custom field value
        """
        if prefer_relational and self.dual_write_enabled:
            return self._read_from_relational(entity, custom_field_name)
        return self._read_from_json(entity, custom_field_name)
    
    def _write_to_json(self, entity, field_name: str, value: Any):
        """Write custom field value to JSON field."""
        if not hasattr(entity, 'custom_fields'):
            return
        
        if entity.custom_fields is None:
            entity.custom_fields = {}
        
        entity.custom_fields[field_name] = value
        entity.save(update_fields=['custom_fields'])
    
    def _write_to_relational(
        self,
        entity,
        custom_field_id: str,
        custom_field_name: str,
        custom_field_type: str,
        value: Any,
        company
    ):
        """Write custom field value to relational table."""
        from core.models import CustomFieldValue
        
        entity_type = entity.__class__.__name__.lower()
        entity_id = entity.id
        
        # Get or create CustomFieldValue
        cfv, created = CustomFieldValue.objects.update_or_create(
            company=company,
            custom_field_id=custom_field_id,
            entity_type=entity_type,
            entity_id=entity_id,
            defaults={
                'custom_field_name': custom_field_name,
            }
        )
        
        # Set typed value based on field type
        self._set_typed_value(cfv, custom_field_type, value)
        cfv.save()
        
        logger.debug(
            f"Wrote custom field {custom_field_name} to relational storage "
            f"for {entity_type}:{entity_id}"
        )
    
    def _set_typed_value(self, cfv, field_type: str, value: Any):
        """Set the appropriate typed value column."""
        # Clear all typed values first
        cfv.value_text = None
        cfv.value_number = None
        cfv.value_date = None
        cfv.value_datetime = None
        cfv.value_boolean = None
        cfv.value_select = None
        
        if value is None:
            return
        
        # Set appropriate typed column
        if field_type in ['text', 'textarea', 'url', 'email', 'phone']:
            cfv.value_text = str(value)
        elif field_type in ['number', 'decimal']:
            cfv.value_number = Decimal(str(value))
        elif field_type == 'date':
            if isinstance(value, str):
                cfv.value_date = date.fromisoformat(value)
            elif isinstance(value, date):
                cfv.value_date = value
        elif field_type == 'datetime':
            if isinstance(value, str):
                cfv.value_datetime = datetime.fromisoformat(value)
            elif isinstance(value, datetime):
                cfv.value_datetime = value
        elif field_type == 'boolean':
            cfv.value_boolean = bool(value)
        elif field_type in ['choice', 'select']:
            cfv.value_select = str(value)
    
    def _read_from_json(self, entity, field_name: str) -> Any:
        """Read custom field value from JSON field."""
        if not hasattr(entity, 'custom_fields'):
            return None
        
        if entity.custom_fields is None:
            return None
        
        return entity.custom_fields.get(field_name)
    
    def _read_from_relational(self, entity, field_name: str) -> Any:
        """Read custom field value from relational table."""
        from core.models import CustomFieldValue
        
        entity_type = entity.__class__.__name__.lower()
        entity_id = entity.id
        
        try:
            cfv = CustomFieldValue.objects.get(
                entity_type=entity_type,
                entity_id=entity_id,
                custom_field_name=field_name
            )
            
            # Return the appropriate typed value
            if cfv.value_text is not None:
                return cfv.value_text
            elif cfv.value_number is not None:
                return cfv.value_number
            elif cfv.value_date is not None:
                return cfv.value_date
            elif cfv.value_datetime is not None:
                return cfv.value_datetime
            elif cfv.value_boolean is not None:
                return cfv.value_boolean
            elif cfv.value_select is not None:
                return cfv.value_select
            
        except CustomFieldValue.DoesNotExist:
            return None
        
        return None


# Global service instance
_custom_field_service = None


def get_custom_field_service() -> CustomFieldService:
    """Get or create the global custom field service instance."""
    global _custom_field_service
    if _custom_field_service is None:
        _custom_field_service = CustomFieldService()
    return _custom_field_service
