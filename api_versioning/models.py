# api_versioning/models.py
# API Versioning and Management Models

from django.db import models
from core.models import CompanyIsolatedModel, User
import uuid
from datetime import datetime, timedelta

class APIVersion(CompanyIsolatedModel):
    """API version definitions and management"""
    
    VERSION_STATUS = [
        ('development', 'Development'),
        ('beta', 'Beta'),
        ('stable', 'Stable'),
        ('deprecated', 'Deprecated'),
        ('retired', 'Retired'),
    ]
    
    version = models.CharField(max_length=20, unique=True, help_text="Version number (e.g., v1.0, v2.1)")
    name = models.CharField(max_length=100, help_text="Human-readable version name")
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=VERSION_STATUS, default='development')
    
    # Version details
    release_date = models.DateField(null=True, blank=True)
    deprecation_date = models.DateField(null=True, blank=True)
    retirement_date = models.DateField(null=True, blank=True)
    
    # Configuration
    is_default = models.BooleanField(default=False, help_text="Default version for new clients")
    is_public = models.BooleanField(default=True, help_text="Publicly accessible")
    requires_auth = models.BooleanField(default=True)
    
    # Documentation
    changelog = models.TextField(blank=True)
    migration_guide = models.TextField(blank=True)
    breaking_changes = models.JSONField(default=list, help_text="List of breaking changes")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_versions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "API Version"
        verbose_name_plural = "API Versions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.version} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default version
        if self.is_default:
            APIVersion.objects.filter(company=self.company, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class APIEndpoint(CompanyIsolatedModel):
    """API endpoint versioning configuration"""
    
    HTTP_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ]
    
    version = models.ForeignKey(APIVersion, on_delete=models.CASCADE, related_name='endpoints')
    path = models.CharField(max_length=200, help_text="API endpoint path")
    method = models.CharField(max_length=10, choices=HTTP_METHODS)
    
    # Endpoint configuration
    is_active = models.BooleanField(default=True)
    is_deprecated = models.BooleanField(default=False)
    deprecation_notice = models.TextField(blank=True)
    
    # Version-specific settings
    rate_limit = models.IntegerField(null=True, blank=True, help_text="Requests per minute")
    timeout = models.IntegerField(default=30, help_text="Request timeout in seconds")
    
    # Documentation
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=list, help_text="Endpoint parameters")
    response_schema = models.JSONField(default=dict, help_text="Response schema")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "API Endpoint"
        verbose_name_plural = "API Endpoints"
        ordering = ['path', 'method']
        unique_together = ['version', 'path', 'method']
    
    def __str__(self):
        return f"{self.method} {self.path} ({self.version.version})"

class APIClient(CompanyIsolatedModel):
    """API client registration and tracking"""
    
    CLIENT_TYPES = [
        ('web', 'Web Application'),
        ('mobile', 'Mobile Application'),
        ('integration', 'Integration'),
        ('partner', 'Partner'),
        ('internal', 'Internal'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPES)
    
    # Client identification
    client_id = models.UUIDField(default=uuid.uuid4, unique=True)
    client_secret = models.CharField(max_length=255, blank=True)
    
    # Version usage
    primary_version = models.ForeignKey(APIVersion, on_delete=models.CASCADE, related_name='primary_clients')
    supported_versions = models.ManyToManyField(APIVersion, related_name='supported_clients', blank=True)
    
    # Access control
    is_active = models.BooleanField(default=True)
    rate_limit = models.IntegerField(default=1000, help_text="Requests per hour")
    
    # Contact information
    contact_email = models.EmailField(blank=True)
    contact_name = models.CharField(max_length=200, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_clients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "API Client"
        verbose_name_plural = "API Clients"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.client_type})"

class APIRequestLog(CompanyIsolatedModel):
    """API request logging and analytics"""
    
    client = models.ForeignKey(APIClient, on_delete=models.CASCADE, related_name='request_logs')
    version = models.ForeignKey(APIVersion, on_delete=models.CASCADE, related_name='request_logs')
    endpoint = models.ForeignKey(APIEndpoint, on_delete=models.CASCADE, related_name='request_logs', null=True, blank=True)
    
    # Request details
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=200)
    query_params = models.JSONField(default=dict)
    headers = models.JSONField(default=dict)
    
    # Response details
    status_code = models.IntegerField()
    response_time = models.FloatField(help_text="Response time in milliseconds")
    response_size = models.IntegerField(help_text="Response size in bytes")
    
    # Client information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    error_type = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "API Request Log"
        verbose_name_plural = "API Request Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['client', 'timestamp']),
            models.Index(fields=['version', 'timestamp']),
            models.Index(fields=['status_code', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code} ({self.timestamp})"

class APIDeprecationNotice(CompanyIsolatedModel):
    """API deprecation notices and migration guides"""
    
    version = models.ForeignKey(APIVersion, on_delete=models.CASCADE, related_name='deprecation_notices')
    endpoint = models.ForeignKey(APIEndpoint, on_delete=models.CASCADE, related_name='deprecation_notices', null=True, blank=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Deprecation timeline
    notice_date = models.DateField()
    deprecation_date = models.DateField()
    retirement_date = models.DateField()
    
    # Migration information
    migration_guide = models.TextField(blank=True)
    alternative_endpoints = models.JSONField(default=list, help_text="Alternative endpoints")
    
    # Impact assessment
    affected_clients = models.ManyToManyField(APIClient, related_name='deprecation_notices', blank=True)
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    acknowledged_by = models.ManyToManyField(User, related_name='acknowledged_deprecations', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "API Deprecation Notice"
        verbose_name_plural = "API Deprecation Notices"
        ordering = ['-deprecation_date']
    
    def __str__(self):
        return f"{self.title} - {self.version.version}"
