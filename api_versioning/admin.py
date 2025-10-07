# api_versioning/admin.py
# API Versioning Admin Interface

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import APIVersion, APIEndpoint, APIClient, APIRequestLog, APIDeprecationNotice

@admin.register(APIVersion)
class APIVersionAdmin(admin.ModelAdmin):
    """API version admin interface"""
    
    list_display = [
        'version', 'name', 'status', 'is_default', 'is_public',
        'release_date', 'created_by', 'created_at'
    ]
    list_filter = [
        'status', 'is_default', 'is_public', 'requires_auth',
        'created_at', 'release_date'
    ]
    search_fields = ['version', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Version Information', {
            'fields': ('version', 'name', 'description', 'status')
        }),
        ('Timeline', {
            'fields': ('release_date', 'deprecation_date', 'retirement_date')
        }),
        ('Configuration', {
            'fields': ('is_default', 'is_public', 'requires_auth')
        }),
        ('Documentation', {
            'fields': ('changelog', 'migration_guide', 'breaking_changes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(APIEndpoint)
class APIEndpointAdmin(admin.ModelAdmin):
    """API endpoint admin interface"""
    
    list_display = [
        'path', 'method', 'version', 'is_active', 'is_deprecated',
        'rate_limit', 'timeout', 'created_at'
    ]
    list_filter = [
        'version', 'method', 'is_active', 'is_deprecated',
        'created_at', 'updated_at'
    ]
    search_fields = ['path', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Endpoint Information', {
            'fields': ('version', 'path', 'method', 'description')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deprecated', 'deprecation_notice')
        }),
        ('Configuration', {
            'fields': ('rate_limit', 'timeout')
        }),
        ('Documentation', {
            'fields': ('parameters', 'response_schema')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(APIClient)
class APIClientAdmin(admin.ModelAdmin):
    """API client admin interface"""
    
    list_display = [
        'name', 'client_type', 'primary_version', 'is_active',
        'rate_limit', 'last_used', 'created_by', 'created_at'
    ]
    list_filter = [
        'client_type', 'is_active', 'primary_version', 'created_at'
    ]
    search_fields = ['name', 'description', 'contact_email']
    readonly_fields = ['client_id', 'created_at', 'updated_at', 'last_used']
    
    fieldsets = (
        ('Client Information', {
            'fields': ('name', 'description', 'client_type', 'client_id', 'client_secret')
        }),
        ('Version Configuration', {
            'fields': ('primary_version', 'supported_versions')
        }),
        ('Access Control', {
            'fields': ('is_active', 'rate_limit')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_name')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'last_used'),
            'classes': ('collapse',)
        })
    )

@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):
    """API request log admin interface"""
    
    list_display = [
        'client', 'method', 'path', 'status_code', 'response_time',
        'ip_address', 'timestamp'
    ]
    list_filter = [
        'client', 'version', 'method', 'status_code', 'timestamp'
    ]
    search_fields = ['path', 'ip_address', 'user_agent']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('client', 'version', 'endpoint', 'method', 'path', 'query_params')
        }),
        ('Response Information', {
            'fields': ('status_code', 'response_time', 'response_size')
        }),
        ('Client Information', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Error Information', {
            'fields': ('error_message', 'error_type'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        })
    )

@admin.register(APIDeprecationNotice)
class APIDeprecationNoticeAdmin(admin.ModelAdmin):
    """API deprecation notice admin interface"""
    
    list_display = [
        'title', 'version', 'severity', 'notice_date', 'deprecation_date',
        'is_active', 'created_at'
    ]
    list_filter = [
        'version', 'severity', 'is_active', 'notice_date', 'deprecation_date'
    ]
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Notice Information', {
            'fields': ('version', 'endpoint', 'title', 'description')
        }),
        ('Timeline', {
            'fields': ('notice_date', 'deprecation_date', 'retirement_date')
        }),
        ('Migration Information', {
            'fields': ('migration_guide', 'alternative_endpoints')
        }),
        ('Impact Assessment', {
            'fields': ('affected_clients', 'severity')
        }),
        ('Status', {
            'fields': ('is_active', 'acknowledged_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
