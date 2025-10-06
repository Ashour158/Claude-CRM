# crm/leads/services/__init__.py
from .lead_conversion_service import (
    LeadConversionService,
    LeadConversionResult,
    AlreadyConvertedError
)

__all__ = [
    'LeadConversionService',
    'LeadConversionResult',
    'AlreadyConvertedError'
]
