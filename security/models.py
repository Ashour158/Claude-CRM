# security/models.py
# Enterprise Security Models

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.models import CompanyIsolatedModel, User
import uuid
import json
from datetime import datetime, timedelta

class SecurityPolicy(CompanyIsolatedModel):
    """Security policies and configurations"""
    
    POLICY_TYPES = [
        ('password', 'Password Policy'),
        ('session', 'Session Policy'),
        ('ip_restriction', 'IP Restriction'),
        ('device_management', 'Device Management'),
        ('data_retention', 'Data Retention'),
        ('audit_logging', 'Audit Logging'),
        ('encryption', 'Encryption'),
        ('backup', 'Backup Policy'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('draft', 'Draft'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    policy_type = models.CharField(
        max_length=30,
        choices=POLICY_TYPES
    )
    
    # Policy Configuration
    configuration = models.JSONField(
        default=dict,
        help_text="Policy-specific configuration"
    )
    rules = models.JSONField(
        default=list,
        help_text="Policy rules and conditions"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_active = models.BooleanField(default=True)
    
    # Enforcement
    enforcement_level = models.CharField(
        max_length=20,
        choices=[
            ('advisory', 'Advisory'),
            ('warning', 'Warning'),
            ('blocking', 'Blocking'),
        ],
        default='advisory'
    )
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_policies'
    )
    
    class Meta:
        db_table = 'security_policy'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class SSOConfiguration(CompanyIsolatedModel):
    """SSO/SAML configuration"""
    
    PROVIDER_TYPES = [
        ('saml', 'SAML'),
        ('oauth2', 'OAuth 2.0'),
        ('oidc', 'OpenID Connect'),
        ('ldap', 'LDAP'),
        ('active_directory', 'Active Directory'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('testing', 'Testing'),
        ('error', 'Error'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    provider_type = models.CharField(
        max_length=30,
        choices=PROVIDER_TYPES
    )
    
    # Configuration
    configuration = models.JSONField(
        default=dict,
        help_text="SSO provider configuration"
    )
    credentials = models.JSONField(
        default=dict,
        help_text="Encrypted credentials"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='inactive'
    )
    is_active = models.BooleanField(default=True)
    
    # Testing
    last_test = models.DateTimeField(null=True, blank=True)
    test_status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('not_tested', 'Not Tested'),
        ],
        default='not_tested'
    )
    
    class Meta:
        db_table = 'sso_configuration'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class SCIMConfiguration(CompanyIsolatedModel):
    """SCIM (System for Cross-domain Identity Management) configuration"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # SCIM Configuration
    endpoint_url = models.URLField(help_text="SCIM endpoint URL")
    bearer_token = models.CharField(
        max_length=500,
        help_text="Bearer token for authentication"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='inactive'
    )
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_syncs = models.IntegerField(default=0)
    successful_syncs = models.IntegerField(default=0)
    failed_syncs = models.IntegerField(default=0)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'scim_configuration'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class IPAllowlist(CompanyIsolatedModel):
    """IP address allowlist for security"""
    
    ALLOWLIST_TYPES = [
        ('whitelist', 'Whitelist'),
        ('blacklist', 'Blacklist'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    allowlist_type = models.CharField(
        max_length=20,
        choices=ALLOWLIST_TYPES,
        default='whitelist'
    )
    
    # IP Configuration
    ip_addresses = models.JSONField(
        default=list,
        help_text="List of IP addresses or CIDR blocks"
    )
    countries = models.JSONField(
        default=list,
        help_text="List of allowed/blocked countries"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_requests = models.IntegerField(default=0)
    blocked_requests = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'ip_allowlist'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class DeviceManagement(CompanyIsolatedModel):
    """Device management and tracking"""
    
    DEVICE_TYPES = [
        ('desktop', 'Desktop'),
        ('laptop', 'Laptop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
        ('pending_approval', 'Pending Approval'),
    ]
    
    # Basic Information
    device_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique device identifier"
    )
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPES
    )
    
    # Device Details
    operating_system = models.CharField(max_length=100)
    browser = models.CharField(max_length=100, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField()
    
    # User Association
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='devices'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending_approval'
    )
    is_trusted = models.BooleanField(default=False)
    
    # Security
    fingerprint = models.CharField(
        max_length=500,
        blank=True,
        help_text="Device fingerprint for identification"
    )
    encryption_key = models.CharField(
        max_length=500,
        blank=True,
        help_text="Device encryption key"
    )
    
    # Activity Tracking
    last_seen = models.DateTimeField(null=True, blank=True)
    total_sessions = models.IntegerField(default=0)
    last_ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'device_management'
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['company', 'user']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'device_id']),
        ]
    
    def __str__(self):
        return f"{self.device_name} - {self.user.get_full_name()}"

class SessionManagement(CompanyIsolatedModel):
    """Session management and tracking"""
    
    SESSION_TYPES = [
        ('web', 'Web Session'),
        ('mobile', 'Mobile Session'),
        ('api', 'API Session'),
        ('sso', 'SSO Session'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('suspended', 'Suspended'),
    ]
    
    # Basic Information
    session_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique session identifier"
    )
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPES,
        default='web'
    )
    
    # User and Device
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    device = models.ForeignKey(
        DeviceManagement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions'
    )
    
    # Session Details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    location = models.JSONField(
        default=dict,
        help_text="Geographic location information"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    terminated_at = models.DateTimeField(null=True, blank=True)
    
    # Security
    is_secure = models.BooleanField(default=True)
    encryption_key = models.CharField(
        max_length=500,
        blank=True,
        help_text="Session encryption key"
    )
    
    class Meta:
        db_table = 'session_management'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['company', 'user']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'session_id']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.session_type}"

class AuditLog(CompanyIsolatedModel):
    """Audit logging for security events"""
    
    EVENT_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('permission_change', 'Permission Change'),
        ('data_access', 'Data Access'),
        ('data_modification', 'Data Modification'),
        ('security_event', 'Security Event'),
        ('system_event', 'System Event'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Basic Information
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPES
    )
    event_name = models.CharField(max_length=255)
    description = models.TextField()
    
    # User and Session
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    session = models.ForeignKey(
        SessionManagement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    # Event Details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location = models.JSONField(
        default=dict,
        help_text="Geographic location"
    )
    
    # Severity and Status
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='medium'
    )
    is_successful = models.BooleanField(default=True)
    
    # Event Data
    event_data = models.JSONField(
        default=dict,
        help_text="Additional event data"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Event metadata"
    )
    
    # Related Entity (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Type of related entity"
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the related entity"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        db_table = 'audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'event_type']),
            models.Index(fields=['company', 'user']),
            models.Index(fields=['company', 'severity']),
            models.Index(fields=['company', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_name} - {self.user.get_full_name() if self.user else 'System'}"

class SecurityIncident(CompanyIsolatedModel):
    """Security incidents and alerts"""
    
    INCIDENT_TYPES = [
        ('unauthorized_access', 'Unauthorized Access'),
        ('data_breach', 'Data Breach'),
        ('malware', 'Malware'),
        ('phishing', 'Phishing'),
        ('ddos', 'DDoS Attack'),
        ('insider_threat', 'Insider Threat'),
        ('policy_violation', 'Policy Violation'),
        ('other', 'Other'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('contained', 'Contained'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    # Basic Information
    incident_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique incident identifier"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    incident_type = models.CharField(
        max_length=30,
        choices=INCIDENT_TYPES
    )
    
    # Severity and Status
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='medium'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    
    # Incident Details
    affected_users = models.ManyToManyField(
        User,
        related_name='security_incidents',
        blank=True
    )
    affected_systems = models.JSONField(
        default=list,
        help_text="List of affected systems"
    )
    
    # Investigation
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents'
    )
    investigation_notes = models.TextField(blank=True)
    
    # Timestamps
    detected_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Impact Assessment
    impact_assessment = models.JSONField(
        default=dict,
        help_text="Impact assessment data"
    )
    remediation_actions = models.JSONField(
        default=list,
        help_text="Remediation actions taken"
    )
    
    class Meta:
        db_table = 'security_incident'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['company', 'incident_type']),
            models.Index(fields=['company', 'severity']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'assigned_to']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.severity}"

class DataRetentionPolicy(CompanyIsolatedModel):
    """Data retention policies"""
    
    RETENTION_TYPES = [
        ('user_data', 'User Data'),
        ('audit_logs', 'Audit Logs'),
        ('conversations', 'Conversations'),
        ('files', 'Files'),
        ('backups', 'Backups'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    retention_type = models.CharField(
        max_length=30,
        choices=RETENTION_TYPES
    )
    
    # Retention Configuration
    retention_period_days = models.IntegerField(
        help_text="Retention period in days"
    )
    auto_delete = models.BooleanField(
        default=False,
        help_text="Automatically delete after retention period"
    )
    archive_before_delete = models.BooleanField(
        default=True,
        help_text="Archive data before deletion"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_records = models.IntegerField(default=0)
    deleted_records = models.IntegerField(default=0)
    last_cleanup = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'data_retention_policy'
        ordering = ['name']
    
    def __str__(self):
        return self.name
