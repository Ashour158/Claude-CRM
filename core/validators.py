# core/validators.py
# Comprehensive validation utilities

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
import re


class PhoneValidator:
    """Validate phone numbers"""
    
    def __call__(self, value):
        if value:
            # Allow international format
            pattern = r'^\+?1?\d{9,15}$'
            if not re.match(pattern, value.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')):
                raise ValidationError(
                    'Invalid phone number format. Use international format.',
                    code='invalid_phone'
                )


class PasswordValidator:
    """Validate password strength"""
    
    def __init__(self, min_length=8, require_uppercase=True, require_lowercase=True, 
                 require_digit=True, require_special=True):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
    
    def __call__(self, value):
        if len(value) < self.min_length:
            raise ValidationError(
                f'Password must be at least {self.min_length} characters long.',
                code='password_too_short'
            )
        
        if self.require_uppercase and not re.search(r'[A-Z]', value):
            raise ValidationError(
                'Password must contain at least one uppercase letter.',
                code='password_no_upper'
            )
        
        if self.require_lowercase and not re.search(r'[a-z]', value):
            raise ValidationError(
                'Password must contain at least one lowercase letter.',
                code='password_no_lower'
            )
        
        if self.require_digit and not re.search(r'\d', value):
            raise ValidationError(
                'Password must contain at least one digit.',
                code='password_no_digit'
            )
        
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError(
                'Password must contain at least one special character.',
                code='password_no_special'
            )


class URLValidator:
    """Validate URL format"""
    
    def __call__(self, value):
        if value:
            pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
            if not re.match(pattern, value):
                raise ValidationError(
                    'Invalid URL format.',
                    code='invalid_url'
                )


class BusinessRulesValidator:
    """Validate business rules"""
    
    @staticmethod
    def validate_date_range(start_date, end_date):
        """Validate that end date is after start date"""
        if start_date and end_date and end_date < start_date:
            raise ValidationError(
                'End date must be after start date.',
                code='invalid_date_range'
            )
    
    @staticmethod
    def validate_amount(amount, min_amount=0, max_amount=None):
        """Validate amount range"""
        if amount < min_amount:
            raise ValidationError(
                f'Amount must be at least {min_amount}.',
                code='amount_too_low'
            )
        
        if max_amount and amount > max_amount:
            raise ValidationError(
                f'Amount cannot exceed {max_amount}.',
                code='amount_too_high'
            )
    
    @staticmethod
    def validate_percentage(value):
        """Validate percentage value"""
        if not 0 <= value <= 100:
            raise ValidationError(
                'Percentage must be between 0 and 100.',
                code='invalid_percentage'
            )


def validate_json_structure(value, required_fields=None):
    """Validate JSON structure"""
    if not isinstance(value, dict):
        raise ValidationError(
            'Value must be a valid JSON object.',
            code='invalid_json'
        )
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in value]
        if missing_fields:
            raise ValidationError(
                f'Missing required fields: {", ".join(missing_fields)}',
                code='missing_json_fields'
            )


def validate_file_size(value, max_size_mb=10):
    """Validate file size"""
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            f'File size cannot exceed {max_size_mb}MB.',
            code='file_too_large'
        )


def validate_file_extension(value, allowed_extensions=None):
    """Validate file extension"""
    if allowed_extensions is None:
        allowed_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png']
    
    ext = value.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}',
            code='invalid_file_type'
        )
