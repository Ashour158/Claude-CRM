# integrations/models.py
# Third-party integrations and API management models

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class APICredential(CompanyIsolatedModel):
    """API credentials for integrations"""
    
    CREDENTIAL_TYPES = [
        ('api_key', 'API Key'),
        ('oauth', 'OAuth'),
        ('basic_auth', 'Basic Auth'),
        ('bearer_token', 'Bearer Token'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    service_name = models.CharField(max_length=100, help_text="Service provider name")
    credential_type = models.CharField(
        max_length=20,
        choices=CREDENTIAL_TYPES,
        default='api_key'
    )
    
    # Credentials
    api_key = models.CharField(max_length=500, blank=True)
    api_secret = models.CharField(max_length=500, blank=True)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    username = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    
    # Configuration
    base_url = models.URLField(blank=True)
    endpoints = models.JSONField(
        default=dict,
        help_text="API endpoints configuration"
    )
    headers = models.JSONField(
        default=dict,
        help_text="Default headers"
    )
    parameters = models.JSONField(
        default=dict,
        help_text="Default parameters"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_verified = models.DateTimeField(null=True, blank=True)
    
    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True)
    auto_refresh = models.BooleanField(default=False)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_api_credentials'
    )
    
    class Meta:
        db_table = 'api_credential'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.service_name})"

class Webhook(CompanyIsolatedModel):
    """Webhook configurations"""
    
    WEBHOOK_TYPES = [
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ]
    
    HTTP_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    webhook_type = models.CharField(
        max_length=20,
        choices=WEBHOOK_TYPES,
        default='incoming'
    )
    
    # Webhook Configuration
    url = models.URLField(help_text="Webhook URL")
    method = models.CharField(
        max_length=10,
        choices=HTTP_METHODS,
        default='POST'
    )
    headers = models.JSONField(
        default=dict,
        help_text="Webhook headers"
    )
    
    # Authentication
    auth_type = models.CharField(
        max_length=20,
        choices=[
            ('none', 'None'),
            ('basic', 'Basic Auth'),
            ('bearer', 'Bearer Token'),
            ('api_key', 'API Key'),
            ('custom', 'Custom'),
        ],
        default='none'
    )
    auth_credentials = models.JSONField(
        default=dict,
        help_text="Authentication credentials"
    )
    
    # Triggers
    trigger_events = models.JSONField(
        default=list,
        help_text="Events that trigger this webhook"
    )
    trigger_conditions = models.JSONField(
        default=dict,
        help_text="Conditions for triggering"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Statistics
    total_calls = models.IntegerField(default=0)
    successful_calls = models.IntegerField(default=0)
    failed_calls = models.IntegerField(default=0)
    last_called = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_webhooks'
    )
    
    class Meta:
        db_table = 'webhook'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class WebhookLog(CompanyIsolatedModel):
    """Webhook execution logs"""
    
    webhook = models.ForeignKey(
        Webhook,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    # Request Information
    request_url = models.URLField()
    request_method = models.CharField(max_length=10)
    request_headers = models.JSONField(default=dict)
    request_body = models.TextField(blank=True)
    
    # Response Information
    response_status = models.IntegerField(null=True, blank=True)
    response_headers = models.JSONField(default=dict)
    response_body = models.TextField(blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    
    # Status
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    # Timing
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'webhook_log'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.webhook.name} - {self.started_at}"

class DataSync(CompanyIsolatedModel):
    """Data synchronization configurations"""
    
    SYNC_TYPES = [
        ('import', 'Import'),
        ('export', 'Export'),
        ('bidirectional', 'Bidirectional'),
    ]
    
    SYNC_STATUS = [
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
    source_system = models.CharField(max_length=100, help_text="Source system name")
    target_system = models.CharField(max_length=100, help_text="Target system name")
    source_credentials = models.ForeignKey(
        APICredential,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_syncs'
    )
    target_credentials = models.ForeignKey(
        APICredential,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='target_syncs'
    )
    
    # Configuration
    entity_type = models.CharField(max_length=100, help_text="Entity type to sync")
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
        choices=SYNC_STATUS,
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
        related_name='owned_data_syncs'
    )
    
    class Meta:
        db_table = 'data_sync'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.source_system} -> {self.target_system})"

class DataSyncLog(CompanyIsolatedModel):
    """Data synchronization logs"""
    
    data_sync = models.ForeignKey(
        DataSync,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    # Sync Information
    sync_started = models.DateTimeField()
    sync_completed = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Statistics
    total_records = models.IntegerField(default=0)
    synced_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    skipped_records = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='running'
    )
    
    # Error Information
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'data_sync_log'
        ordering = ['-sync_started']
    
    def __str__(self):
        return f"{self.data_sync.name} - {self.sync_started}"

class EmailIntegration(CompanyIsolatedModel):
    """Email service integrations"""
    
    EMAIL_PROVIDERS = [
        ('smtp', 'SMTP'),
        ('sendgrid', 'SendGrid'),
        ('mailgun', 'Mailgun'),
        ('ses', 'Amazon SES'),
        ('mandrill', 'Mandrill'),
        ('postmark', 'Postmark'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    provider = models.CharField(
        max_length=20,
        choices=EMAIL_PROVIDERS,
        default='smtp'
    )
    
    # SMTP Configuration
    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.IntegerField(null=True, blank=True)
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_password = models.CharField(max_length=255, blank=True)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_use_ssl = models.BooleanField(default=False)
    
    # API Configuration
    api_key = models.CharField(max_length=500, blank=True)
    api_secret = models.CharField(max_length=500, blank=True)
    api_endpoint = models.URLField(blank=True)
    
    # Settings
    from_email = models.EmailField(help_text="Default from email")
    from_name = models.CharField(max_length=255, blank=True)
    reply_to_email = models.EmailField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_verified = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)
    total_bounced = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_email_integrations'
    )
    
    class Meta:
        db_table = 'email_integration'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.provider})"

class CalendarIntegration(CompanyIsolatedModel):
    """Calendar service integrations"""
    
    CALENDAR_PROVIDERS = [
        ('google', 'Google Calendar'),
        ('outlook', 'Microsoft Outlook'),
        ('exchange', 'Microsoft Exchange'),
        ('caldav', 'CalDAV'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    provider = models.CharField(
        max_length=20,
        choices=CALENDAR_PROVIDERS,
        default='google'
    )
    
    # OAuth Configuration
    client_id = models.CharField(max_length=255, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Calendar Settings
    calendar_id = models.CharField(max_length=255, blank=True)
    calendar_name = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Sync Settings
    sync_direction = models.CharField(
        max_length=20,
        choices=[
            ('import', 'Import Only'),
            ('export', 'Export Only'),
            ('bidirectional', 'Bidirectional'),
        ],
        default='bidirectional'
    )
    sync_frequency = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
        ],
        default='hourly'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_connected = models.BooleanField(default=False)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_calendar_integrations'
    )
    
    class Meta:
        db_table = 'calendar_integration'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.provider})"