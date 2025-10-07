# compliance/models.py
# Security and compliance models

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel, Company
import uuid
import json

User = get_user_model()


class CompliancePolicy(CompanyIsolatedModel):
    """Policy-as-Code configuration"""
    
    POLICY_TYPES = [
        ('gdpr', 'GDPR'),
        ('ccpa', 'CCPA'),
        ('soc2', 'SOC2'),
        ('hipaa', 'HIPAA'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    policy_type = models.CharField(
        max_length=20,
        choices=POLICY_TYPES,
        default='custom'
    )
    
    # Policy Configuration (YAML stored as JSON)
    policy_config = models.JSONField(
        default=dict,
        help_text="Policy configuration in YAML format"
    )
    
    # Version Control
    version = models.CharField(max_length=50, default='1.0.0')
    previous_version_id = models.UUIDField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Enforcement
    is_enforced = models.BooleanField(default=False)
    enforcement_level = models.CharField(
        max_length=20,
        choices=[
            ('soft', 'Soft (Warnings Only)'),
            ('hard', 'Hard (Blocking)'),
        ],
        default='soft'
    )
    
    # Metadata
    applied_at = models.DateTimeField(null=True, blank=True)
    applied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='applied_policies'
    )
    
    class Meta:
        db_table = 'compliance_policy'
        ordering = ['-created_at']
        verbose_name_plural = 'Compliance Policies'
    
    def __str__(self):
        return f"{self.name} (v{self.version})"


class PolicyAuditLog(CompanyIsolatedModel):
    """Audit log for policy changes and enforcement"""
    
    ACTION_TYPES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('applied', 'Applied'),
        ('rollback', 'Rollback'),
        ('validated', 'Validated'),
        ('violation', 'Violation Detected'),
    ]
    
    policy = models.ForeignKey(
        CompliancePolicy,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    action_details = models.JSONField(default=dict)
    
    # Impact Analysis
    entities_affected = models.JSONField(
        default=list,
        help_text="List of entity types affected"
    )
    records_affected = models.IntegerField(default=0)
    
    # User Info
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    
    # Additional Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'policy_audit_log'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.policy.name} - {self.created_at}"


class DataResidency(CompanyIsolatedModel):
    """Data residency configuration for compliance"""
    
    REGION_CHOICES = [
        ('us-east-1', 'US East (N. Virginia)'),
        ('us-west-2', 'US West (Oregon)'),
        ('eu-west-1', 'EU (Ireland)'),
        ('eu-central-1', 'EU (Frankfurt)'),
        ('ap-southeast-1', 'Asia Pacific (Singapore)'),
        ('ap-northeast-1', 'Asia Pacific (Tokyo)'),
        ('ca-central-1', 'Canada (Central)'),
        ('sa-east-1', 'South America (São Paulo)'),
    ]
    
    # Region Configuration
    primary_region = models.CharField(
        max_length=50,
        choices=REGION_CHOICES,
        help_text="Primary data storage region"
    )
    
    allowed_regions = models.JSONField(
        default=list,
        help_text="List of allowed regions for data replication"
    )
    
    # Storage Configuration
    storage_prefix = models.CharField(
        max_length=255,
        help_text="S3 bucket prefix for region-specific storage"
    )
    
    bucket_name = models.CharField(max_length=255, blank=True)
    
    # Enforcement
    enforce_region = models.BooleanField(
        default=True,
        help_text="Enforce regional data residency"
    )
    
    block_cross_region = models.BooleanField(
        default=True,
        help_text="Block cross-region data transfers"
    )
    
    # Compliance
    compliance_frameworks = models.JSONField(
        default=list,
        help_text="List of compliance frameworks requiring this configuration"
    )
    
    class Meta:
        db_table = 'data_residency'
        ordering = ['-created_at']
        verbose_name_plural = 'Data Residencies'
    
    def __str__(self):
        return f"{self.company.name} - {self.primary_region}"


class DataSubjectRequest(CompanyIsolatedModel):
    """Data Subject Rights (DSR) requests (GDPR, CCPA)"""
    
    REQUEST_TYPES = [
        ('access', 'Right to Access'),
        ('rectification', 'Right to Rectification'),
        ('erasure', 'Right to Erasure'),
        ('portability', 'Right to Data Portability'),
        ('restriction', 'Right to Restriction'),
        ('objection', 'Right to Object'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Request Information
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    request_id = models.CharField(max_length=100, unique=True, editable=False)
    
    # Subject Information
    subject_email = models.EmailField()
    subject_name = models.CharField(max_length=255, blank=True)
    subject_phone = models.CharField(max_length=50, blank=True)
    
    # Request Details
    description = models.TextField(blank=True)
    entities_affected = models.JSONField(
        default=list,
        help_text="List of entity types to process"
    )
    
    # Processing Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Execution Details
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_dsr_requests'
    )
    
    # Audit Trail
    audit_data = models.JSONField(
        default=dict,
        help_text="Detailed audit trail of deletion/modification"
    )
    
    # Rollback Support
    can_rollback = models.BooleanField(default=True)
    rollback_data = models.JSONField(
        default=dict,
        help_text="Data snapshot for rollback"
    )
    
    # Compliance
    due_date = models.DateTimeField(
        help_text="Legal deadline for completion (typically 30 days)"
    )
    
    class Meta:
        db_table = 'data_subject_request'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.request_id} - {self.request_type} - {self.subject_email}"
    
    def save(self, *args, **kwargs):
        if not self.request_id:
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            self.request_id = f"DSR-{timestamp}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class SecretVault(CompanyIsolatedModel):
    """Central secrets vault for integrations"""
    
    SECRET_TYPES = [
        ('api_key', 'API Key'),
        ('access_token', 'Access Token'),
        ('refresh_token', 'Refresh Token'),
        ('certificate', 'Certificate'),
        ('private_key', 'Private Key'),
        ('password', 'Password'),
        ('custom', 'Custom'),
    ]
    
    # Secret Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    secret_type = models.CharField(
        max_length=20,
        choices=SECRET_TYPES,
        default='api_key'
    )
    
    # Encrypted Secret
    secret_value = models.TextField(
        help_text="Encrypted secret value"
    )
    
    # KMS Configuration
    kms_key_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="KMS key ID for encryption"
    )
    
    encryption_algorithm = models.CharField(
        max_length=50,
        default='AES256',
        help_text="Encryption algorithm used"
    )
    
    # Rotation
    rotation_enabled = models.BooleanField(default=False)
    rotation_days = models.IntegerField(
        default=90,
        help_text="Days between automatic rotations"
    )
    last_rotated = models.DateTimeField(null=True, blank=True)
    next_rotation = models.DateTimeField(null=True, blank=True)
    
    # Access Control
    allowed_services = models.JSONField(
        default=list,
        help_text="List of services allowed to access this secret"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_secrets'
    )
    
    class Meta:
        db_table = 'secret_vault'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.secret_type})"


class SecretAccessLog(CompanyIsolatedModel):
    """Audit log for secret access"""
    
    secret = models.ForeignKey(
        SecretVault,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    
    # Access Information
    accessed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    
    service_name = models.CharField(
        max_length=255,
        help_text="Service that accessed the secret"
    )
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Success/Failure
    success = models.BooleanField(default=True)
    failure_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'secret_access_log'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.secret.name} - {self.accessed_by} - {self.created_at}"


class AccessReview(CompanyIsolatedModel):
    """Automated access review records"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    # Review Information
    review_id = models.CharField(max_length=100, unique=True, editable=False)
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Statistics
    total_users_reviewed = models.IntegerField(default=0)
    stale_access_found = models.IntegerField(default=0)
    access_revoked = models.IntegerField(default=0)
    
    # Review Data
    review_data = models.JSONField(
        default=dict,
        help_text="Detailed review findings"
    )
    
    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='conducted_reviews'
    )
    
    class Meta:
        db_table = 'access_review'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.review_id} - {self.review_period_start} to {self.review_period_end}"
    
    def save(self, *args, **kwargs):
        if not self.review_id:
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d')
            self.review_id = f"AR-{timestamp}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class StaleAccess(CompanyIsolatedModel):
    """Stale access flagged during reviews"""
    
    access_review = models.ForeignKey(
        AccessReview,
        on_delete=models.CASCADE,
        related_name='stale_accesses'
    )
    
    # User Information
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stale_accesses'
    )
    
    # Access Details
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=255)
    last_accessed = models.DateTimeField(null=True, blank=True)
    days_inactive = models.IntegerField()
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolution = models.CharField(
        max_length=20,
        choices=[
            ('revoked', 'Access Revoked'),
            ('retained', 'Access Retained'),
            ('pending', 'Pending Decision'),
        ],
        default='pending'
    )
    
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resolved_stale_accesses'
    )
    
    class Meta:
        db_table = 'stale_access'
        ordering = ['-days_inactive']
    
    def __str__(self):
        return f"{self.user.email} - {self.resource_type} - {self.days_inactive} days"


class RetentionPolicy(CompanyIsolatedModel):
    """Data retention policies"""
    
    # Policy Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Entity Configuration
    entity_type = models.CharField(
        max_length=100,
        help_text="Model name (e.g., 'Lead', 'Contact', 'Deal')"
    )
    
    # Retention Rules
    retention_days = models.IntegerField(
        help_text="Number of days to retain data"
    )
    
    # Deletion Configuration
    deletion_method = models.CharField(
        max_length=20,
        choices=[
            ('soft', 'Soft Delete (Mark as deleted)'),
            ('hard', 'Hard Delete (Physical removal)'),
            ('archive', 'Archive (Move to cold storage)'),
        ],
        default='soft'
    )
    
    # Filters
    filter_conditions = models.JSONField(
        default=dict,
        help_text="Conditions to identify records for retention"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Execution
    last_executed = models.DateTimeField(null=True, blank=True)
    next_execution = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'retention_policy'
        ordering = ['entity_type', 'name']
        verbose_name_plural = 'Retention Policies'
    
    def __str__(self):
        return f"{self.name} - {self.entity_type} ({self.retention_days} days)"


class RetentionLog(CompanyIsolatedModel):
    """Log of retention policy executions"""
    
    policy = models.ForeignKey(
        RetentionPolicy,
        on_delete=models.CASCADE,
        related_name='execution_logs'
    )
    
    # Execution Details
    execution_started = models.DateTimeField(auto_now_add=True)
    execution_completed = models.DateTimeField(null=True, blank=True)
    
    # Results
    records_processed = models.IntegerField(default=0)
    records_deleted = models.IntegerField(default=0)
    records_archived = models.IntegerField(default=0)
    errors_encountered = models.IntegerField(default=0)
    
    # Details
    execution_details = models.JSONField(
        default=dict,
        help_text="Detailed execution log"
    )
    
    # Compliance
    compliance_log = models.JSONField(
        default=dict,
        help_text="Compliance information for audit"
    )
    
    class Meta:
        db_table = 'retention_log'
        ordering = ['-execution_started']
    
    def __str__(self):
        return f"{self.policy.name} - {self.execution_started}"
