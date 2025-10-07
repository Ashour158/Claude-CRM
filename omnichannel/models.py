# omnichannel/models.py
# Omnichannel Communication Models

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import CompanyIsolatedModel, User
import uuid
import json

class CommunicationChannel(CompanyIsolatedModel):
    """Communication channels configuration"""
    
    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('sms', 'SMS'),
        ('chat', 'Chat'),
        ('social_media', 'Social Media'),
        ('web_form', 'Web Form'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
        ('error', 'Error'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    channel_type = models.CharField(
        max_length=20,
        choices=CHANNEL_TYPES
    )
    description = models.TextField(blank=True)
    
    # Channel Configuration
    configuration = models.JSONField(
        default=dict,
        help_text="Channel-specific configuration"
    )
    credentials = models.JSONField(
        default=dict,
        help_text="Encrypted credentials for the channel"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    is_active = models.BooleanField(default=True)
    
    # SLA Configuration
    response_time_sla = models.IntegerField(
        default=60,
        help_text="Response time SLA in minutes"
    )
    resolution_time_sla = models.IntegerField(
        default=240,
        help_text="Resolution time SLA in minutes"
    )
    
    # Statistics
    total_conversations = models.IntegerField(default=0)
    active_conversations = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    customer_satisfaction = models.FloatField(default=0.0)
    
    class Meta:
        db_table = 'communication_channel'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Conversation(CompanyIsolatedModel):
    """Omnichannel conversations"""
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic Information
    conversation_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique conversation identifier"
    )
    subject = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    
    # Channel Information
    channel = models.ForeignKey(
        CommunicationChannel,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="External system conversation ID"
    )
    
    # Participants
    customer = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='customer_conversations',
        help_text="Customer in the conversation"
    )
    assigned_agent = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_conversations',
        help_text="Assigned agent"
    )
    
    # Status and Priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='medium'
    )
    
    # SLA Tracking
    sla_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="SLA deadline"
    )
    first_response_time = models.IntegerField(
        null=True,
        blank=True,
        help_text="First response time in minutes"
    )
    resolution_time = models.IntegerField(
        null=True,
        blank=True,
        help_text="Resolution time in minutes"
    )
    
    # Metadata
    tags = models.JSONField(
        default=list,
        help_text="Conversation tags"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata"
    )
    
    # Timestamps
    last_activity = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last activity timestamp"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Resolution timestamp"
    )
    
    class Meta:
        db_table = 'conversation'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'channel']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'assigned_agent']),
            models.Index(fields=['company', 'conversation_id']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.channel.name}"

class Message(CompanyIsolatedModel):
    """Individual messages in conversations"""
    
    MESSAGE_TYPES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
        ('system', 'System'),
        ('auto_reply', 'Auto Reply'),
    ]
    
    DIRECTION_CHOICES = [
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ]
    
    # Basic Information
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='inbound'
    )
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES
    )
    
    # Content
    content = models.TextField()
    content_type = models.CharField(
        max_length=50,
        default='text/plain',
        help_text="MIME type of content"
    )
    
    # Sender and Recipient
    sender = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    
    # External References
    external_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="External system message ID"
    )
    thread_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Thread ID for email conversations"
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Attachments
    attachments = models.JSONField(
        default=list,
        help_text="Message attachments"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Message metadata"
    )
    
    class Meta:
        db_table = 'message'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['company', 'conversation']),
            models.Index(fields=['company', 'sender']),
            models.Index(fields=['company', 'recipient']),
        ]
    
    def __str__(self):
        return f"{self.sender.get_full_name()} - {self.content[:50]}"

class ConversationTemplate(CompanyIsolatedModel):
    """Templates for common conversation responses"""
    
    TEMPLATE_TYPES = [
        ('greeting', 'Greeting'),
        ('closing', 'Closing'),
        ('escalation', 'Escalation'),
        ('follow_up', 'Follow Up'),
        ('auto_reply', 'Auto Reply'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPES,
        default='custom'
    )
    
    # Template Content
    subject_template = models.CharField(
        max_length=500,
        blank=True,
        help_text="Subject template with variables"
    )
    content_template = models.TextField(
        help_text="Content template with variables"
    )
    
    # Variables
    variables = models.JSONField(
        default=list,
        help_text="Available template variables"
    )
    
    # Channel Association
    channels = models.ManyToManyField(
        CommunicationChannel,
        related_name='templates',
        help_text="Channels this template can be used on"
    )
    
    # Usage Statistics
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(
        default=False,
        help_text="Available to all users"
    )
    
    # Owner
    owner = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_templates'
    )
    
    class Meta:
        db_table = 'conversation_template'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ConversationRule(CompanyIsolatedModel):
    """Automation rules for conversations"""
    
    RULE_TYPES = [
        ('auto_assign', 'Auto Assign'),
        ('auto_reply', 'Auto Reply'),
        ('escalation', 'Escalation'),
        ('tagging', 'Auto Tagging'),
        ('routing', 'Routing'),
        ('sla_alert', 'SLA Alert'),
    ]
    
    TRIGGER_CONDITIONS = [
        ('new_conversation', 'New Conversation'),
        ('keyword_match', 'Keyword Match'),
        ('sla_breach', 'SLA Breach'),
        ('priority_change', 'Priority Change'),
        ('channel_change', 'Channel Change'),
        ('time_based', 'Time Based'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPES
    )
    trigger_condition = models.CharField(
        max_length=20,
        choices=TRIGGER_CONDITIONS
    )
    
    # Rule Configuration
    conditions = models.JSONField(
        default=dict,
        help_text="Rule conditions"
    )
    actions = models.JSONField(
        default=dict,
        help_text="Rule actions"
    )
    
    # Channel Association
    channels = models.ManyToManyField(
        CommunicationChannel,
        related_name='rules',
        help_text="Channels this rule applies to"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(
        default=0,
        help_text="Rule priority (higher = more important)"
    )
    
    # Statistics
    execution_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'conversation_rule'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return self.name

class ConversationMetric(CompanyIsolatedModel):
    """Conversation metrics and KPIs"""
    
    METRIC_TYPES = [
        ('response_time', 'Response Time'),
        ('resolution_time', 'Resolution Time'),
        ('customer_satisfaction', 'Customer Satisfaction'),
        ('conversation_volume', 'Conversation Volume'),
        ('channel_performance', 'Channel Performance'),
        ('agent_performance', 'Agent Performance'),
    ]
    
    # Basic Information
    metric_type = models.CharField(
        max_length=30,
        choices=METRIC_TYPES
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Metric Configuration
    calculation_method = models.CharField(
        max_length=100,
        help_text="Method for calculating the metric"
    )
    aggregation_period = models.CharField(
        max_length=20,
        default='daily',
        help_text="Aggregation period (daily, weekly, monthly)"
    )
    
    # Filters
    filters = models.JSONField(
        default=dict,
        help_text="Filters for the metric"
    )
    
    # Target Values
    target_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Target value for the metric"
    )
    warning_threshold = models.FloatField(
        null=True,
        blank=True,
        help_text="Warning threshold"
    )
    critical_threshold = models.FloatField(
        null=True,
        blank=True,
        help_text="Critical threshold"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'conversation_metric'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ConversationAnalytics(CompanyIsolatedModel):
    """Conversation analytics and insights"""
    
    # Basic Information
    metric = models.ForeignKey(
        ConversationMetric,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Values
    current_value = models.FloatField()
    previous_value = models.FloatField(null=True, blank=True)
    target_value = models.FloatField(null=True, blank=True)
    
    # Trends
    trend_direction = models.CharField(
        max_length=10,
        choices=[
            ('up', 'Up'),
            ('down', 'Down'),
            ('stable', 'Stable'),
        ]
    )
    trend_percentage = models.FloatField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('good', 'Good'),
            ('warning', 'Warning'),
            ('critical', 'Critical'),
        ],
        default='good'
    )
    
    # Insights
    insights = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    class Meta:
        db_table = 'conversation_analytics'
        ordering = ['-period_end']
        indexes = [
            models.Index(fields=['company', 'metric']),
            models.Index(fields=['company', 'period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.metric.name} - {self.period_start.date()}"
