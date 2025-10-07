# audit/models.py
# Comprehensive audit explorer models for tracking all system changes

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class AuditLog(CompanyIsolatedModel):
    """Comprehensive audit log for all system changes"""
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('share', 'Share'),
        ('unshare', 'Unshare'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('execute', 'Execute'),
        ('configure', 'Configure'),
    ]
    
    # Audit Entry ID
    audit_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # User Information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    user_email = models.EmailField(
        blank=True,
        help_text="Stored for historical record if user is deleted"
    )
    impersonated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='impersonation_audit_logs',
        help_text="User who performed action on behalf of another user"
    )
    
    # Action Information
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    action_description = models.CharField(
        max_length=255,
        help_text="Human-readable description of action"
    )
    
    # Entity Information (using Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=100, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    entity_type = models.CharField(
        max_length=100,
        help_text="Entity type name"
    )
    entity_id = models.CharField(max_length=100)
    entity_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Display name of entity"
    )
    
    # Change Details
    old_values = models.JSONField(
        default=dict,
        help_text="Values before change"
    )
    new_values = models.JSONField(
        default=dict,
        help_text="Values after change"
    )
    changed_fields = models.JSONField(
        default=list,
        help_text="List of changed field names"
    )
    
    # Request Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=255, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    # Additional Context
    reason = models.TextField(
        blank=True,
        help_text="Reason for change (if provided)"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata about the action"
    )
    
    # Compliance Flags
    is_sensitive = models.BooleanField(
        default=False,
        help_text="Marks sensitive data changes"
    )
    requires_review = models.BooleanField(
        default=False,
        help_text="Flags for compliance review"
    )
    reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_audit_logs'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['entity_type', 'entity_id', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['is_sensitive', '-timestamp']),
            models.Index(fields=['requires_review', 'reviewed']),
        ]
    
    def __str__(self):
        return f"{self.user_email} - {self.action} - {self.entity_type} - {self.timestamp}"


class AuditLogExport(CompanyIsolatedModel):
    """Audit log export jobs"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Export Information
    export_id = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=255)
    
    # Filters
    filters = models.JSONField(
        default=dict,
        help_text="Filters applied to export (date range, users, actions, etc.)"
    )
    
    # Export Configuration
    format = models.CharField(
        max_length=20,
        choices=[
            ('csv', 'CSV'),
            ('excel', 'Excel'),
            ('json', 'JSON'),
            ('pdf', 'PDF'),
        ],
        default='csv'
    )
    include_metadata = models.BooleanField(default=True)
    include_old_values = models.BooleanField(default=True)
    include_new_values = models.BooleanField(default=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Results
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    record_count = models.IntegerField(default=0)
    
    # Timing
    requested_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When export file will be deleted"
    )
    
    # Error Information
    error_message = models.TextField(blank=True)
    
    # Requester
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requested_audit_exports'
    )
    
    class Meta:
        db_table = 'audit_log_export'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Export {self.name} - {self.status}"


class ComplianceReport(CompanyIsolatedModel):
    """Compliance and security reports"""
    
    REPORT_TYPES = [
        ('access', 'Access Report'),
        ('changes', 'Change Report'),
        ('data_export', 'Data Export Report'),
        ('permission', 'Permission Change Report'),
        ('login', 'Login Activity Report'),
        ('sensitive_data', 'Sensitive Data Access Report'),
        ('custom', 'Custom Compliance Report'),
    ]
    
    # Report Information
    report_id = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPES
    )
    
    # Report Period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Configuration
    configuration = models.JSONField(
        default=dict,
        help_text="Report configuration and filters"
    )
    
    # Results
    findings = models.JSONField(
        default=list,
        help_text="List of compliance findings"
    )
    violations = models.JSONField(
        default=list,
        help_text="List of policy violations"
    )
    recommendations = models.JSONField(
        default=list,
        help_text="List of recommendations"
    )
    
    # Summary Statistics
    total_events = models.IntegerField(default=0)
    flagged_events = models.IntegerField(default=0)
    high_risk_events = models.IntegerField(default=0)
    medium_risk_events = models.IntegerField(default=0)
    low_risk_events = models.IntegerField(default=0)
    
    # Status
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # File
    report_file = models.FileField(
        upload_to='compliance_reports/',
        null=True,
        blank=True
    )
    
    # Creator
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_compliance_reports'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_report'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.period_start} - {self.period_end})"


class AuditPolicy(CompanyIsolatedModel):
    """Audit and compliance policies"""
    
    # Policy Information
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    # Policy Rules
    rules = models.JSONField(
        default=list,
        help_text="List of policy rules"
    )
    
    # Entities Covered
    applies_to_entities = models.JSONField(
        default=list,
        help_text="Entity types this policy applies to"
    )
    applies_to_actions = models.JSONField(
        default=list,
        help_text="Actions this policy monitors"
    )
    
    # Alerting
    alert_on_violation = models.BooleanField(default=True)
    alert_recipients = models.JSONField(
        default=list,
        help_text="Users to alert on policy violation"
    )
    
    # Retention
    retention_days = models.IntegerField(
        default=365,
        help_text="Days to retain audit logs (0 = forever)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(
        default=0,
        help_text="Policy priority (higher = more important)"
    )
    
    # Statistics
    violation_count = models.IntegerField(default=0)
    last_violation = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_audit_policies'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'audit_policy'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return self.name
