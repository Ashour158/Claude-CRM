# data_import/models.py
# Data Import and Deduplication Engine Models

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import CompanyIsolatedModel, User
import uuid
import json
from datetime import datetime, timedelta

class ImportTemplate(CompanyIsolatedModel):
    """Reusable import templates for data import"""
    
    TEMPLATE_TYPES = [
        ('contacts', 'Contacts'),
        ('leads', 'Leads'),
        ('accounts', 'Accounts'),
        ('deals', 'Deals'),
        ('products', 'Products'),
        ('activities', 'Activities'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    target_model = models.CharField(max_length=100, help_text="Target Django model name")
    
    # Field mapping configuration
    field_mappings = models.JSONField(default=dict, help_text="Source to target field mappings")
    transformations = models.JSONField(default=dict, help_text="Data transformation rules")
    validation_rules = models.JSONField(default=dict, help_text="Field validation rules")
    
    # Duplicate detection settings
    duplicate_detection_enabled = models.BooleanField(default=True)
    duplicate_fields = models.JSONField(default=list, help_text="Fields to check for duplicates")
    duplicate_algorithm = models.CharField(
        max_length=20,
        choices=[
            ('exact', 'Exact Match'),
            ('fuzzy', 'Fuzzy Match'),
            ('phonetic', 'Phonetic Match'),
            ('combined', 'Combined Match'),
        ],
        default='fuzzy'
    )
    duplicate_threshold = models.FloatField(default=0.8, help_text="Similarity threshold for fuzzy matching")
    
    # Import settings
    batch_size = models.IntegerField(default=100)
    skip_errors = models.BooleanField(default=True)
    create_missing = models.BooleanField(default=True)
    update_existing = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='import_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Import Template"
        verbose_name_plural = "Import Templates"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"

class ImportJob(CompanyIsolatedModel):
    """Import job execution tracking"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    template = models.ForeignKey(ImportTemplate, on_delete=models.CASCADE, related_name='jobs')
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=20, choices=[
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML'),
    ])
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0, help_text="Progress percentage")
    
    # Statistics
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    valid_rows = models.IntegerField(default=0)
    invalid_rows = models.IntegerField(default=0)
    duplicate_rows = models.IntegerField(default=0)
    imported_rows = models.IntegerField(default=0)
    skipped_rows = models.IntegerField(default=0)
    
    # Error tracking
    error_count = models.IntegerField(default=0)
    error_log = models.JSONField(default=list, help_text="Error details")
    
    # Execution details
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='import_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Import Job"
        verbose_name_plural = "Import Jobs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.template.name} - {self.file_name} ({self.status})"

class StagedRecord(CompanyIsolatedModel):
    """Staged records for preview before import"""
    
    job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='staged_records')
    row_number = models.IntegerField()
    
    # Raw data
    raw_data = models.JSONField(help_text="Original row data")
    
    # Processed data
    processed_data = models.JSONField(help_text="Transformed data ready for import")
    
    # Validation
    is_valid = models.BooleanField(default=True)
    validation_errors = models.JSONField(default=list, help_text="Validation error details")
    
    # Duplicate detection
    is_duplicate = models.BooleanField(default=False)
    duplicate_matches = models.JSONField(default=list, help_text="Matching existing records")
    duplicate_strategy = models.CharField(
        max_length=20,
        choices=[
            ('skip', 'Skip'),
            ('update', 'Update'),
            ('merge', 'Merge'),
            ('create', 'Create New'),
        ],
        default='skip'
    )
    
    # Import status
    import_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('imported', 'Imported'),
            ('skipped', 'Skipped'),
            ('error', 'Error'),
        ],
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Staged Record"
        verbose_name_plural = "Staged Records"
        ordering = ['row_number']
        unique_together = ['job', 'row_number']
    
    def __str__(self):
        return f"Row {self.row_number} - {self.job.file_name}"

class ImportLog(CompanyIsolatedModel):
    """Detailed import execution logs"""
    
    LOG_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]
    
    job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    message = models.TextField()
    details = models.JSONField(default=dict, help_text="Additional log details")
    
    # Context
    row_number = models.IntegerField(null=True, blank=True)
    field_name = models.CharField(max_length=100, blank=True)
    field_value = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Import Log"
        verbose_name_plural = "Import Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.log_type.upper()}: {self.message[:50]}..."

class DuplicateMatch(CompanyIsolatedModel):
    """Duplicate detection matches"""
    
    job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='duplicate_matches')
    staged_record = models.ForeignKey(StagedRecord, on_delete=models.CASCADE, related_name='matches')
    
    # Matching record details
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    matched_object = GenericForeignKey('content_type', 'object_id')
    
    # Match details
    similarity_score = models.FloatField(help_text="Similarity score (0-1)")
    match_fields = models.JSONField(default=list, help_text="Fields that matched")
    match_algorithm = models.CharField(max_length=20, help_text="Algorithm used for matching")
    
    # Resolution
    resolution = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('skip', 'Skip'),
            ('update', 'Update'),
            ('merge', 'Merge'),
            ('create', 'Create New'),
        ],
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Duplicate Match"
        verbose_name_plural = "Duplicate Matches"
        ordering = ['-similarity_score']
    
    def __str__(self):
        return f"Match: {self.staged_record.row_number} -> {self.matched_object} ({self.similarity_score:.2f})"
