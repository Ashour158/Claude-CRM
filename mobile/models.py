# mobile/models.py
# Mobile Application Models

from django.db import models
from core.models import CompanyIsolatedModel, User
import uuid
import json
from datetime import datetime, timedelta

class MobileDevice(CompanyIsolatedModel):
    """Mobile device registration and management"""
    
    DEVICE_TYPES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
        ('tablet', 'Tablet'),
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
    os_version = models.CharField(max_length=50)
    app_version = models.CharField(max_length=50)
    device_model = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    
    # User Association
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mobile_devices'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending_approval'
    )
    is_trusted = models.BooleanField(default=False)
    
    # Security
    push_token = models.CharField(
        max_length=500,
        blank=True,
        help_text="Push notification token"
    )
    fingerprint = models.CharField(
        max_length=500,
        blank=True,
        help_text="Device fingerprint"
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
    
    # App Configuration
    app_config = models.JSONField(
        default=dict,
        help_text="App-specific configuration"
    )
    user_preferences = models.JSONField(
        default=dict,
        help_text="User preferences for the app"
    )
    
    class Meta:
        db_table = 'mobile_device'
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['company', 'user']),
            models.Index(fields=['company', 'device_type']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.device_name} - {self.user.get_full_name()}"

class MobileSession(CompanyIsolatedModel):
    """Mobile app sessions"""
    
    SESSION_TYPES = [
        ('app', 'App Session'),
        ('background', 'Background Session'),
        ('sync', 'Sync Session'),
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
        default='app'
    )
    
    # Device and User
    device = models.ForeignKey(
        MobileDevice,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mobile_sessions'
    )
    
    # Session Details
    app_version = models.CharField(max_length=50)
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
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Session Data
    session_data = models.JSONField(
        default=dict,
        help_text="Session-specific data"
    )
    offline_data = models.JSONField(
        default=dict,
        help_text="Offline data for sync"
    )
    
    class Meta:
        db_table = 'mobile_session'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['company', 'device']),
            models.Index(fields=['company', 'user']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.session_type}"

class OfflineData(CompanyIsolatedModel):
    """Offline data synchronization"""
    
    SYNC_TYPES = [
        ('full', 'Full Sync'),
        ('incremental', 'Incremental Sync'),
        ('selective', 'Selective Sync'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('syncing', 'Syncing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('conflict', 'Conflict'),
    ]
    
    # Basic Information
    device = models.ForeignKey(
        MobileDevice,
        on_delete=models.CASCADE,
        related_name='offline_data'
    )
    session = models.ForeignKey(
        MobileSession,
        on_delete=models.CASCADE,
        related_name='offline_data'
    )
    
    # Sync Configuration
    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPES,
        default='incremental'
    )
    entity_type = models.CharField(
        max_length=100,
        help_text="Type of entity being synced"
    )
    entity_id = models.UUIDField(help_text="ID of the entity")
    
    # Data
    data = models.JSONField(
        default=dict,
        help_text="Entity data"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Sync metadata"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    # Conflict Resolution
    has_conflict = models.BooleanField(default=False)
    conflict_data = models.JSONField(
        default=dict,
        help_text="Conflict data"
    )
    resolution_strategy = models.CharField(
        max_length=50,
        blank=True,
        help_text="Conflict resolution strategy"
    )
    
    class Meta:
        db_table = 'offline_data'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'device']),
            models.Index(fields=['company', 'entity_type', 'entity_id']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.entity_type} - {self.entity_id}"

class PushNotification(CompanyIsolatedModel):
    """Push notifications for mobile apps"""
    
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('alert', 'Alert'),
        ('reminder', 'Reminder'),
        ('update', 'Update'),
        ('marketing', 'Marketing'),
        ('system', 'System'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('failed', 'Failed'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info'
    )
    
    # Recipients
    devices = models.ManyToManyField(
        MobileDevice,
        related_name='notifications',
        help_text="Target devices"
    )
    users = models.ManyToManyField(
        User,
        related_name='notifications',
        help_text="Target users"
    )
    
    # Content
    payload = models.JSONField(
        default=dict,
        help_text="Notification payload"
    )
    action_url = models.URLField(
        blank=True,
        help_text="Action URL when notification is tapped"
    )
    
    # Scheduling
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled send time"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Notification expiration time"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'push_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'notification_type']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'scheduled_at']),
        ]
    
    def __str__(self):
        return self.title

class MobileAppConfig(CompanyIsolatedModel):
    """Mobile app configuration and settings"""
    
    CONFIG_TYPES = [
        ('general', 'General'),
        ('ui', 'UI Configuration'),
        ('features', 'Feature Flags'),
        ('api', 'API Configuration'),
        ('sync', 'Sync Configuration'),
        ('security', 'Security Settings'),
    ]
    
    # Basic Information
    config_type = models.CharField(
        max_length=20,
        choices=CONFIG_TYPES
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Configuration
    configuration = models.JSONField(
        default=dict,
        help_text="Configuration data"
    )
    version = models.CharField(max_length=50, default='1.0.0')
    
    # Targeting
    target_devices = models.JSONField(
        default=list,
        help_text="Target device types"
    )
    target_users = models.JSONField(
        default=list,
        help_text="Target user groups"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_required = models.BooleanField(default=False)
    
    # Timestamps
    effective_from = models.DateTimeField(auto_now_add=True)
    effective_until = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'mobile_app_config'
        ordering = ['config_type', 'name']
        indexes = [
            models.Index(fields=['company', 'config_type']),
            models.Index(fields=['company', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.config_type} - {self.name}"

class MobileAnalytics(CompanyIsolatedModel):
    """Mobile app analytics and usage tracking"""
    
    METRIC_TYPES = [
        ('usage', 'Usage'),
        ('performance', 'Performance'),
        ('error', 'Error'),
        ('user_engagement', 'User Engagement'),
        ('feature_usage', 'Feature Usage'),
        ('crash', 'Crash'),
    ]
    
    # Basic Information
    device = models.ForeignKey(
        MobileDevice,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    session = models.ForeignKey(
        MobileSession,
        on_delete=models.CASCADE,
        related_name='analytics',
        null=True,
        blank=True
    )
    
    # Metric Details
    metric_type = models.CharField(
        max_length=30,
        choices=METRIC_TYPES
    )
    metric_name = models.CharField(max_length=255)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=50, blank=True)
    
    # Context
    screen_name = models.CharField(max_length=255, blank=True)
    action_name = models.CharField(max_length=255, blank=True)
    user_id = models.CharField(max_length=255, blank=True)
    
    # Data
    properties = models.JSONField(
        default=dict,
        help_text="Additional metric properties"
    )
    context_data = models.JSONField(
        default=dict,
        help_text="Context data"
    )
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mobile_analytics'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company', 'device']),
            models.Index(fields=['company', 'metric_type']),
            models.Index(fields=['company', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.device_name} - {self.metric_name}"

class MobileCrash(CompanyIsolatedModel):
    """Mobile app crash reports"""
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('investigating', 'Investigating'),
        ('fixed', 'Fixed'),
        ('wont_fix', "Won't Fix"),
        ('duplicate', 'Duplicate'),
    ]
    
    # Basic Information
    device = models.ForeignKey(
        MobileDevice,
        on_delete=models.CASCADE,
        related_name='crashes'
    )
    session = models.ForeignKey(
        MobileSession,
        on_delete=models.CASCADE,
        related_name='crashes',
        null=True,
        blank=True
    )
    
    # Crash Details
    crash_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique crash identifier"
    )
    error_type = models.CharField(max_length=255)
    error_message = models.TextField()
    stack_trace = models.TextField()
    
    # Severity and Status
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_LEVELS,
        default='medium'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    
    # App Information
    app_version = models.CharField(max_length=50)
    os_version = models.CharField(max_length=50)
    device_model = models.CharField(max_length=100, blank=True)
    
    # Crash Data
    crash_data = models.JSONField(
        default=dict,
        help_text="Additional crash data"
    )
    user_actions = models.JSONField(
        default=list,
        help_text="User actions leading to crash"
    )
    
    # Resolution
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_crashes'
    )
    resolution_notes = models.TextField(blank=True)
    fixed_in_version = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'mobile_crash'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'device']),
            models.Index(fields=['company', 'severity']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.error_type} - {self.severity}"
