"""
Custom validators for CRM data.
"""

try:
    from django.core.exceptions import ValidationError
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    # Placeholder for non-Django environments
    class ValidationError(Exception):
        pass

import re


def validate_phone_number(value):
    """
    Validate phone number format.
    
    Args:
        value: Phone number string
        
    Raises:
        ValidationError: If phone number format is invalid
    """
    if not value:
        return
    
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', value)
    
    # Check if it contains only digits and optional +
    if not re.match(r'^\+?\d{10,15}$', cleaned):
        raise ValidationError(
            'Phone number must be 10-15 digits, optionally starting with +'
        )


def validate_email_domain(value):
    """
    Validate that email is from an allowed domain.
    
    Args:
        value: Email address
        
    Raises:
        ValidationError: If email domain is not allowed
    """
    # Placeholder - can be extended with domain blacklist/whitelist
    if not value:
        return
    
    if '@' not in value:
        raise ValidationError('Invalid email format')
