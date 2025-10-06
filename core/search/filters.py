# core/search/filters.py
# GDPR and PII/PHI filtering for search results

from typing import Dict, Any, List, Set
import logging

logger = logging.getLogger(__name__)


class GDPRFilter:
    """
    Filter for handling PII/PHI data in search results according to GDPR requirements.
    """
    
    # PII fields that should be masked or filtered
    PII_FIELDS = {
        'email', 'phone', 'mobile', 'fax',
        'date_of_birth', 'birth_date',
        'ssn', 'social_security_number',
        'tax_id', 'tax_identification',
        'passport_number', 'drivers_license',
        'credit_card', 'bank_account',
    }
    
    # PHI (Protected Health Information) fields
    PHI_FIELDS = {
        'medical_record', 'diagnosis', 'treatment',
        'health_insurance', 'prescription',
    }
    
    # Address fields that may contain PII
    ADDRESS_FIELDS = {
        'address_line1', 'address_line2', 'address',
        'billing_address_line1', 'billing_address_line2',
        'shipping_address_line1', 'shipping_address_line2',
        'mailing_address_line1', 'mailing_address_line2',
        'other_address_line1', 'other_address_line2',
        'street', 'street_address',
    }
    
    # Sensitive fields
    SENSITIVE_FIELDS = PII_FIELDS | PHI_FIELDS
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize GDPR filter with configuration.
        
        Args:
            config: Configuration dictionary with:
                - mask_pii: Whether to mask PII fields (default: False)
                - remove_pii: Whether to remove PII fields (default: False)
                - mask_phi: Whether to mask PHI fields (default: False)
                - remove_phi: Whether to remove PHI fields (default: False)
                - mask_addresses: Whether to mask address fields (default: False)
                - allowed_users: Set of user IDs that can see unfiltered data
                - allowed_roles: Set of roles that can see unfiltered data
        """
        self.config = config or {}
        self.mask_pii = self.config.get('mask_pii', False)
        self.remove_pii = self.config.get('remove_pii', False)
        self.mask_phi = self.config.get('mask_phi', False)
        self.remove_phi = self.config.get('remove_phi', False)
        self.mask_addresses = self.config.get('mask_addresses', False)
        self.allowed_users = set(self.config.get('allowed_users', []))
        self.allowed_roles = set(self.config.get('allowed_roles', ['admin', 'compliance']))
    
    def filter_result(
        self, 
        data: Dict[str, Any],
        user_id: str = None,
        user_role: str = None
    ) -> Dict[str, Any]:
        """
        Filter a single search result according to GDPR rules.
        
        Args:
            data: Result data dictionary
            user_id: ID of user requesting data
            user_role: Role of user requesting data
        
        Returns:
            Filtered data dictionary
        """
        # Check if user has permission to see unfiltered data
        if self._user_has_permission(user_id, user_role):
            return data
        
        filtered_data = data.copy()
        pii_filtered = False
        
        # Filter PII fields
        if self.mask_pii or self.remove_pii:
            for field in self.PII_FIELDS:
                if field in filtered_data:
                    if self.remove_pii:
                        del filtered_data[field]
                    elif self.mask_pii:
                        filtered_data[field] = self._mask_value(filtered_data[field], field)
                    pii_filtered = True
        
        # Filter PHI fields
        if self.mask_phi or self.remove_phi:
            for field in self.PHI_FIELDS:
                if field in filtered_data:
                    if self.remove_phi:
                        del filtered_data[field]
                    elif self.mask_phi:
                        filtered_data[field] = self._mask_value(filtered_data[field], field)
                    pii_filtered = True
        
        # Filter address fields
        if self.mask_addresses:
            for field in self.ADDRESS_FIELDS:
                if field in filtered_data:
                    filtered_data[field] = self._mask_address(filtered_data[field])
                    pii_filtered = True
        
        return filtered_data
    
    def filter_results(
        self, 
        results: List[Dict[str, Any]],
        user_id: str = None,
        user_role: str = None
    ) -> List[Dict[str, Any]]:
        """
        Filter multiple search results.
        
        Args:
            results: List of result dictionaries
            user_id: ID of user requesting data
            user_role: Role of user requesting data
        
        Returns:
            List of filtered result dictionaries
        """
        return [
            self.filter_result(result, user_id, user_role)
            for result in results
        ]
    
    def _user_has_permission(self, user_id: str = None, user_role: str = None) -> bool:
        """Check if user has permission to see unfiltered data"""
        if user_id and user_id in self.allowed_users:
            return True
        if user_role and user_role in self.allowed_roles:
            return True
        return False
    
    def _mask_value(self, value: Any, field_type: str) -> str:
        """
        Mask a sensitive value based on its type.
        
        Args:
            value: Value to mask
            field_type: Type of field (used for appropriate masking)
        
        Returns:
            Masked string
        """
        if not value:
            return value
        
        value_str = str(value)
        
        # Email masking: show first char and domain
        if 'email' in field_type:
            if '@' in value_str:
                local, domain = value_str.split('@', 1)
                if len(local) > 1:
                    return f"{local[0]}***@{domain}"
                return f"***@{domain}"
        
        # Phone masking: show last 4 digits
        if 'phone' in field_type or 'mobile' in field_type or 'fax' in field_type:
            # Remove non-digits
            digits = ''.join(c for c in value_str if c.isdigit())
            if len(digits) >= 4:
                return f"***-***-{digits[-4:]}"
            return "***-***-****"
        
        # Date masking: show only year
        if 'date' in field_type or 'birth' in field_type:
            if len(value_str) >= 4:
                return f"{value_str[:4]}-**-**"
        
        # Default masking: show first and last char
        if len(value_str) > 2:
            return f"{value_str[0]}***{value_str[-1]}"
        
        return "***"
    
    def _mask_address(self, address: str) -> str:
        """
        Mask address by showing only city/state.
        
        Args:
            address: Full address string
        
        Returns:
            Masked address showing only general location
        """
        if not address:
            return address
        
        # Simple masking: replace street numbers and names
        parts = address.split(',')
        if len(parts) > 1:
            # Keep only the last parts (typically city, state)
            return ', '.join(parts[-2:]).strip()
        
        return "*** (address masked)"
    
    def get_sensitive_fields(self) -> Set[str]:
        """Get all fields considered sensitive"""
        return self.SENSITIVE_FIELDS | self.ADDRESS_FIELDS
    
    def is_field_sensitive(self, field_name: str) -> bool:
        """Check if a field is considered sensitive"""
        field_lower = field_name.lower()
        return (
            field_lower in self.SENSITIVE_FIELDS or
            any(sensitive in field_lower for sensitive in self.SENSITIVE_FIELDS) or
            field_lower in self.ADDRESS_FIELDS
        )
    
    def tag_result_with_sensitivity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tag result fields with sensitivity classification.
        
        Args:
            data: Result data dictionary
        
        Returns:
            Dictionary with sensitivity tags added
        """
        sensitivity_tags = {}
        
        for field in data.keys():
            if field in self.PII_FIELDS:
                sensitivity_tags[field] = 'PII'
            elif field in self.PHI_FIELDS:
                sensitivity_tags[field] = 'PHI'
            elif field in self.ADDRESS_FIELDS:
                sensitivity_tags[field] = 'ADDRESS'
            else:
                sensitivity_tags[field] = 'PUBLIC'
        
        return {
            'data': data,
            'sensitivity': sensitivity_tags
        }
