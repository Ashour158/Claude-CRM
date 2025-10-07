# data_import/models.py
# Data import staging, mapping, validation, and deduplication models

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class ImportTemplate(CompanyIsolatedModel):
    """Import templates with field mapping configuration"""
    
    ENTITY_TYPES = [
        ('account', 'Account'),
        ('contact', 'Contact'),
        ('lead', 'Lead'),
        ('deal', 'Deal'),
        ('product', 'Product'),
        ('invoice', 'Invoice'),
        ('custom', 'Custom Entity'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPES
    )
    
    # Field Mapping
    field_mapping = models.JSONField(
        default=dict,
        help_text="Maps source fields to target entity fields"
    )
    default_values = models.JSONField(
        default=dict,
        help_text="Default values for unmapped fields"
    )
    transformation_rules = models.JSONField(
        default=list,
        help_text="Data transformation rules (e.g., date format, text case)"
    )
    
    # Validation Rules
    validation_rules = models.JSONField(
        default=list,
        help_text="Field validation rules"
    )
    required_fields = models.JSONField(
        default=list,
        help_text="List of required field names"
    )
    
    # Deduplication Settings
    dedupe_enabled = models.BooleanField(
        default=True,
        help_text="Enable duplicate detection"
    )
    dedupe_fields = models.JSONField(
        default=list,
        help_text="Fields to use for duplicate detection"
    )
    dedupe_strategy = models.CharField(
        max_length=20,
        choices=[
            ('skip', 'Skip Duplicates'),
            ('update', 'Update Existing'),
            ('create_new', 'Create New'),
            ('merge', 'Merge Records'),
        ],
        default='skip'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(
        default=False,
        help_text="Available to all users in company"
    )
    
    # Statistics
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_import_templates'
    )
    
    class Meta:
        db_table = 'import_template'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.entity_type})"


class ImportJob(CompanyIsolatedModel):
    """Import job instances"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('validating', 'Validating'),
        ('staging', 'Staging'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    import_template = models.ForeignKey(
        ImportTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='import_jobs'
    )
    
    # File Information
    source_file = models.FileField(
        upload_to='imports/',
        help_text="Uploaded import file"
    )
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    file_type = models.CharField(
        max_length=20,
        choices=[
            ('csv', 'CSV'),
            ('excel', 'Excel'),
            ('json', 'JSON'),
            ('xml', 'XML'),
        ]
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Statistics
    total_rows = models.IntegerField(default=0)
    valid_rows = models.IntegerField(default=0)
    invalid_rows = models.IntegerField(default=0)
    duplicate_rows = models.IntegerField(default=0)
    imported_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Progress
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    current_row = models.IntegerField(default=0)
    
    # Error Information
    error_summary = models.TextField(blank=True)
    error_log = models.JSONField(
        default=list,
        help_text="Detailed error log"
    )
    
    # Owner
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_imports'
    )
    
    class Meta:
        db_table = 'import_job'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.status}"


class ImportStagingRecord(CompanyIsolatedModel):
    """Staging area for import records before final import"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Validation'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('duplicate', 'Duplicate'),
        ('imported', 'Imported'),
        ('skipped', 'Skipped'),
        ('failed', 'Failed'),
    ]
    
    import_job = models.ForeignKey(
        ImportJob,
        on_delete=models.CASCADE,
        related_name='staging_records'
    )
    
    # Record Information
    row_number = models.IntegerField(help_text="Row number in source file")
    source_data = models.JSONField(
        default=dict,
        help_text="Original data from source file"
    )
    mapped_data = models.JSONField(
        default=dict,
        help_text="Data after field mapping"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Validation
    is_valid = models.BooleanField(default=False)
    validation_errors = models.JSONField(
        default=list,
        help_text="Validation error messages"
    )
    
    # Deduplication
    is_duplicate = models.BooleanField(default=False)
    duplicate_of = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID of existing record (if duplicate)"
    )
    duplicate_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Similarity score (0-100)"
    )
    duplicate_candidates = models.JSONField(
        default=list,
        help_text="List of potential duplicate records"
    )
    
    # Import Result
    imported_entity_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID of imported entity"
    )
    import_action = models.CharField(
        max_length=20,
        choices=[
            ('created', 'Created'),
            ('updated', 'Updated'),
            ('merged', 'Merged'),
            ('skipped', 'Skipped'),
        ],
        blank=True
    )
    import_error = models.TextField(blank=True)
    
    class Meta:
        db_table = 'import_staging_record'
        ordering = ['import_job', 'row_number']
        indexes = [
            models.Index(fields=['import_job', 'status']),
            models.Index(fields=['import_job', 'is_duplicate']),
        ]
    
    def __str__(self):
        return f"Row {self.row_number} - {self.status}"


class DuplicateRule(CompanyIsolatedModel):
    """Duplicate detection rules"""
    
    MATCH_TYPES = [
        ('exact', 'Exact Match'),
        ('fuzzy', 'Fuzzy Match'),
        ('phonetic', 'Phonetic Match'),
        ('custom', 'Custom Algorithm'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    entity_type = models.CharField(max_length=50)
    
    # Match Configuration
    match_fields = models.JSONField(
        default=list,
        help_text="Fields to compare for duplicates"
    )
    match_type = models.CharField(
        max_length=20,
        choices=MATCH_TYPES,
        default='exact'
    )
    match_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=80.00,
        help_text="Minimum similarity score to consider as duplicate (0-100)"
    )
    
    # Field Weights
    field_weights = models.JSONField(
        default=dict,
        help_text="Importance weight for each field (0-1)"
    )
    
    # Advanced Options
    case_sensitive = models.BooleanField(default=False)
    ignore_whitespace = models.BooleanField(default=True)
    ignore_special_chars = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(
        default=0,
        help_text="Rule priority (higher = check first)"
    )
    
    # Statistics
    match_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_duplicate_rules'
    )
    
    class Meta:
        db_table = 'duplicate_rule'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.entity_type})"
