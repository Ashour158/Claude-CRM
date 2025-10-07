# marketplace/models.py
# Marketplace and Extensibility Models

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import CompanyIsolatedModel, User
import uuid
import json
from datetime import datetime, timedelta

class MarketplaceApp(CompanyIsolatedModel):
    """Marketplace applications and plugins"""
    
    APP_TYPES = [
        ('integration', 'Integration'),
        ('workflow', 'Workflow'),
        ('report', 'Report'),
        ('dashboard', 'Dashboard'),
        ('automation', 'Automation'),
        ('connector', 'Connector'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
        ('deprecated', 'Deprecated'),
    ]
    
    # Basic Information
    app_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique app identifier"
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    short_description = models.CharField(max_length=500)
    app_type = models.CharField(
        max_length=20,
        choices=APP_TYPES
    )
    
    # Version Information
    version = models.CharField(max_length=50, default='1.0.0')
    latest_version = models.CharField(max_length=50, default='1.0.0')
    is_latest = models.BooleanField(default=True)
    
    # Developer Information
    developer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='developed_apps'
    )
    developer_name = models.CharField(max_length=255)
    developer_email = models.EmailField()
    developer_website = models.URLField(blank=True)
    
    # App Configuration
    manifest = models.JSONField(
        default=dict,
        help_text="App manifest configuration"
    )
    permissions = models.JSONField(
        default=list,
        help_text="Required permissions"
    )
    dependencies = models.JSONField(
        default=list,
        help_text="App dependencies"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_public = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # Pricing
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Statistics
    download_count = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    review_count = models.IntegerField(default=0)
    install_count = models.IntegerField(default=0)
    
    # Files
    app_file = models.FileField(
        upload_to='marketplace/apps/',
        null=True,
        blank=True,
        help_text="App package file"
    )
    icon = models.ImageField(
        upload_to='marketplace/icons/',
        null=True,
        blank=True
    )
    screenshots = models.JSONField(
        default=list,
        help_text="App screenshots"
    )
    
    # Security
    is_verified = models.BooleanField(default=False)
    security_scan_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
            ('warning', 'Warning'),
        ],
        default='pending'
    )
    
    class Meta:
        db_table = 'marketplace_app'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'app_type']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'is_public']),
            models.Index(fields=['company', 'developer']),
        ]
    
    def __str__(self):
        return self.name

class AppInstallation(CompanyIsolatedModel):
    """App installations by companies"""
    
    STATUS_CHOICES = [
        ('installing', 'Installing'),
        ('installed', 'Installed'),
        ('failed', 'Failed'),
        ('uninstalling', 'Uninstalling'),
        ('uninstalled', 'Uninstalled'),
    ]
    
    # Basic Information
    app = models.ForeignKey(
        MarketplaceApp,
        on_delete=models.CASCADE,
        related_name='installations'
    )
    installed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='app_installations'
    )
    
    # Installation Details
    version = models.CharField(max_length=50)
    installation_config = models.JSONField(
        default=dict,
        help_text="Installation configuration"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='installing'
    )
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    installed_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    uninstalled_at = models.DateTimeField(null=True, blank=True)
    
    # Usage Statistics
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'app_installation'
        ordering = ['-installed_at']
        indexes = [
            models.Index(fields=['company', 'app']),
            models.Index(fields=['company', 'installed_by']),
            models.Index(fields=['company', 'status']),
        ]
        unique_together = ['company', 'app']
    
    def __str__(self):
        return f"{self.app.name} - {self.installed_by.get_full_name()}"

class AppReview(CompanyIsolatedModel):
    """App reviews and ratings"""
    
    # Basic Information
    app = models.ForeignKey(
        MarketplaceApp,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='app_reviews'
    )
    
    # Review Content
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    # Helpfulness
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'app_review'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'app']),
            models.Index(fields=['company', 'reviewer']),
        ]
        unique_together = ['company', 'app', 'reviewer']
    
    def __str__(self):
        return f"{self.app.name} - {self.rating} stars"

class AppPermission(CompanyIsolatedModel):
    """App permission requests and grants"""
    
    PERMISSION_TYPES = [
        ('read', 'Read'),
        ('write', 'Write'),
        ('delete', 'Delete'),
        ('admin', 'Admin'),
        ('api', 'API Access'),
        ('file_access', 'File Access'),
        ('user_data', 'User Data'),
        ('company_data', 'Company Data'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('revoked', 'Revoked'),
    ]
    
    # Basic Information
    app = models.ForeignKey(
        MarketplaceApp,
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='permission_requests'
    )
    
    # Permission Details
    permission_type = models.CharField(
        max_length=20,
        choices=PERMISSION_TYPES
    )
    resource = models.CharField(
        max_length=255,
        help_text="Resource the permission applies to"
    )
    scope = models.JSONField(
        default=dict,
        help_text="Permission scope and conditions"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_permissions'
    )
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Usage Tracking
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'app_permission'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['company', 'app']),
            models.Index(fields=['company', 'requested_by']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.app.name} - {self.permission_type}"

class AppWebhook(CompanyIsolatedModel):
    """App webhooks for real-time integration"""
    
    WEBHOOK_TYPES = [
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ]
    
    # Basic Information
    app = models.ForeignKey(
        MarketplaceApp,
        on_delete=models.CASCADE,
        related_name='webhooks'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    webhook_type = models.CharField(
        max_length=20,
        choices=WEBHOOK_TYPES
    )
    
    # Webhook Configuration
    endpoint_url = models.URLField(help_text="Webhook endpoint URL")
    events = models.JSONField(
        default=list,
        help_text="Events to trigger webhook"
    )
    headers = models.JSONField(
        default=dict,
        help_text="Custom headers"
    )
    secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="Webhook secret for verification"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_calls = models.IntegerField(default=0)
    successful_calls = models.IntegerField(default=0)
    failed_calls = models.IntegerField(default=0)
    last_called = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'app_webhook'
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'app']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.app.name} - {self.name}"

class AppExecution(CompanyIsolatedModel):
    """App execution tracking and monitoring"""
    
    EXECUTION_TYPES = [
        ('scheduled', 'Scheduled'),
        ('manual', 'Manual'),
        ('triggered', 'Triggered'),
        ('webhook', 'Webhook'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    app = models.ForeignKey(
        MarketplaceApp,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    installation = models.ForeignKey(
        AppInstallation,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    execution_type = models.CharField(
        max_length=20,
        choices=EXECUTION_TYPES,
        default='manual'
    )
    
    # Execution Details
    function_name = models.CharField(
        max_length=255,
        help_text="Function or method being executed"
    )
    parameters = models.JSONField(
        default=dict,
        help_text="Execution parameters"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Execution duration in milliseconds"
    )
    
    # Results
    result_data = models.JSONField(
        default=dict,
        help_text="Execution result data"
    )
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)
    
    # Resource Usage
    memory_usage = models.IntegerField(
        null=True,
        blank=True,
        help_text="Memory usage in MB"
    )
    cpu_usage = models.FloatField(
        null=True,
        blank=True,
        help_text="CPU usage percentage"
    )
    
    class Meta:
        db_table = 'app_execution'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'app']),
            models.Index(fields=['company', 'installation']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.app.name} - {self.function_name}"

class AppAnalytics(CompanyIsolatedModel):
    """App analytics and usage statistics"""
    
    METRIC_TYPES = [
        ('usage', 'Usage'),
        ('performance', 'Performance'),
        ('error', 'Error'),
        ('user_engagement', 'User Engagement'),
        ('revenue', 'Revenue'),
    ]
    
    # Basic Information
    app = models.ForeignKey(
        MarketplaceApp,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    metric_type = models.CharField(
        max_length=30,
        choices=METRIC_TYPES
    )
    metric_name = models.CharField(max_length=255)
    
    # Metric Data
    value = models.FloatField(help_text="Metric value")
    unit = models.CharField(
        max_length=50,
        blank=True,
        help_text="Metric unit"
    )
    dimensions = models.JSONField(
        default=dict,
        help_text="Metric dimensions"
    )
    
    # Time Period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metric metadata"
    )
    
    class Meta:
        db_table = 'app_analytics'
        ordering = ['-period_end']
        indexes = [
            models.Index(fields=['company', 'app']),
            models.Index(fields=['company', 'metric_type']),
            models.Index(fields=['company', 'period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.app.name} - {self.metric_name}"

class AppSubscription(CompanyIsolatedModel):
    """App subscription management"""
    
    SUBSCRIPTION_TYPES = [
        ('free', 'Free'),
        ('trial', 'Trial'),
        ('paid', 'Paid'),
        ('enterprise', 'Enterprise'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    # Basic Information
    app = models.ForeignKey(
        MarketplaceApp,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='app_subscriptions'
    )
    
    # Subscription Details
    subscription_type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TYPES,
        default='free'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    currency = models.CharField(max_length=3, default='USD')
    billing_cycle = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
            ('one_time', 'One Time'),
        ],
        default='monthly'
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Usage Limits
    usage_limits = models.JSONField(
        default=dict,
        help_text="Subscription usage limits"
    )
    current_usage = models.JSONField(
        default=dict,
        help_text="Current usage statistics"
    )
    
    class Meta:
        db_table = 'app_subscription'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['company', 'app']),
            models.Index(fields=['company', 'subscriber']),
            models.Index(fields=['company', 'status']),
        ]
        unique_together = ['company', 'app', 'subscriber']
    
    def __str__(self):
        return f"{self.app.name} - {self.subscriber.get_full_name()}"
