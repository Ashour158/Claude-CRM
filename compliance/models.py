# compliance/models.py
# Compliance and Governance Models

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import CompanyIsolatedModel, User
import uuid
import json
from datetime import datetime, timedelta

class CompliancePolicy(CompanyIsolatedModel):
    """Compliance policies and governance rules"""
    
    POLICY_TYPES = [
        ('data_protection', 'Data Protection'),
        ('access_control', 'Access Control'),
        ('data_retention', 'Data Retention'),
        ('privacy', 'Privacy'),
        ('security', 'Security'),
        ('audit', 'Audit'),
        ('governance', 'Governance'),
    ]
    
    COMPLIANCE_STANDARDS = [
        ('gdpr', 'GDPR'),
        ('ccpa', 'CCPA'),
        ('sox', 'SOX'),
        ('hipaa', 'HIPAA'),
        ('pci_dss', 'PCI DSS'),
        ('iso27001', 'ISO 27001'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    compliance_standard = models.CharField(max_length=20, choices=COMPLIANCE_STANDARDS)
    
    # Policy configuration
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1, help_text="Priority level (1-10)")
    
    # Policy rules
    rules = models.JSONField(default=dict, help_text="Policy rules and conditions")
    enforcement_level = models.CharField(
        max_length=20,
        choices=[
            ('advisory', 'Advisory'),
            ('mandatory', 'Mandatory'),
            ('critical', 'Critical'),
        ],
        default='mandatory'
    )
    
    # Scope
    target_models = models.JSONField(default=list, help_text="Models covered by this policy")
    target_users = models.ManyToManyField(User, related_name='compliance_policies', blank=True)
    target_roles = models.JSONField(default=list, help_text="User roles covered")
    
    # Compliance requirements
    requires_consent = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    requires_documentation = models.BooleanField(default=False)
    
    # Review and maintenance
    review_frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annually', 'Annually'),
            ('as_needed', 'As Needed'),
        ],
        default='quarterly'
    )
    next_review_date = models.DateField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_policies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Compliance Policy"
        verbose_name_plural = "Compliance Policies"
        ordering = ['priority', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.compliance_standard})"

class DataRetentionRule(CompanyIsolatedModel):
    """Data retention rules and policies"""
    
    RETENTION_TYPES = [
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
        ('conditional', 'Conditional'),
    ]
    
    policy = models.ForeignKey(CompliancePolicy, on_delete=models.CASCADE, related_name='retention_rules')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Retention configuration
    retention_period = models.DurationField(help_text="How long to retain data")
    retention_type = models.CharField(max_length=20, choices=RETENTION_TYPES, default='automatic')
    
    # Scope
    target_model = models.CharField(max_length=100, help_text="Django model name")
    conditions = models.JSONField(default=dict, help_text="Retention conditions")
    
    # Actions
    action_on_expiry = models.CharField(
        max_length=20,
        choices=[
            ('delete', 'Delete'),
            ('archive', 'Archive'),
            ('anonymize', 'Anonymize'),
            ('encrypt', 'Encrypt'),
        ],
        default='delete'
    )
    
    # Notification
    notify_before_expiry = models.BooleanField(default=True)
    notification_days = models.IntegerField(default=30, help_text="Days before expiry to notify")
    notification_recipients = models.JSONField(default=list, help_text="Notification recipients")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_executed = models.DateTimeField(null=True, blank=True)
    next_execution = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Data Retention Rule"
        verbose_name_plural = "Data Retention Rules"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.retention_period}"

class AccessReview(CompanyIsolatedModel):
    """Access review and certification"""
    
    REVIEW_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Review configuration
    review_type = models.CharField(
        max_length=20,
        choices=[
            ('user_access', 'User Access'),
            ('data_access', 'Data Access'),
            ('permission_review', 'Permission Review'),
            ('compliance_review', 'Compliance Review'),
        ],
        default='user_access'
    )
    
    # Scope
    target_users = models.ManyToManyField(User, related_name='access_reviews', blank=True)
    target_roles = models.JSONField(default=list, help_text="Roles to review")
    target_permissions = models.JSONField(default=list, help_text="Permissions to review")
    
    # Timeline
    start_date = models.DateField()
    due_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    
    # Reviewers
    reviewers = models.ManyToManyField(User, related_name='assigned_reviews', blank=True)
    approvers = models.ManyToManyField(User, related_name='approved_reviews', blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=REVIEW_STATUS, default='pending')
    progress_percentage = models.IntegerField(default=0)
    
    # Results
    total_items = models.IntegerField(default=0)
    reviewed_items = models.IntegerField(default=0)
    approved_items = models.IntegerField(default=0)
    rejected_items = models.IntegerField(default=0)
    
    # Compliance
    compliance_policy = models.ForeignKey(CompliancePolicy, on_delete=models.CASCADE, null=True, blank=True)
    compliance_score = models.FloatField(null=True, blank=True, help_text="Compliance score (0-100)")
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_reviews')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Access Review"
        verbose_name_plural = "Access Reviews"
        ordering = ['-due_date']
    
    def __str__(self):
        return f"{self.name} - {self.review_type}"

class DataSubjectRequest(CompanyIsolatedModel):
    """Data Subject Rights (DSR) requests (GDPR, CCPA)"""
    
    REQUEST_TYPES = [
        ('access', 'Data Access'),
        ('portability', 'Data Portability'),
        ('rectification', 'Data Rectification'),
        ('erasure', 'Data Erasure'),
        ('restriction', 'Processing Restriction'),
        ('objection', 'Object to Processing'),
    ]
    
    REQUEST_STATUS = [
        ('received', 'Received'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Request details
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    subject_name = models.CharField(max_length=200)
    subject_email = models.EmailField()
    subject_phone = models.CharField(max_length=20, blank=True)
    
    # Request content
    description = models.TextField()
    specific_data = models.JSONField(default=list, help_text="Specific data requested")
    justification = models.TextField(blank=True)
    
    # Status and processing
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='received')
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='medium'
    )
    
    # Timeline
    received_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Processing
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_dsrs')
    processing_notes = models.TextField(blank=True)
    
    # Compliance
    legal_basis = models.CharField(max_length=100, blank=True)
    verification_method = models.CharField(max_length=100, blank=True)
    verification_completed = models.BooleanField(default=False)
    
    # Response
    response_data = models.JSONField(default=dict, help_text="Response data provided")
    response_method = models.CharField(max_length=100, blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Data Subject Request"
        verbose_name_plural = "Data Subject Requests"
        ordering = ['-received_date']
    
    def __str__(self):
        return f"{self.request_type} - {self.subject_name} ({self.status})"

class ComplianceViolation(CompanyIsolatedModel):
    """Compliance violations and incidents"""
    
    VIOLATION_TYPES = [
        ('policy_breach', 'Policy Breach'),
        ('data_breach', 'Data Breach'),
        ('access_violation', 'Access Violation'),
        ('retention_violation', 'Retention Violation'),
        ('consent_violation', 'Consent Violation'),
        ('security_incident', 'Security Incident'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Violation details
    violation_type = models.CharField(max_length=20, choices=VIOLATION_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    
    # Related entities
    policy = models.ForeignKey(CompliancePolicy, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='violations')
    
    # Incident details
    incident_date = models.DateTimeField()
    discovered_date = models.DateTimeField(auto_now_add=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_violations')
    
    # Impact assessment
    affected_users = models.IntegerField(default=0)
    affected_data = models.JSONField(default=list, help_text="Types of data affected")
    potential_impact = models.TextField(blank=True)
    
    # Response
    response_actions = models.JSONField(default=list, help_text="Actions taken")
    mitigation_measures = models.TextField(blank=True)
    prevention_measures = models.TextField(blank=True)
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolution_date = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Compliance
    regulatory_notification = models.BooleanField(default=False)
    notification_date = models.DateTimeField(null=True, blank=True)
    notification_authority = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Compliance Violation"
        verbose_name_plural = "Compliance Violations"
        ordering = ['-discovered_date']
    
    def __str__(self):
        return f"{self.title} - {self.severity} ({self.violation_type})"
