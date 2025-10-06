# core/permissions_service.py
# Field-level permissions and masking service for Phase 4+

import hashlib
import logging
from typing import Dict, Any, List, Optional, Set
from django.core.cache import cache
from core.permissions_models import (
    Role, RoleFieldPermission, GDPRRegistry, MaskingAuditLog
)

logger = logging.getLogger(__name__)

class FieldPermissionService:
    """Service for field-level permission management"""
    
    CACHE_PREFIX = 'field_perms'
    CACHE_TTL = 300  # 5 minutes
    
    @classmethod
    def get_field_permissions(
        cls,
        role: Role,
        object_type: str
    ) -> Dict[str, str]:
        """
        Get field permissions for a role and object type.
        
        Returns:
            Dict mapping field_name -> mode ('view', 'mask', 'hidden', 'edit')
        """
        cache_key = f"{cls.CACHE_PREFIX}:{role.id}:{object_type}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        permissions = {}
        field_perms = RoleFieldPermission.objects.filter(
            role=role,
            object_type=object_type
        )
        
        for perm in field_perms:
            permissions[perm.field_name] = perm.mode
        
        cache.set(cache_key, permissions, cls.CACHE_TTL)
        return permissions
    
    @classmethod
    def can_view_field(
        cls,
        role: Role,
        object_type: str,
        field_name: str
    ) -> bool:
        """Check if role can view a field (not hidden)"""
        perms = cls.get_field_permissions(role, object_type)
        mode = perms.get(field_name, 'view')
        return mode != 'hidden'
    
    @classmethod
    def can_edit_field(
        cls,
        role: Role,
        object_type: str,
        field_name: str
    ) -> bool:
        """Check if role can edit a field"""
        perms = cls.get_field_permissions(role, object_type)
        mode = perms.get(field_name, 'view')
        return mode == 'edit'
    
    @classmethod
    def should_mask_field(
        cls,
        role: Role,
        object_type: str,
        field_name: str
    ) -> bool:
        """Check if field should be masked for this role"""
        perms = cls.get_field_permissions(role, object_type)
        mode = perms.get(field_name, 'view')
        return mode == 'mask'
    
    @classmethod
    def filter_fields_for_role(
        cls,
        data: Dict[str, Any],
        role: Role,
        object_type: str,
        apply_masking: bool = True
    ) -> Dict[str, Any]:
        """
        Filter and mask fields in data based on role permissions.
        
        Args:
            data: Dictionary of field values
            role: User's role
            object_type: Object type (e.g., 'lead', 'contact')
            apply_masking: Whether to apply masking (vs just hiding)
        
        Returns:
            Filtered dictionary with permissions applied
        """
        perms = cls.get_field_permissions(role, object_type)
        filtered = {}
        
        for field_name, value in data.items():
            mode = perms.get(field_name, 'view')
            
            if mode == 'hidden':
                # Skip hidden fields
                continue
            elif mode == 'mask' and apply_masking:
                # Mask the field
                filtered[field_name] = MaskingService.mask_field(
                    value, object_type, field_name, role.company
                )
            else:
                # Include field as-is
                filtered[field_name] = value
        
        return filtered

class MaskingService:
    """Service for data masking and PII protection"""
    
    @classmethod
    def mask_field(
        cls,
        value: Any,
        object_type: str,
        field_name: str,
        company
    ) -> Any:
        """
        Mask a field value according to GDPR registry rules.
        
        Args:
            value: Field value to mask
            object_type: Object type
            field_name: Field name
            company: Company context
        
        Returns:
            Masked value
        """
        if value is None or value == '':
            return value
        
        # Get masking config from GDPR registry
        try:
            registry = GDPRRegistry.objects.get(
                company=company,
                object_type=object_type,
                field_name=field_name,
                is_active=True
            )
            mask_type = registry.mask_type
            mask_config = registry.mask_config
        except GDPRRegistry.DoesNotExist:
            # Default to redaction if not configured
            mask_type = 'redact'
            mask_config = {}
        
        if mask_type == 'hash':
            return cls._mask_hash(value)
        elif mask_type == 'partial':
            return cls._mask_partial(value, mask_config)
        elif mask_type == 'redact':
            return '[REDACTED]'
        elif mask_type == 'encrypt':
            return cls._mask_encrypt(value, mask_config)
        elif mask_type == 'tokenize':
            return cls._mask_tokenize(value)
        else:
            return '[MASKED]'
    
    @staticmethod
    def _mask_hash(value: Any) -> str:
        """One-way hash masking"""
        value_str = str(value)
        hashed = hashlib.sha256(value_str.encode()).hexdigest()
        return f"hash:{hashed[:16]}..."
    
    @staticmethod
    def _mask_partial(value: Any, config: Dict) -> str:
        """Partial masking (show first/last N characters)"""
        value_str = str(value)
        show_first = config.get('show_first', 2)
        show_last = config.get('show_last', 2)
        mask_char = config.get('mask_char', '*')
        
        if len(value_str) <= show_first + show_last:
            # String too short, mask all but first char
            return value_str[0] + (mask_char * (len(value_str) - 1))
        
        return (
            value_str[:show_first] +
            (mask_char * (len(value_str) - show_first - show_last)) +
            value_str[-show_last:]
        )
    
    @staticmethod
    def _mask_encrypt(value: Any, config: Dict) -> str:
        """Reversible encryption masking (stub)"""
        # TODO: Implement proper encryption
        return f"enc:{hashlib.md5(str(value).encode()).hexdigest()[:16]}"
    
    @staticmethod
    def _mask_tokenize(value: Any) -> str:
        """Replace with deterministic token"""
        # Create deterministic token
        token_hash = hashlib.md5(str(value).encode()).hexdigest()
        return f"token_{token_hash[:8]}"
    
    @classmethod
    def log_masking_decision(
        cls,
        user,
        object_type: str,
        object_id: str,
        field_name: str,
        action: str,
        reason: str = ''
    ):
        """Log masking decision for audit"""
        try:
            MaskingAuditLog.objects.create(
                user=user,
                company=user.usercompanyaccess_set.first().company,
                object_type=object_type,
                object_id=object_id,
                field_name=field_name,
                action=action,
                reason=reason
            )
        except Exception as e:
            logger.error(f"Error logging masking decision: {e}")

class FieldPermissionMixin:
    """Mixin for DRF serializers to apply field-level permissions"""
    
    def get_fields(self):
        """Override to filter fields based on permissions"""
        fields = super().get_fields()
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            return fields
        
        # Get user's role (simplified - assumes role from company access)
        try:
            company_access = request.user.usercompanyaccess_set.filter(
                is_active=True
            ).first()
            if not company_access:
                return fields
            
            # Get role from company access
            from core.permissions_models import Role
            try:
                role = Role.objects.get(
                    company=company_access.company,
                    name=company_access.role
                )
            except Role.DoesNotExist:
                return fields
            
            # Get object type from model
            model_name = self.Meta.model.__name__.lower()
            
            # Filter fields
            filtered_fields = {}
            for field_name, field in fields.items():
                if FieldPermissionService.can_view_field(role, model_name, field_name):
                    filtered_fields[field_name] = field
            
            return filtered_fields
        
        except Exception as e:
            logger.error(f"Error applying field permissions: {e}")
            return fields
    
    def to_representation(self, instance):
        """Override to mask fields in output"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            return data
        
        try:
            company_access = request.user.usercompanyaccess_set.filter(
                is_active=True
            ).first()
            if not company_access:
                return data
            
            from core.permissions_models import Role
            try:
                role = Role.objects.get(
                    company=company_access.company,
                    name=company_access.role
                )
            except Role.DoesNotExist:
                return data
            
            model_name = self.Meta.model.__name__.lower()
            
            # Apply masking to fields
            for field_name in list(data.keys()):
                if FieldPermissionService.should_mask_field(role, model_name, field_name):
                    data[field_name] = MaskingService.mask_field(
                        data[field_name],
                        model_name,
                        field_name,
                        company_access.company
                    )
            
            return data
        
        except Exception as e:
            logger.error(f"Error applying masking: {e}")
            return data
