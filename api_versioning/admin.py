# api_versioning/admin.py
# Admin configuration for API versioning module

from django.contrib import admin
from .models import APIVersion, APIEndpoint, APIClient, APIRequestLog

@admin.register(APIVersion)
class APIVersionAdmin(admin.ModelAdmin):
    list_display = ['version_number', 'version_name', 'status', 'is_default', 'is_active', 
                   'release_date', 'deprecation_date', 'request_count']
    list_filter = ['status', 'is_default', 'is_active']
    search_fields = ['version_number', 'version_name', 'description']
    readonly_fields = ['request_count', 'active_clients', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Version Information', {
            'fields': ('version_number', 'version_name', 'description')
        }),
        ('Status', {
            'fields': ('status', 'is_default', 'is_active')
        }),
        ('Release Schedule', {
            'fields': ('release_date', 'deprecation_date', 'sunset_date')
        }),
        ('Documentation', {
            'fields': ('changelog', 'breaking_changes', 'migration_guide'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('request_count', 'active_clients'),
            'classes': ('collapse',)
        }),
    )

@admin.register(APIEndpoint)
class APIEndpointAdmin(admin.ModelAdmin):
    list_display = ['path', 'method', 'api_version', 'serializer_class', 'is_active']
    list_filter = ['api_version', 'method', 'is_active']
    search_fields = ['path', 'description']

@admin.register(APIClient)
class APIClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'client_id', 'client_type', 'preferred_version', 'is_active', 
                   'total_requests', 'owner']
    list_filter = ['client_type', 'is_active', 'preferred_version']
    search_fields = ['name', 'client_id', 'contact_email']
    readonly_fields = ['total_requests', 'last_request', 'created_at', 'updated_at']

@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):
    list_display = ['path', 'method', 'api_version', 'status_code', 'response_time_ms', 'user', 'timestamp']
    list_filter = ['api_version', 'method', 'status_code', 'timestamp']
    search_fields = ['path', 'user__email']
    readonly_fields = ['timestamp']
