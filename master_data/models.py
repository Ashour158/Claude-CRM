# master_data/models.py
# Master data management models

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class DataCategory(CompanyIsolatedModel):
    """Data categories for master data management"""
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'data_category'
        ordering = ['name']
        verbose_name_plural = 'Data Categories'
    
    def __str__(self):
        return self.name

class MasterDataField(CompanyIsolatedModel):
    """Master data field definitions"""
    
    FIELD_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Boolean'),
        ('choice', 'Choice'),
        ('multichoice', 'Multi Choice'),
        ('reference', 'Reference'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPES,
        default='text'
    )
    
    # Field Configuration
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    default_value = models.TextField(blank=True)
    choices = models.JSONField(
        default=list,
        help_text="Choices for choice/multichoice fields"
    )
    validation_rules = models.JSONField(
        default=dict,
        help_text="Field validation rules"
    )
    
    # Reference Configuration
    reference_model = models.CharField(
        max_length=100,
        blank=True,
        help_text="Referenced model for reference fields"
    )
    reference_field = models.CharField(
        max_length=100,
        blank=True,
        help_text="Referenced field for reference fields"
    )
    
    # Display Settings
    display_order = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    help_text = models.TextField(blank=True)
    
    # Access Control
    is_editable = models.BooleanField(default=True)
    is_searchable = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'master_data_field'
        ordering = ['display_order']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return self.label

class DataQualityRule(CompanyIsolatedModel):
    """Data quality rules and validation"""
    
    RULE_TYPES = [
        ('completeness', 'Completeness'),
        ('accuracy', 'Accuracy'),
        ('consistency', 'Consistency'),
        ('uniqueness', 'Uniqueness'),
        ('validity', 'Validity'),
        ('timeliness', 'Timeliness'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPES,
        default='validity'
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='medium'
    )
    
    # Rule Configuration
    entity_type = models.CharField(
        max_length=100,
        help_text="Entity type this rule applies to"
    )
    field_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Field name this rule applies to"
    )
    condition = models.TextField(help_text="Rule condition/expression")
    error_message = models.TextField(help_text="Error message when rule fails")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_global = models.BooleanField(
        default=False,
        help_text="Apply to all companies"
    )
    
    # Execution
    execution_count = models.IntegerField(default=0)
    violation_count = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_data_quality_rules'
    )
    
    class Meta:
        db_table = 'data_quality_rule'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class DataQualityViolation(CompanyIsolatedModel):
    """Data quality violations"""
    
    rule = models.ForeignKey(
        DataQualityRule,
        on_delete=models.CASCADE,
        related_name='violations'
    )
    
    # Violation Details
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100, blank=True)
    current_value = models.TextField(blank=True)
    expected_value = models.TextField(blank=True)
    violation_message = models.TextField()
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('ignored', 'Ignored'),
        ],
        default='open'
    )
    
    # Resolution
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_violations'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'data_quality_violation'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rule.name} - {self.entity_type} {self.entity_id}"

class DataImport(CompanyIsolatedModel):
    """Data import configurations and history"""
    
    IMPORT_TYPES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('api', 'API'),
        ('database', 'Database'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    import_type = models.CharField(
        max_length=20,
        choices=IMPORT_TYPES,
        default='csv'
    )
    
    # Source Configuration
    source_file = models.FileField(
        upload_to='imports/',
        null=True,
        blank=True
    )
    source_url = models.URLField(blank=True)
    source_config = models.JSONField(
        default=dict,
        help_text="Source configuration"
    )
    
    # Target Configuration
    target_entity = models.CharField(
        max_length=100,
        help_text="Target entity type"
    )
    field_mapping = models.JSONField(
        default=dict,
        help_text="Field mapping configuration"
    )
    import_rules = models.JSONField(
        default=dict,
        help_text="Import rules and transformations"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_records = models.IntegerField(default=0)
    imported_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    skipped_records = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_data_imports'
    )
    
    class Meta:
        db_table = 'data_import'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class DataExport(CompanyIsolatedModel):
    """Data export configurations and history"""
    
    EXPORT_TYPES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('pdf', 'PDF'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    export_type = models.CharField(
        max_length=20,
        choices=EXPORT_TYPES,
        default='csv'
    )
    
    # Source Configuration
    source_entity = models.CharField(
        max_length=100,
        help_text="Source entity type"
    )
    source_filters = models.JSONField(
        default=dict,
        help_text="Source filters"
    )
    source_fields = models.JSONField(
        default=list,
        help_text="Fields to export"
    )
    
    # Export Configuration
    export_format = models.JSONField(
        default=dict,
        help_text="Export format configuration"
    )
    export_rules = models.JSONField(
        default=dict,
        help_text="Export rules and transformations"
    )
    
    # Output
    output_file = models.FileField(
        upload_to='exports/',
        null=True,
        blank=True
    )
    output_url = models.URLField(blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_records = models.IntegerField(default=0)
    exported_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_data_exports'
    )
    
    class Meta:
        db_table = 'data_export'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class DataSynchronization(CompanyIsolatedModel):
    """Data synchronization between systems"""
    
    SYNC_TYPES = [
        ('import', 'Import'),
        ('export', 'Export'),
        ('bidirectional', 'Bidirectional'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPES,
        default='import'
    )
    
    # Source and Target
    source_system = models.CharField(max_length=100)
    target_system = models.CharField(max_length=100)
    source_config = models.JSONField(
        default=dict,
        help_text="Source system configuration"
    )
    target_config = models.JSONField(
        default=dict,
        help_text="Target system configuration"
    )
    
    # Sync Configuration
    entity_type = models.CharField(
        max_length=100,
        help_text="Entity type to sync"
    )
    field_mapping = models.JSONField(
        default=dict,
        help_text="Field mapping between systems"
    )
    sync_filters = models.JSONField(
        default=dict,
        help_text="Filters for sync data"
    )
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='manual'
    )
    schedule_time = models.TimeField(null=True, blank=True)
    next_sync = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_records = models.IntegerField(default=0)
    synced_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_data_synchronizations'
    )
    
    class Meta:
        db_table = 'data_synchronization'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.source_system} -> {self.target_system})"