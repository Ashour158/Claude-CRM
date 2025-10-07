# events/models.py
# Event-Driven Architecture Models

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import CompanyIsolatedModel, User
import uuid
import json

class EventType(CompanyIsolatedModel):
    """Event type definitions"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('system', 'System'),
            ('business', 'Business'),
            ('user', 'User'),
            ('integration', 'Integration'),
        ],
        default='business'
    )
    
    # Event Schema
    schema = models.JSONField(
        default=dict,
        help_text="JSON schema for event data"
    )
    
    # Configuration
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(
        default=False,
        help_text="Available to all companies"
    )
    
    # Statistics
    total_events = models.IntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'event_type'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Event(CompanyIsolatedModel):
    """Event instances"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    event_type = models.ForeignKey(
        EventType,
        on_delete=models.CASCADE,
        related_name='events'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Event Data
    data = models.JSONField(
        default=dict,
        help_text="Event payload data"
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
    
    # Status and Processing
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    priority = models.IntegerField(
        default=0,
        help_text="Event priority (higher = more important)"
    )
    
    # Processing Information
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_events'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Processing duration in milliseconds"
    )
    
    # Error Handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Correlation
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
        help_text="Correlation ID for related events"
    )
    parent_event = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='child_events'
    )
    
    class Meta:
        db_table = 'event'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'event_type']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'priority']),
            models.Index(fields=['company', 'correlation_id']),
            models.Index(fields=['company', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.status}"

class EventHandler(CompanyIsolatedModel):
    """Event handlers and processors"""
    
    HANDLER_TYPES = [
        ('webhook', 'Webhook'),
        ('email', 'Email'),
        ('notification', 'Notification'),
        ('workflow', 'Workflow'),
        ('integration', 'Integration'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    handler_type = models.CharField(
        max_length=20,
        choices=HANDLER_TYPES,
        default='custom'
    )
    
    # Event Configuration
    event_types = models.ManyToManyField(
        EventType,
        related_name='handlers',
        help_text="Event types this handler processes"
    )
    conditions = models.JSONField(
        default=dict,
        help_text="Conditions for handler execution"
    )
    
    # Handler Configuration
    endpoint_url = models.URLField(
        blank=True,
        help_text="Webhook endpoint URL"
    )
    handler_function = models.CharField(
        max_length=255,
        blank=True,
        help_text="Python function name for custom handlers"
    )
    configuration = models.JSONField(
        default=dict,
        help_text="Handler-specific configuration"
    )
    
    # Execution Settings
    is_async = models.BooleanField(
        default=True,
        help_text="Execute handler asynchronously"
    )
    timeout_seconds = models.IntegerField(
        default=30,
        help_text="Handler execution timeout"
    )
    retry_on_failure = models.BooleanField(default=True)
    max_retries = models.IntegerField(default=3)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_executions = models.IntegerField(default=0)
    successful_executions = models.IntegerField(default=0)
    failed_executions = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_handlers'
    )
    
    class Meta:
        db_table = 'event_handler'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def success_rate(self):
        """Calculate handler success rate"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100

class EventExecution(CompanyIsolatedModel):
    """Event handler execution records"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]
    
    # Basic Information
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    handler = models.ForeignKey(
        EventHandler,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    
    # Execution Details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
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
        help_text="Handler execution result"
    )
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)
    
    # Retry Information
    retry_count = models.IntegerField(default=0)
    is_retry = models.BooleanField(default=False)
    parent_execution = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='retry_executions'
    )
    
    class Meta:
        db_table = 'event_execution'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'event']),
            models.Index(fields=['company', 'handler']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.handler.name} - {self.event.name}"

class EventSubscription(CompanyIsolatedModel):
    """Event subscriptions for real-time updates"""
    
    SUBSCRIPTION_TYPES = [
        ('websocket', 'WebSocket'),
        ('webhook', 'Webhook'),
        ('email', 'Email'),
        ('notification', 'Notification'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    subscription_type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TYPES,
        default='websocket'
    )
    
    # Event Configuration
    event_types = models.ManyToManyField(
        EventType,
        related_name='subscriptions',
        help_text="Event types to subscribe to"
    )
    filters = models.JSONField(
        default=dict,
        help_text="Event filters for subscription"
    )
    
    # Subscription Configuration
    endpoint_url = models.URLField(
        blank=True,
        help_text="Webhook endpoint URL"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_subscriptions'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_events = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'event_subscription'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class EventStream(CompanyIsolatedModel):
    """Event stream for real-time event processing"""
    
    STREAM_TYPES = [
        ('realtime', 'Real-time'),
        ('batch', 'Batch'),
        ('hybrid', 'Hybrid'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    stream_type = models.CharField(
        max_length=20,
        choices=STREAM_TYPES,
        default='realtime'
    )
    
    # Stream Configuration
    event_types = models.ManyToManyField(
        EventType,
        related_name='streams',
        help_text="Event types in this stream"
    )
    filters = models.JSONField(
        default=dict,
        help_text="Stream filters"
    )
    buffer_size = models.IntegerField(
        default=1000,
        help_text="Stream buffer size"
    )
    flush_interval = models.IntegerField(
        default=60,
        help_text="Flush interval in seconds"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_processing = models.BooleanField(default=False)
    last_processed = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_events = models.IntegerField(default=0)
    processed_events = models.IntegerField(default=0)
    failed_events = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'event_stream'
        ordering = ['name']
    
    def __str__(self):
        return self.name
