# security/admin.py
# Enterprise Security Admin Configuration

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    SecurityPolicy, SSOConfiguration, SCIMConfiguration, IPAllowlist,
    DeviceManagement, SessionManagement, AuditLog, SecurityIncident,
    DataRetentionPolicy
)

@admin.register(SecurityPolicy)
class SecurityPolicyAdmin(admin.ModelAdmin):
    """Security policy admin interface"""
    list_display = [
        'name', 'policy_type', 'status', 'enforcement_level',
        'is_active', 'owner', 'created_at'
    ]
    list_filter = [
        'policy_type', 'status', 'enforcement_level', 'is_active',
        'owner', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['owner']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'policy_type')
        }),
        ('Configuration', {
            'fields': ('configuration', 'rules')
        }),
        ('Status', {
            'fields': ('status', 'is_active', 'enforcement_level')
        }),
        ('Owner', {
            'fields': ('owner',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SSOConfiguration)
class SSOConfigurationAdmin(admin.ModelAdmin):
    """SSO configuration admin interface"""
    list_display = [
        'name', 'provider_type', 'status', 'is_active',
        'test_status', 'last_test', 'created_at'
    ]
    list_filter = [
        'provider_type', 'status', 'is_active', 'test_status', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'last_test', 'test_status', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'provider_type')
        }),
        ('Configuration', {
            'fields': ('configuration', 'credentials')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Testing', {
            'fields': ('last_test', 'test_status'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SCIMConfiguration)
class SCIMConfigurationAdmin(admin.ModelAdmin):
    """SCIM configuration admin interface"""
    list_display = [
        'name', 'status', 'is_active', 'total_syncs',
        'successful_syncs', 'last_sync', 'created_at'
    ]
    list_filter = [
        'status', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'total_syncs', 'successful_syncs', 'failed_syncs',
        'last_sync', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Configuration', {
            'fields': ('endpoint_url', 'bearer_token')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_syncs', 'successful_syncs', 'failed_syncs', 'last_sync'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(IPAllowlist)
class IPAllowlistAdmin(admin.ModelAdmin):
    """IP allowlist admin interface"""
    list_display = [
        'name', 'allowlist_type', 'is_active', 'total_requests',
        'blocked_requests', 'created_at'
    ]
    list_filter = [
        'allowlist_type', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'total_requests', 'blocked_requests', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'allowlist_type')
        }),
        ('IP Configuration', {
            'fields': ('ip_addresses', 'countries')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('total_requests', 'blocked_requests'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(DeviceManagement)
class DeviceManagementAdmin(admin.ModelAdmin):
    """Device management admin interface"""
    list_display = [
        'device_name', 'device_type', 'user', 'status', 'is_trusted',
        'last_seen', 'total_sessions', 'created_at'
    ]
    list_filter = [
        'device_type', 'status', 'is_trusted', 'user', 'created_at'
    ]
    search_fields = ['device_name', 'operating_system', 'browser', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'device_id', 'last_seen', 'total_sessions', 'last_ip_address',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('device_id', 'device_name', 'device_type', 'user')
        }),
        ('Device Details', {
            'fields': ('operating_system', 'os_version', 'app_version', 'device_model', 'manufacturer')
        }),
        ('Status', {
            'fields': ('status', 'is_trusted')
        }),
        ('Security', {
            'fields': ('push_token', 'fingerprint', 'encryption_key'),
            'classes': ('collapse',)
        }),
        ('Activity', {
            'fields': ('last_seen', 'total_sessions', 'last_ip_address'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('app_config', 'user_preferences'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SessionManagement)
class SessionManagementAdmin(admin.ModelAdmin):
    """Session management admin interface"""
    list_display = [
        'session_id', 'session_type', 'user', 'device', 'status',
        'started_at', 'last_activity', 'expires_at'
    ]
    list_filter = [
        'session_type', 'status', 'user', 'device', 'started_at'
    ]
    search_fields = ['session_id', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'session_id', 'started_at', 'last_activity', 'terminated_at',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['user', 'device']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('session_id', 'session_type', 'user', 'device')
        }),
        ('Session Details', {
            'fields': ('app_version', 'ip_address', 'user_agent', 'location')
        }),
        ('Status', {
            'fields': ('status', 'is_secure')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'last_activity', 'expires_at', 'terminated_at')
        }),
        ('Security', {
            'fields': ('encryption_key',),
            'classes': ('collapse',)
        }),
        ('Data', {
            'fields': ('session_data', 'offline_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Audit log admin interface"""
    list_display = [
        'event_name', 'event_type', 'user', 'severity', 'is_successful',
        'created_at'
    ]
    list_filter = [
        'event_type', 'severity', 'is_successful', 'user', 'created_at'
    ]
    search_fields = ['event_name', 'description', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'session']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('event_type', 'event_name', 'description')
        }),
        ('User and Session', {
            'fields': ('user', 'session')
        }),
        ('Event Details', {
            'fields': ('ip_address', 'user_agent', 'location')
        }),
        ('Severity and Status', {
            'fields': ('severity', 'is_successful')
        }),
        ('Event Data', {
            'fields': ('event_data', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Related Entity', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    """Security incident admin interface"""
    list_display = [
        'title', 'incident_type', 'severity', 'status', 'assigned_to',
        'detected_at', 'resolved_at'
    ]
    list_filter = [
        'incident_type', 'severity', 'status', 'assigned_to', 'detected_at'
    ]
    search_fields = ['title', 'description', 'assigned_to__first_name', 'assigned_to__last_name']
    readonly_fields = [
        'incident_id', 'detected_at', 'resolved_at', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['assigned_to']
    filter_horizontal = ['affected_users']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('incident_id', 'title', 'description', 'incident_type')
        }),
        ('Severity and Status', {
            'fields': ('severity', 'status')
        }),
        ('Affected Systems', {
            'fields': ('affected_users', 'affected_systems')
        }),
        ('Investigation', {
            'fields': ('assigned_to', 'investigation_notes')
        }),
        ('Timestamps', {
            'fields': ('detected_at', 'resolved_at')
        }),
        ('Impact Assessment', {
            'fields': ('impact_assessment', 'remediation_actions'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(DataRetentionPolicy)
class DataRetentionPolicyAdmin(admin.ModelAdmin):
    """Data retention policy admin interface"""
    list_display = [
        'name', 'retention_type', 'retention_period_days', 'is_active',
        'total_records', 'deleted_records', 'last_cleanup'
    ]
    list_filter = [
        'retention_type', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'total_records', 'deleted_records', 'last_cleanup',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'retention_type')
        }),
        ('Retention Configuration', {
            'fields': ('retention_period_days', 'auto_delete', 'archive_before_delete')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('total_records', 'deleted_records', 'last_cleanup'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
