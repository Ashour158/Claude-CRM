# master_data/models.py
# Master Data Management for enterprise CRM

from django.db import models
from core.models import CompanyIsolatedModel, User
from django.core.validators import RegexValidator
import uuid

class MasterDataCategory(CompanyIsolatedModel):
    """Categories for master data classification"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Master Data Categories"
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class MasterDataField(CompanyIsolatedModel):
    """Fields for master data records"""
    
    FIELD_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Boolean'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('phone', 'Phone'),
        ('select', 'Select'),
        ('multiselect', 'Multi-Select'),
    ]
    
    category = models.ForeignKey(MasterDataCategory, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    default_value = models.TextField(blank=True, null=True)
    validation_rules = models.JSONField(default=dict, blank=True)
    options = models.JSONField(default=list, blank=True)  # For select/multiselect fields
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('company', 'category', 'name')
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class MasterDataRecord(CompanyIsolatedModel):
    """Master data records"""
    
    category = models.ForeignKey(MasterDataCategory, on_delete=models.CASCADE, related_name='records')
    external_id = models.CharField(max_length=100, blank=True, null=True)  # External system ID
    data = models.JSONField(default=dict)  # Flexible data storage
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_master_data')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_master_data')
    verified_at = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('company', 'category', 'external_id')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.category.name} - {self.external_id or self.id}"
    
    def get_field_value(self, field_name: str):
        """Get value for a specific field"""
        return self.data.get(field_name)
    
    def set_field_value(self, field_name: str, value):
        """Set value for a specific field"""
        self.data[field_name] = value
        self.save(update_fields=['data'])
    
    def validate_data(self):
        """Validate data against field definitions"""
        errors = []
        
        for field in self.category.fields.filter(is_active=True):
            value = self.data.get(field.name)
            
            # Check required fields
            if field.is_required and not value:
                errors.append(f"{field.name} is required")
                continue
            
            # Skip validation if no value and not required
            if not value:
                continue
            
            # Type-specific validation
            if field.field_type == 'email':
                from django.core.validators import validate_email
                try:
                    validate_email(value)
                except:
                    errors.append(f"{field.name} must be a valid email")
            
            elif field.field_type == 'number':
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append(f"{field.name} must be a number")
            
            elif field.field_type == 'date':
                from datetime import datetime
                try:
                    datetime.strptime(value, '%Y-%m-%d')
                except (ValueError, TypeError):
                    errors.append(f"{field.name} must be a valid date (YYYY-MM-DD)")
            
            elif field.field_type == 'boolean':
                if value not in [True, False, 'true', 'false', '1', '0']:
                    errors.append(f"{field.name} must be true or false")
            
            elif field.field_type == 'url':
                from django.core.validators import URLValidator
                try:
                    URLValidator()(value)
                except:
                    errors.append(f"{field.name} must be a valid URL")
            
            elif field.field_type == 'phone':
                phone_validator = RegexValidator(
                    regex=r'^\+?1?\d{9,15}$',
                    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
                )
                try:
                    phone_validator(value)
                except:
                    errors.append(f"{field.name} must be a valid phone number")
            
            elif field.field_type in ['select', 'multiselect']:
                if field.field_type == 'select':
                    if value not in field.options:
                        errors.append(f"{field.name} must be one of: {', '.join(field.options)}")
                else:  # multiselect
                    if not isinstance(value, list):
                        errors.append(f"{field.name} must be a list")
                    elif not all(option in field.options for option in value):
                        errors.append(f"{field.name} must contain only valid options")
        
        return errors


class DataQualityRule(CompanyIsolatedModel):
    """Data quality rules for master data"""
    
    RULE_TYPES = [
        ('completeness', 'Completeness'),
        ('accuracy', 'Accuracy'),
        ('consistency', 'Consistency'),
        ('uniqueness', 'Uniqueness'),
        ('validity', 'Validity'),
    ]
    
    category = models.ForeignKey(MasterDataCategory, on_delete=models.CASCADE, related_name='quality_rules')
    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    description = models.TextField()
    rule_expression = models.TextField()  # JSON or SQL expression
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('company', 'category', 'name')
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class DataQualityCheck(CompanyIsolatedModel):
    """Data quality check results"""
    
    record = models.ForeignKey(MasterDataRecord, on_delete=models.CASCADE, related_name='quality_checks')
    rule = models.ForeignKey(DataQualityRule, on_delete=models.CASCADE, related_name='check_results')
    passed = models.BooleanField()
    error_message = models.TextField(blank=True, null=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('record', 'rule')
        ordering = ['-checked_at']
    
    def __str__(self):
        return f"{self.record} - {self.rule.name} - {'PASS' if self.passed else 'FAIL'}"


class DataMapping(CompanyIsolatedModel):
    """Data mapping between systems"""
    
    MAPPING_TYPES = [
        ('import', 'Import'),
        ('export', 'Export'),
        ('sync', 'Synchronization'),
    ]
    
    name = models.CharField(max_length=100)
    mapping_type = models.CharField(max_length=20, choices=MAPPING_TYPES)
    source_system = models.CharField(max_length=100)
    target_system = models.CharField(max_length=100)
    category = models.ForeignKey(MasterDataCategory, on_delete=models.CASCADE, related_name='mappings')
    field_mappings = models.JSONField(default=dict)  # Field mapping configuration
    transformation_rules = models.JSONField(default=dict)  # Data transformation rules
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_frequency = models.IntegerField(default=24)  # Hours between syncs
    
    class Meta:
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.mapping_type})"


class DataSyncLog(CompanyIsolatedModel):
    """Data synchronization logs"""
    
    mapping = models.ForeignKey(DataMapping, on_delete=models.CASCADE, related_name='sync_logs')
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='running')
    records_processed = models.IntegerField(default=0)
    records_successful = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.mapping.name} - {self.started_at} - {self.status}"


class DataGovernance(CompanyIsolatedModel):
    """Data governance policies and rules"""
    
    POLICY_TYPES = [
        ('retention', 'Data Retention'),
        ('privacy', 'Privacy'),
        ('access', 'Access Control'),
        ('quality', 'Data Quality'),
        ('compliance', 'Compliance'),
    ]
    
    name = models.CharField(max_length=100)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    description = models.TextField()
    rules = models.JSONField(default=dict)  # Policy rules and conditions
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_governance_policies')
    
    class Meta:
        unique_together = ('company', 'name')
        ordering = ['-effective_date']
    
    def __str__(self):
        return f"{self.name} ({self.policy_type})"
