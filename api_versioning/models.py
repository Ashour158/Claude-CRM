# api_versioning/models.py
# Backward-compatible API versioning models

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel

User = get_user_model()

class APIVersion(models.Model):
    """API version definitions"""
    
    STATUS_CHOICES = [
        ('development', 'Development'),
        ('beta', 'Beta'),
        ('stable', 'Stable'),
        ('deprecated', 'Deprecated'),
        ('sunset', 'Sunset'),
    ]
    
    # Version Information
    version_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Version number (e.g., 'v1', 'v2', '2023-10-01')"
    )
    version_name = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='development'
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Default version if not specified"
    )
    is_active = models.BooleanField(default=True)
    
    # Release Information
    release_date = models.DateField(null=True, blank=True)
    deprecation_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this version will be deprecated"
    )
    sunset_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this version will be removed"
    )
    
    # Changelog
    changelog = models.TextField(
        blank=True,
        help_text="Changes in this version"
    )
    breaking_changes = models.TextField(
        blank=True,
        help_text="Breaking changes from previous version"
    )
    migration_guide = models.TextField(
        blank=True,
        help_text="Guide for migrating from previous version"
    )
    
    # Statistics
    request_count = models.IntegerField(default=0)
    active_clients = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'api_version'
        ordering = ['-version_number']
    
    def __str__(self):
        return f"API {self.version_number} ({self.status})"


class APIEndpoint(models.Model):
    """API endpoint version mappings"""
    
    # Endpoint Information
    path = models.CharField(max_length=255)
    method = models.CharField(
        max_length=10,
        choices=[
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('PUT', 'PUT'),
            ('PATCH', 'PATCH'),
            ('DELETE', 'DELETE'),
        ]
    )
    api_version = models.ForeignKey(
        APIVersion,
        on_delete=models.CASCADE,
        related_name='endpoints'
    )
    
    # Serializer Configuration
    serializer_class = models.CharField(
        max_length=255,
        help_text="Fully qualified serializer class name"
    )
    queryset_filters = models.JSONField(
        default=dict,
        help_text="Default queryset filters for this version"
    )
    
    # Behavior Changes
    field_mappings = models.JSONField(
        default=dict,
        help_text="Field name mappings from standard to this version"
    )
    deprecated_fields = models.JSONField(
        default=list,
        help_text="Fields deprecated in this version"
    )
    new_fields = models.JSONField(
        default=list,
        help_text="Fields added in this version"
    )
    
    # Documentation
    description = models.TextField(blank=True)
    request_example = models.TextField(blank=True)
    response_example = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'api_endpoint'
        unique_together = ('path', 'method', 'api_version')
        ordering = ['path', 'method']
    
    def __str__(self):
        return f"{self.method} {self.path} ({self.api_version.version_number})"


class APIClient(CompanyIsolatedModel):
    """API client registrations"""
    
    # Client Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    client_id = models.CharField(max_length=100, unique=True)
    
    # Version Preferences
    preferred_version = models.ForeignKey(
        APIVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preferred_by_clients'
    )
    supported_versions = models.ManyToManyField(
        APIVersion,
        blank=True,
        related_name='supporting_clients'
    )
    
    # Client Details
    client_type = models.CharField(
        max_length=50,
        choices=[
            ('web', 'Web Application'),
            ('mobile', 'Mobile Application'),
            ('integration', 'Integration'),
            ('internal', 'Internal Service'),
            ('third_party', 'Third Party'),
        ],
        default='web'
    )
    
    # Contact Information
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_requests = models.IntegerField(default=0)
    last_request = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_api_clients'
    )
    
    class Meta:
        db_table = 'api_client'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.client_id})"


class APIRequestLog(CompanyIsolatedModel):
    """API request logging for version tracking"""
    
    # Request Information
    api_version = models.ForeignKey(
        APIVersion,
        on_delete=models.SET_NULL,
        null=True,
        related_name='request_logs'
    )
    api_client = models.ForeignKey(
        APIClient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='request_logs'
    )
    
    # Request Details
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    version_header = models.CharField(
        max_length=50,
        blank=True,
        help_text="Accept-Version header value"
    )
    
    # Response
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField(help_text="Response time in milliseconds")
    
    # User
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='api_requests'
    )
    
    # Metadata
    user_agent = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'api_request_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['api_version', 'timestamp']),
            models.Index(fields=['api_client', 'timestamp']),
            models.Index(fields=['path', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code}"
