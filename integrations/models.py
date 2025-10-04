# integrations/models.py
from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class Integration(CompanyIsolatedModel):
    """
    Third-party integrations
    """
    INTEGRATION_TYPES = [
        ('email', 'Email Service'),
        ('calendar', 'Calendar'),
        ('crm', 'CRM System'),
        ('marketing', 'Marketing Platform'),
        ('analytics', 'Analytics'),
        ('storage', 'File Storage'),
        ('payment', 'Payment Gateway'),
        ('communication', 'Communication'),
        ('social', 'Social Media'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('pending', 'Pending'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Integration name")
    integration_type = models.CharField(
        max_length=20,
        choices=INTEGRATION_TYPES,
        help_text="Type of integration"
    )
    provider = models.CharField(max_length=100, help_text="Integration provider")
    description = models.TextField(blank=True, help_text="Integration description")
    
    # Configuration
    api_endpoint = models.URLField(blank=True, help_text="API endpoint URL")
    api_key = models.CharField(max_length=500, blank=True, help_text="API key")
    api_secret = models.CharField(max_length=500, blank=True, help_text="API secret")
    webhook_url = models.URLField(blank=True, help_text="Webhook URL")
    
    # Settings
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Integration-specific settings"
    )
    credentials = models.JSONField(
        default=dict,
        blank=True,
        help_text="Encrypted credentials"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_active = models.BooleanField(default=True)
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_integrations',
        help_text="Integration owner"
    )
    
    # Additional Information
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last synchronization time"
    )
    sync_frequency = models.PositiveIntegerField(
        default=3600,
        help_text="Sync frequency in seconds"
    )
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.get_integration_type_display()})"

class EmailIntegration(CompanyIsolatedModel):
    """
    Email service integrations
    """
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
    name = models.CharField(max_length=255, help_text="Email integration name")
    provider = models.CharField(
        max_length=20,
        choices=EMAIL_PROVIDERS,
        help_text="Email provider"
    )
    
    # SMTP Configuration
    smtp_host = models.CharField(max_length=255, blank=True, help_text="SMTP host")
    smtp_port = models.PositiveIntegerField(default=587, help_text="SMTP port")
    smtp_username = models.CharField(max_length=255, blank=True, help_text="SMTP username")
    smtp_password = models.CharField(max_length=255, blank=True, help_text="SMTP password")
    smtp_use_tls = models.BooleanField(default=True, help_text="Use TLS")
    smtp_use_ssl = models.BooleanField(default=False, help_text="Use SSL")
    
    # API Configuration
    api_key = models.CharField(max_length=500, blank=True, help_text="API key")
    api_secret = models.CharField(max_length=500, blank=True, help_text="API secret")
    api_url = models.URLField(blank=True, help_text="API URL")
    
    # Settings
    from_email = models.EmailField(help_text="Default from email")
    from_name = models.CharField(max_length=255, help_text="Default from name")
    reply_to_email = models.EmailField(blank=True, help_text="Reply-to email")
    
    # Rate Limiting
    rate_limit_per_hour = models.PositiveIntegerField(
        default=1000,
        help_text="Rate limit per hour"
    )
    rate_limit_per_day = models.PositiveIntegerField(
        default=10000,
        help_text="Rate limit per day"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_email_integrations',
        help_text="Integration owner"
    )
    
    # Statistics
    emails_sent = models.PositiveIntegerField(default=0, help_text="Total emails sent")
    emails_delivered = models.PositiveIntegerField(default=0, help_text="Total emails delivered")
    emails_bounced = models.PositiveIntegerField(default=0, help_text="Total emails bounced")
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_display()})"

class CalendarIntegration(CompanyIsolatedModel):
    """
    Calendar service integrations
    """
    CALENDAR_PROVIDERS = [
        ('google', 'Google Calendar'),
        ('outlook', 'Microsoft Outlook'),
        ('apple', 'Apple Calendar'),
        ('caldav', 'CalDAV'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Calendar integration name")
    provider = models.CharField(
        max_length=20,
        choices=CALENDAR_PROVIDERS,
        help_text="Calendar provider"
    )
    
    # OAuth Configuration
    client_id = models.CharField(max_length=500, blank=True, help_text="OAuth client ID")
    client_secret = models.CharField(max_length=500, blank=True, help_text="OAuth client secret")
    redirect_uri = models.URLField(blank=True, help_text="OAuth redirect URI")
    access_token = models.TextField(blank=True, help_text="OAuth access token")
    refresh_token = models.TextField(blank=True, help_text="OAuth refresh token")
    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Token expiration time"
    )
    
    # Calendar Settings
    calendar_id = models.CharField(max_length=255, blank=True, help_text="Calendar ID")
    calendar_name = models.CharField(max_length=255, blank=True, help_text="Calendar name")
    timezone = models.CharField(max_length=50, default='UTC', help_text="Calendar timezone")
    
    # Sync Settings
    sync_events = models.BooleanField(default=True, help_text="Sync events")
    sync_tasks = models.BooleanField(default=True, help_text="Sync tasks")
    sync_contacts = models.BooleanField(default=False, help_text="Sync contacts")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_connected = models.BooleanField(default=False)
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_calendar_integrations',
        help_text="Integration owner"
    )
    
    # Statistics
    events_synced = models.PositiveIntegerField(default=0, help_text="Total events synced")
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last synchronization time"
    )
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_display()})"

class Webhook(CompanyIsolatedModel):
    """
    Webhook configurations
    """
    WEBHOOK_TYPES = [
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ]
    
    HTTP_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Webhook name")
    webhook_type = models.CharField(
        max_length=20,
        choices=WEBHOOK_TYPES,
        help_text="Type of webhook"
    )
    url = models.URLField(help_text="Webhook URL")
    http_method = models.CharField(
        max_length=10,
        choices=HTTP_METHODS,
        default='POST',
        help_text="HTTP method"
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
        default='none',
        help_text="Authentication type"
    )
    auth_username = models.CharField(max_length=255, blank=True, help_text="Auth username")
    auth_password = models.CharField(max_length=255, blank=True, help_text="Auth password")
    auth_token = models.CharField(max_length=500, blank=True, help_text="Auth token")
    auth_header = models.CharField(max_length=255, blank=True, help_text="Auth header name")
    
    # Configuration
    headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom headers"
    )
    payload_template = models.TextField(blank=True, help_text="Payload template")
    
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
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_webhooks',
        help_text="Webhook owner"
    )
    
    # Statistics
    total_calls = models.PositiveIntegerField(default=0, help_text="Total webhook calls")
    successful_calls = models.PositiveIntegerField(default=0, help_text="Successful calls")
    failed_calls = models.PositiveIntegerField(default=0, help_text="Failed calls")
    last_called = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last webhook call time"
    )
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.get_webhook_type_display()})"

class WebhookLog(CompanyIsolatedModel):
    """
    Webhook execution logs
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
        ('retrying', 'Retrying'),
    ]
    
    # Basic Information
    webhook = models.ForeignKey(
        Webhook,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Execution status"
    )
    
    # Request Details
    request_url = models.URLField(help_text="Request URL")
    request_method = models.CharField(max_length=10, help_text="Request method")
    request_headers = models.JSONField(
        default=dict,
        help_text="Request headers"
    )
    request_payload = models.TextField(help_text="Request payload")
    
    # Response Details
    response_status_code = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Response status code"
    )
    response_headers = models.JSONField(
        default=dict,
        help_text="Response headers"
    )
    response_body = models.TextField(blank=True, help_text="Response body")
    
    # Execution Details
    execution_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Execution time in seconds"
    )
    error_message = models.TextField(blank=True, help_text="Error message")
    retry_count = models.PositiveIntegerField(default=0, help_text="Number of retries")
    
    # Context
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_webhooks'
    )
    object_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of object that triggered the webhook"
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of object that triggered the webhook"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'webhook']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.webhook.name} - {self.status}"

class APICredential(CompanyIsolatedModel):
    """
    API credentials for third-party services
    """
    CREDENTIAL_TYPES = [
        ('api_key', 'API Key'),
        ('oauth', 'OAuth'),
        ('basic_auth', 'Basic Auth'),
        ('bearer_token', 'Bearer Token'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Credential name")
    service = models.CharField(max_length=100, help_text="Service name")
    credential_type = models.CharField(
        max_length=20,
        choices=CREDENTIAL_TYPES,
        help_text="Type of credential"
    )
    
    # Credentials
    api_key = models.CharField(max_length=500, blank=True, help_text="API key")
    api_secret = models.CharField(max_length=500, blank=True, help_text="API secret")
    access_token = models.TextField(blank=True, help_text="Access token")
    refresh_token = models.TextField(blank=True, help_text="Refresh token")
    username = models.CharField(max_length=255, blank=True, help_text="Username")
    password = models.CharField(max_length=255, blank=True, help_text="Password")
    
    # OAuth Configuration
    client_id = models.CharField(max_length=500, blank=True, help_text="OAuth client ID")
    client_secret = models.CharField(max_length=500, blank=True, help_text="OAuth client secret")
    redirect_uri = models.URLField(blank=True, help_text="OAuth redirect URI")
    scope = models.TextField(blank=True, help_text="OAuth scope")
    
    # Additional Configuration
    base_url = models.URLField(blank=True, help_text="Base API URL")
    headers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional headers"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_api_credentials',
        help_text="Credential owner"
    )
    
    # Expiration
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Credential expiration time"
    )
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.service})"

class DataSync(CompanyIsolatedModel):
    """
    Data synchronization between systems
    """
    SYNC_TYPES = [
        ('one_way', 'One Way'),
        ('two_way', 'Two Way'),
        ('real_time', 'Real Time'),
    ]
    
    SYNC_STATUS = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('error', 'Error'),
        ('completed', 'Completed'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Sync name")
    description = models.TextField(blank=True, help_text="Sync description")
    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPES,
        help_text="Type of synchronization"
    )
    
    # Source and Target
    source_system = models.CharField(max_length=100, help_text="Source system")
    target_system = models.CharField(max_length=100, help_text="Target system")
    source_endpoint = models.URLField(help_text="Source endpoint")
    target_endpoint = models.URLField(help_text="Target endpoint")
    
    # Configuration
    sync_frequency = models.PositiveIntegerField(
        default=3600,
        help_text="Sync frequency in seconds"
    )
    batch_size = models.PositiveIntegerField(
        default=100,
        help_text="Batch size for sync"
    )
    sync_conditions = models.JSONField(
        default=dict,
        help_text="Sync conditions"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS,
        default='active'
    )
    is_active = models.BooleanField(default=True)
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_data_syncs',
        help_text="Sync owner"
    )
    
    # Statistics
    total_records_synced = models.PositiveIntegerField(default=0)
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last synchronization time"
    )
    next_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Next synchronization time"
    )
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.source_system} -> {self.target_system})"
