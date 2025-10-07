# marketplace/models.py
# Marketplace plugin kernel with manifest, runner, and install lifecycle

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class Plugin(models.Model):
    """Plugin definitions in the marketplace"""
    
    PLUGIN_TYPES = [
        ('integration', 'Integration'),
        ('report', 'Report Template'),
        ('widget', 'Dashboard Widget'),
        ('workflow', 'Workflow Template'),
        ('theme', 'UI Theme'),
        ('extension', 'Feature Extension'),
        ('connector', 'Data Connector'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('suspended', 'Suspended'),
        ('deprecated', 'Deprecated'),
    ]
    
    # Basic Information
    plugin_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    tagline = models.CharField(max_length=255, blank=True)
    plugin_type = models.CharField(
        max_length=50,
        choices=PLUGIN_TYPES
    )
    
    # Version Information
    version = models.CharField(max_length=50)
    changelog = models.TextField(blank=True)
    
    # Manifest
    manifest = models.JSONField(
        default=dict,
        help_text="Plugin manifest (dependencies, permissions, config)"
    )
    
    # Requirements
    min_system_version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Minimum CRM system version required"
    )
    dependencies = models.JSONField(
        default=list,
        help_text="List of required plugins"
    )
    required_permissions = models.JSONField(
        default=list,
        help_text="Permissions required by plugin"
    )
    
    # Installation
    install_script = models.TextField(
        blank=True,
        help_text="Installation script or commands"
    )
    uninstall_script = models.TextField(
        blank=True,
        help_text="Uninstallation cleanup script"
    )
    configuration_schema = models.JSONField(
        default=dict,
        help_text="Configuration options schema"
    )
    default_configuration = models.JSONField(
        default=dict,
        help_text="Default configuration values"
    )
    
    # Media
    icon_url = models.URLField(blank=True)
    screenshots = models.JSONField(
        default=list,
        help_text="List of screenshot URLs"
    )
    video_url = models.URLField(blank=True)
    
    # Developer Information
    developer_name = models.CharField(max_length=255)
    developer_email = models.EmailField()
    developer_website = models.URLField(blank=True)
    support_url = models.URLField(blank=True)
    documentation_url = models.URLField(blank=True)
    
    # Pricing
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    pricing_model = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('one_time', 'One-Time Purchase'),
            ('subscription', 'Subscription'),
            ('freemium', 'Freemium'),
        ],
        default='free'
    )
    trial_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Trial period in days"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Statistics
    install_count = models.IntegerField(default=0)
    active_installs = models.IntegerField(default=0)
    rating_average = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text="Average rating (0-5)"
    )
    rating_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Approval
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_plugins'
    )
    review_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'plugin'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['plugin_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class PluginInstallation(CompanyIsolatedModel):
    """Plugin installations for companies"""
    
    STATUS_CHOICES = [
        ('installing', 'Installing'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('updating', 'Updating'),
        ('uninstalling', 'Uninstalling'),
    ]
    
    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name='installations'
    )
    
    # Installation Details
    installation_id = models.UUIDField(default=uuid.uuid4, unique=True)
    installed_version = models.CharField(max_length=50)
    
    # Configuration
    configuration = models.JSONField(
        default=dict,
        help_text="Plugin configuration for this installation"
    )
    enabled_features = models.JSONField(
        default=list,
        help_text="List of enabled features"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='installing'
    )
    is_enabled = models.BooleanField(default=True)
    
    # Lifecycle Tracking
    installed_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    last_activated = models.DateTimeField(null=True, blank=True)
    last_deactivated = models.DateTimeField(null=True, blank=True)
    
    # Error Tracking
    error_message = models.TextField(blank=True)
    error_count = models.IntegerField(default=0)
    last_error = models.DateTimeField(null=True, blank=True)
    
    # Usage Statistics
    execution_count = models.IntegerField(default=0)
    last_execution = models.DateTimeField(null=True, blank=True)
    
    # Installation Owner
    installed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='installed_plugins'
    )
    
    class Meta:
        db_table = 'plugin_installation'
        unique_together = ('company', 'plugin')
        ordering = ['-installed_at']
    
    def __str__(self):
        return f"{self.plugin.name} - {self.company.name}"


class PluginExecution(CompanyIsolatedModel):
    """Plugin execution logs"""
    
    installation = models.ForeignKey(
        PluginInstallation,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    
    # Execution Details
    execution_id = models.UUIDField(default=uuid.uuid4)
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='triggered_plugin_executions'
    )
    trigger_type = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Manual'),
            ('scheduled', 'Scheduled'),
            ('webhook', 'Webhook'),
            ('event', 'System Event'),
            ('api', 'API Call'),
        ]
    )
    
    # Input/Output
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ]
    )
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Execution duration in milliseconds"
    )
    
    # Error Information
    error_message = models.TextField(blank=True)
    error_stack = models.TextField(blank=True)
    
    class Meta:
        db_table = 'plugin_execution'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['installation', '-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.installation.plugin.name} - {self.started_at}"


class PluginReview(CompanyIsolatedModel):
    """User reviews and ratings for plugins"""
    
    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    # Review Details
    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=255, blank=True)
    review_text = models.TextField(blank=True)
    
    # Pros/Cons
    pros = models.TextField(blank=True)
    cons = models.TextField(blank=True)
    
    # Reviewer
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='plugin_reviews'
    )
    
    # Verification
    is_verified_purchase = models.BooleanField(default=False)
    
    # Helpful Votes
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    # Developer Response
    developer_response = models.TextField(blank=True)
    developer_responded_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plugin_review'
        unique_together = ('plugin', 'reviewer', 'company')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.plugin.name} - {self.rating} stars by {self.reviewer.email}"
