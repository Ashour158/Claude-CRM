# audit/models.py
# Audit and Compliance Management Models

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import CompanyIsolatedModel, User
import uuid
import json
from datetime import datetime, timedelta

class AuditLog(CompanyIsolatedModel):
    """Comprehensive audit logging for all system changes"""
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('permission_change', 'Permission Change'),
        ('data_access', 'Data Access'),
        ('system_change', 'System Change'),
    ]
    
    # Entity being audited
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Action details
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField(blank=True)
    
    # User and session information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    session_key = models.CharField(max_length=40, blank=True)
    
    # Request context
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Change details
    old_values = models.JSONField(default=dict, help_text="Previous field values")
    new_values = models.JSONField(default=dict, help_text="New field values")
    changed_fields = models.JSONField(default=list, help_text="List of changed fields")
    
    # Compliance and security
    is_sensitive = models.BooleanField(default=False, help_text="Contains sensitive data")
    requires_review = models.BooleanField(default=False, help_text="Requires compliance review")
    compliance_flags = models.JSONField(default=list, help_text="Compliance-related flags")
    
    # Impersonation tracking
    impersonated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='impersonation_audit_logs',
        help_text="User who performed action on behalf of another"
    )
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['content_type', 'object_id', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['is_sensitive', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action.upper()}: {self.content_object} by {self.user} at {self.timestamp}"

class AuditPolicy(CompanyIsolatedModel):
    """Audit policies and monitoring rules"""
    
    POLICY_TYPES = [
        ('retention', 'Data Retention'),
        ('monitoring', 'Activity Monitoring'),
        ('alerting', 'Alert Generation'),
        ('compliance', 'Compliance Check'),
        ('security', 'Security Audit'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    
    # Policy configuration
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1, help_text="Priority level (1-10)")
    
    # Monitoring rules
    target_models = models.JSONField(default=list, help_text="Models to monitor")
    target_actions = models.JSONField(default=list, help_text="Actions to monitor")
    conditions = models.JSONField(default=dict, help_text="Policy conditions")
    
    # Retention settings
    retention_period = models.DurationField(null=True, blank=True, help_text="How long to keep logs")
    auto_archive = models.BooleanField(default=False)
    auto_delete = models.BooleanField(default=False)
    
    # Alert settings
    alert_enabled = models.BooleanField(default=False)
    alert_recipients = models.JSONField(default=list, help_text="Alert recipients")
    alert_threshold = models.IntegerField(default=1, help_text="Number of violations before alert")
    
    # Compliance settings
    compliance_standard = models.CharField(max_length=100, blank=True, help_text="Compliance standard (e.g., SOX, GDPR)")
    review_required = models.BooleanField(default=False)
    review_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ],
        default='monthly'
    )
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_policies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Audit Policy"
        verbose_name_plural = "Audit Policies"
        ordering = ['priority', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.policy_type})"

class AuditReview(CompanyIsolatedModel):
    """Audit log reviews and compliance checks"""
    
    REVIEW_STATUS = [
        ('pending', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('requires_action', 'Requires Action'),
    ]
    
    audit_log = models.ForeignKey(AuditLog, on_delete=models.CASCADE, related_name='reviews')
    policy = models.ForeignKey(AuditPolicy, on_delete=models.CASCADE, related_name='reviews')
    
    status = models.CharField(max_length=20, choices=REVIEW_STATUS, default='pending')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_reviews')
    
    # Review details
    review_notes = models.TextField(blank=True)
    compliance_notes = models.TextField(blank=True)
    risk_assessment = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low Risk'),
            ('medium', 'Medium Risk'),
            ('high', 'High Risk'),
            ('critical', 'Critical Risk'),
        ],
        default='low'
    )
    
    # Action taken
    action_taken = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    assigned_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Audit Review"
        verbose_name_plural = "Audit Reviews"
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"Review: {self.audit_log} - {self.status}"

class ComplianceReport(CompanyIsolatedModel):
    """Compliance reports and analytics"""
    
    REPORT_TYPES = [
        ('security', 'Security Audit'),
        ('data_access', 'Data Access Report'),
        ('user_activity', 'User Activity Report'),
        ('system_changes', 'System Changes Report'),
        ('compliance', 'Compliance Report'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    
    # Report configuration
    date_range_start = models.DateTimeField()
    date_range_end = models.DateTimeField()
    filters = models.JSONField(default=dict, help_text="Report filters")
    
    # Report content
    summary = models.TextField(blank=True)
    findings = models.JSONField(default=list, help_text="Report findings")
    recommendations = models.JSONField(default=list, help_text="Recommendations")
    
    # Compliance details
    compliance_standard = models.CharField(max_length=100, blank=True)
    compliance_score = models.FloatField(null=True, blank=True, help_text="Compliance score (0-100)")
    violations_count = models.IntegerField(default=0)
    critical_issues = models.IntegerField(default=0)
    
    # Report status
    status = models.CharField(
        max_length=20,
        choices=[
            ('generating', 'Generating'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='generating'
    )
    
    # Export options
    export_format = models.CharField(
        max_length=20,
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
            ('json', 'JSON'),
        ],
        default='pdf'
    )
    export_path = models.CharField(max_length=500, blank=True)
    
    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compliance_reports')
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Compliance Report"
        verbose_name_plural = "Compliance Reports"
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.name} - {self.report_type} ({self.date_range_start.date()})"

class AuditExport(CompanyIsolatedModel):
    """Audit log export jobs"""
    
    EXPORT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    EXPORT_FORMATS = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('xml', 'XML'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Export configuration
    date_range_start = models.DateTimeField()
    date_range_end = models.DateTimeField()
    filters = models.JSONField(default=dict, help_text="Export filters")
    format = models.CharField(max_length=20, choices=EXPORT_FORMATS, default='csv')
    
    # Export settings
    include_sensitive = models.BooleanField(default=False)
    anonymize_data = models.BooleanField(default=False)
    compression_enabled = models.BooleanField(default=True)
    
    # Status and results
    status = models.CharField(max_length=20, choices=EXPORT_STATUS, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    record_count = models.IntegerField(default=0)
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Timestamps
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_exports')
    requested_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Audit Export"
        verbose_name_plural = "Audit Exports"
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.name} - {self.status} ({self.requested_at.date()})"
