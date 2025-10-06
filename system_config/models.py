# system_config/models.py
# System configuration and settings models

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class SystemSetting(CompanyIsolatedModel):
    """System-wide settings"""
    
    SETTING_TYPES = [
        ('general', 'General'),
        ('email', 'Email'),
        ('security', 'Security'),
        ('integration', 'Integration'),
        ('notification', 'Notification'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    key = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    setting_type = models.CharField(
        max_length=20,
        choices=SETTING_TYPES,
        default='general'
    )
    
    # Setting Value
    value = models.TextField(blank=True)
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
            ('email', 'Email'),
            ('url', 'URL'),
        ],
        default='string'
    )
    
    # Validation
    is_required = models.BooleanField(default=False)
    validation_rules = models.JSONField(
        default=dict,
        help_text="Validation rules for the setting"
    )
    
    # Access Control
    is_public = models.BooleanField(default=False)
    is_editable = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'system_setting'
        ordering = ['setting_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.key})"

class CustomField(CompanyIsolatedModel):
    """Custom fields for entities"""
    
    FIELD_TYPES = [
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('number', 'Number'),
        ('decimal', 'Decimal'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('boolean', 'Boolean'),
        ('choice', 'Choice'),
        ('multichoice', 'Multi Choice'),
        ('url', 'URL'),
        ('email', 'Email'),
        ('phone', 'Phone'),
    ]
    
    ENTITY_TYPES = [
        ('account', 'Account'),
        ('contact', 'Contact'),
        ('lead', 'Lead'),
        ('deal', 'Deal'),
        ('product', 'Product'),
        ('campaign', 'Campaign'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPES,
        default='text'
    )
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPES
    )
    
    # Field Configuration
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    default_value = models.TextField(blank=True)
    choices = models.JSONField(
        default=list,
        help_text="Choices for choice/multichoice fields"
    )
    validation_rules = models.JSONField(
        default=dict,
        help_text="Field validation rules"
    )
    
    # Display Settings
    display_order = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    help_text = models.TextField(blank=True)
    
    # Access Control
    is_editable = models.BooleanField(default=True)
    is_searchable = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'custom_field'
        ordering = ['entity_type', 'display_order']
        unique_together = ('company', 'name', 'entity_type')
    
    def __str__(self):
        return f"{self.label} ({self.entity_type})"

class WorkflowRule(CompanyIsolatedModel):
    """Workflow automation rules"""
    
    RULE_TYPES = [
        ('trigger', 'Trigger'),
        ('condition', 'Condition'),
        ('action', 'Action'),
    ]
    
    TRIGGER_TYPES = [
        ('create', 'Record Created'),
        ('update', 'Record Updated'),
        ('delete', 'Record Deleted'),
        ('field_change', 'Field Changed'),
        ('status_change', 'Status Changed'),
        ('date_reached', 'Date Reached'),
        ('email_received', 'Email Received'),
        ('webhook', 'Webhook'),
    ]
    
    ACTION_TYPES = [
        ('send_email', 'Send Email'),
        ('create_task', 'Create Task'),
        ('update_field', 'Update Field'),
        ('change_status', 'Change Status'),
        ('assign_user', 'Assign User'),
        ('send_notification', 'Send Notification'),
        ('create_record', 'Create Record'),
        ('webhook', 'Webhook'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPES,
        default='trigger'
    )
    
    # Rule Configuration
    entity_type = models.CharField(
        max_length=50,
        help_text="Entity type this rule applies to"
    )
    trigger_type = models.CharField(
        max_length=20,
        choices=TRIGGER_TYPES,
        blank=True
    )
    conditions = models.JSONField(
        default=dict,
        help_text="Rule conditions"
    )
    actions = models.JSONField(
        default=list,
        help_text="Rule actions"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_global = models.BooleanField(
        default=False,
        help_text="Apply to all companies"
    )
    
    # Execution
    execution_count = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_workflow_rules'
    )
    
    class Meta:
        db_table = 'workflow_rule'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class NotificationTemplate(CompanyIsolatedModel):
    """Notification templates"""
    
    TEMPLATE_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPES,
        default='email'
    )
    
    # Template Content
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    html_body = models.TextField(blank=True)
    
    # Template Settings
    is_active = models.BooleanField(default=True)
    is_global = models.BooleanField(
        default=False,
        help_text="Available to all companies"
    )
    
    # Variables
    variables = models.JSONField(
        default=list,
        help_text="Available template variables"
    )
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_notification_templates'
    )
    
    class Meta:
        db_table = 'notification_template'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class UserPreference(CompanyIsolatedModel):
    """User preferences and settings"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    
    # Dashboard Preferences
    dashboard_layout = models.JSONField(
        default=dict,
        help_text="Dashboard layout configuration"
    )
    default_dashboard = models.CharField(
        max_length=100,
        blank=True,
        help_text="Default dashboard ID"
    )
    
    # Display Preferences
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Light'),
            ('dark', 'Dark'),
            ('auto', 'Auto'),
        ],
        default='light'
    )
    language = models.CharField(
        max_length=10,
        default='en',
        help_text="User language preference"
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="User timezone"
    )
    date_format = models.CharField(
        max_length=20,
        default='MM/DD/YYYY',
        help_text="Date format preference"
    )
    time_format = models.CharField(
        max_length=10,
        choices=[
            ('12', '12 Hour'),
            ('24', '24 Hour'),
        ],
        default='12'
    )
    
    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Notification Settings
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('never', 'Never'),
        ],
        default='immediate'
    )
    
    # Custom Preferences
    custom_preferences = models.JSONField(
        default=dict,
        help_text="Custom user preferences"
    )
    
    class Meta:
        db_table = 'user_preference'
        unique_together = ('user', 'company')
    
    def __str__(self):
        return f"{self.user.email} - Preferences"
