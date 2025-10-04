# system_config/models.py
from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class CustomField(CompanyIsolatedModel):
    """
    Custom fields for various models
    """
    FIELD_TYPES = [
        ('text', 'Text'),
        ('textarea', 'Text Area'),
        ('number', 'Number'),
        ('decimal', 'Decimal'),
        ('boolean', 'Boolean'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('time', 'Time'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('phone', 'Phone'),
        ('select', 'Select'),
        ('multiselect', 'Multi-Select'),
        ('radio', 'Radio'),
        ('checkbox', 'Checkbox'),
        ('file', 'File'),
        ('image', 'Image'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Field name")
    label = models.CharField(max_length=255, help_text="Display label")
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPES,
        help_text="Field type"
    )
    description = models.TextField(blank=True, help_text="Field description")
    
    # Field Configuration
    model_name = models.CharField(
        max_length=100,
        help_text="Model this field belongs to (e.g., 'Contact', 'Account')"
    )
    is_required = models.BooleanField(default=False, help_text="Is field required?")
    is_unique = models.BooleanField(default=False, help_text="Is field unique?")
    default_value = models.TextField(blank=True, help_text="Default value")
    
    # Field Options (for select, radio, checkbox fields)
    options = models.JSONField(
        default=list,
        blank=True,
        help_text="Options for select/radio/checkbox fields"
    )
    
    # Validation
    min_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum length for text fields"
    )
    max_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum length for text fields"
    )
    min_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum value for number fields"
    )
    max_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum value for number fields"
    )
    
    # Display Configuration
    sequence = models.PositiveIntegerField(default=0, help_text="Display order")
    is_visible = models.BooleanField(default=True, help_text="Is field visible?")
    help_text = models.TextField(blank=True, help_text="Help text for users")
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_custom_fields',
        help_text="Field owner"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['model_name', 'sequence']
        unique_together = ('company', 'model_name', 'name')
    
    def __str__(self):
        return f"{self.model_name}.{self.name} ({self.get_field_type_display()})"

class CustomFieldValue(CompanyIsolatedModel):
    """
    Values for custom fields
    """
    field = models.ForeignKey(
        CustomField,
        on_delete=models.CASCADE,
        related_name='values'
    )
    object_id = models.UUIDField(help_text="ID of the object this value belongs to")
    value = models.TextField(help_text="Field value")
    
    class Meta:
        unique_together = ('field', 'object_id')
        ordering = ['field__sequence']
    
    def __str__(self):
        return f"{self.field.name}: {self.value}"

class SystemPreference(CompanyIsolatedModel):
    """
    System preferences and settings
    """
    PREFERENCE_CATEGORIES = [
        ('general', 'General'),
        ('email', 'Email'),
        ('security', 'Security'),
        ('integration', 'Integration'),
        ('notification', 'Notification'),
        ('workflow', 'Workflow'),
        ('reporting', 'Reporting'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    key = models.CharField(max_length=255, help_text="Preference key")
    value = models.TextField(help_text="Preference value")
    category = models.CharField(
        max_length=20,
        choices=PREFERENCE_CATEGORIES,
        default='general'
    )
    description = models.TextField(blank=True, help_text="Preference description")
    
    # Data Type
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
        ],
        default='string'
    )
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_preferences',
        help_text="Preference owner"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['category', 'key']
        unique_together = ('company', 'key')
    
    def __str__(self):
        return f"{self.key} = {self.value}"

class WorkflowConfiguration(CompanyIsolatedModel):
    """
    Workflow configuration and settings
    """
    WORKFLOW_TYPES = [
        ('lead_qualification', 'Lead Qualification'),
        ('deal_approval', 'Deal Approval'),
        ('task_assignment', 'Task Assignment'),
        ('email_sequence', 'Email Sequence'),
        ('notification', 'Notification'),
        ('data_sync', 'Data Synchronization'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Workflow name")
    description = models.TextField(blank=True, help_text="Workflow description")
    workflow_type = models.CharField(
        max_length=20,
        choices=WORKFLOW_TYPES,
        help_text="Type of workflow"
    )
    
    # Configuration
    trigger_model = models.CharField(
        max_length=100,
        help_text="Model that triggers this workflow"
    )
    trigger_conditions = models.JSONField(
        default=dict,
        help_text="Conditions that trigger the workflow"
    )
    actions = models.JSONField(
        default=list,
        help_text="Actions to perform when triggered"
    )
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_workflows',
        help_text="Workflow owner"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.get_workflow_type_display()})"

class UserPreference(CompanyIsolatedModel):
    """
    User-specific preferences
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    key = models.CharField(max_length=255, help_text="Preference key")
    value = models.TextField(help_text="Preference value")
    category = models.CharField(
        max_length=50,
        default='user',
        help_text="Preference category"
    )
    
    class Meta:
        unique_together = ('user', 'key')
        ordering = ['category', 'key']
    
    def __str__(self):
        return f"{self.user.email}: {self.key} = {self.value}"

class SystemLog(CompanyIsolatedModel):
    """
    System logs and events
    """
    LOG_LEVELS = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    LOG_CATEGORIES = [
        ('system', 'System'),
        ('user', 'User'),
        ('security', 'Security'),
        ('integration', 'Integration'),
        ('workflow', 'Workflow'),
        ('email', 'Email'),
        ('api', 'API'),
        ('database', 'Database'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    level = models.CharField(
        max_length=20,
        choices=LOG_LEVELS,
        help_text="Log level"
    )
    category = models.CharField(
        max_length=20,
        choices=LOG_CATEGORIES,
        help_text="Log category"
    )
    message = models.TextField(help_text="Log message")
    
    # Context
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_logs'
    )
    object_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of object related to this log"
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of object related to this log"
    )
    
    # Additional Data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional log data"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'level']),
            models.Index(fields=['company', 'category']),
            models.Index(fields=['company', 'user']),
            models.Index(fields=['company', 'created_at']),
        ]
    
    def __str__(self):
        return f"[{self.level}] {self.message}"

class SystemHealth(CompanyIsolatedModel):
    """
    System health monitoring
    """
    COMPONENT_TYPES = [
        ('database', 'Database'),
        ('cache', 'Cache'),
        ('email', 'Email Service'),
        ('storage', 'File Storage'),
        ('api', 'API Gateway'),
        ('worker', 'Background Worker'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    # Basic Information
    component = models.CharField(
        max_length=20,
        choices=COMPONENT_TYPES,
        help_text="System component"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        help_text="Component status"
    )
    message = models.TextField(help_text="Status message")
    
    # Metrics
    response_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Response time in milliseconds"
    )
    memory_usage = models.FloatField(
        null=True,
        blank=True,
        help_text="Memory usage in MB"
    )
    cpu_usage = models.FloatField(
        null=True,
        blank=True,
        help_text="CPU usage percentage"
    )
    
    # Additional Data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional health data"
    )
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('company', 'component')
    
    def __str__(self):
        return f"{self.component}: {self.status}"

class DataBackup(CompanyIsolatedModel):
    """
    Data backup configuration and history
    """
    BACKUP_TYPES = [
        ('full', 'Full Backup'),
        ('incremental', 'Incremental Backup'),
        ('differential', 'Differential Backup'),
    ]
    
    BACKUP_STATUS = [
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Backup name")
    description = models.TextField(blank=True, help_text="Backup description")
    backup_type = models.CharField(
        max_length=20,
        choices=BACKUP_TYPES,
        help_text="Type of backup"
    )
    status = models.CharField(
        max_length=20,
        choices=BACKUP_STATUS,
        default='scheduled'
    )
    
    # Schedule
    scheduled_at = models.DateTimeField(
        help_text="Scheduled backup time"
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual start time"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Completion time"
    )
    
    # Backup Details
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to backup file"
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Backup file size in bytes"
    )
    
    # Assignment
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_backups'
    )
    
    # Additional Information
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional backup data"
    )
    
    class Meta:
        ordering = ['-scheduled_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'scheduled_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_backup_type_display()})"
