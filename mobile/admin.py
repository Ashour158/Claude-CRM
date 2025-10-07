# mobile/admin.py
# Mobile Application Admin Configuration

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    MobileDevice, MobileSession, OfflineData, PushNotification,
    MobileAppConfig, MobileAnalytics, MobileCrash
)

@admin.register(MobileDevice)
class MobileDeviceAdmin(admin.ModelAdmin):
    """Mobile device admin interface"""
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

@admin.register(MobileSession)
class MobileSessionAdmin(admin.ModelAdmin):
    """Mobile session admin interface"""
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

@admin.register(OfflineData)
class OfflineDataAdmin(admin.ModelAdmin):
    """Offline data admin interface"""
    list_display = [
        'entity_type', 'entity_id', 'device', 'session', 'sync_type',
        'status', 'created_at', 'synced_at'
    ]
    list_filter = [
        'sync_type', 'status', 'device', 'session', 'created_at'
    ]
    search_fields = ['entity_type', 'device__device_name']
    readonly_fields = [
        'created_at', 'synced_at', 'last_modified', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['device', 'session']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('device', 'session', 'sync_type', 'entity_type', 'entity_id')
        }),
        ('Data', {
            'fields': ('data', 'metadata')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'synced_at', 'last_modified')
        }),
        ('Conflict Resolution', {
            'fields': ('has_conflict', 'conflict_data', 'resolution_strategy'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    """Push notification admin interface"""
    list_display = [
        'title', 'notification_type', 'status', 'scheduled_at',
        'sent_at', 'total_sent', 'total_delivered'
    ]
    list_filter = [
        'notification_type', 'status', 'scheduled_at', 'sent_at', 'created_at'
    ]
    search_fields = ['title', 'message']
    readonly_fields = [
        'sent_at', 'delivered_at', 'opened_at', 'total_sent',
        'total_delivered', 'total_opened', 'created_at', 'updated_at'
    ]
    filter_horizontal = ['devices', 'users']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'message', 'notification_type')
        }),
        ('Recipients', {
            'fields': ('devices', 'users')
        }),
        ('Content', {
            'fields': ('payload', 'action_url')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'expires_at')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Delivery', {
            'fields': ('sent_at', 'delivered_at', 'opened_at'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('total_sent', 'total_delivered', 'total_opened'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(MobileAppConfig)
class MobileAppConfigAdmin(admin.ModelAdmin):
    """Mobile app configuration admin interface"""
    list_display = [
        'name', 'config_type', 'version', 'is_active', 'is_required',
        'effective_from', 'effective_until'
    ]
    list_filter = [
        'config_type', 'is_active', 'is_required', 'effective_from', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('config_type', 'name', 'description', 'version')
        }),
        ('Configuration', {
            'fields': ('configuration',)
        }),
        ('Targeting', {
            'fields': ('target_devices', 'target_users')
        }),
        ('Status', {
            'fields': ('is_active', 'is_required')
        }),
        ('Effective Period', {
            'fields': ('effective_from', 'effective_until')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(MobileAnalytics)
class MobileAnalyticsAdmin(admin.ModelAdmin):
    """Mobile analytics admin interface"""
    list_display = [
        'metric_name', 'metric_type', 'device', 'metric_value',
        'screen_name', 'action_name', 'timestamp'
    ]
    list_filter = [
        'metric_type', 'device', 'timestamp', 'created_at'
    ]
    search_fields = ['metric_name', 'action_name', 'device__device_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['device', 'session']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('device', 'session', 'metric_type', 'metric_name')
        }),
        ('Metric Data', {
            'fields': ('metric_value', 'metric_unit')
        }),
        ('Context', {
            'fields': ('screen_name', 'action_name', 'user_id')
        }),
        ('Data', {
            'fields': ('properties', 'context_data')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'created_at', 'updated_at')
        })
    )

@admin.register(MobileCrash)
class MobileCrashAdmin(admin.ModelAdmin):
    """Mobile crash admin interface"""
    list_display = [
        'crash_id', 'error_type', 'device', 'severity', 'status',
        'assigned_to', 'created_at'
    ]
    list_filter = [
        'severity', 'status', 'assigned_to', 'device', 'created_at'
    ]
    search_fields = ['error_type', 'error_message', 'device__device_name']
    readonly_fields = [
        'crash_id', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['device', 'session', 'assigned_to']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('crash_id', 'device', 'session')
        }),
        ('Crash Details', {
            'fields': ('error_type', 'error_message', 'stack_trace')
        }),
        ('Severity and Status', {
            'fields': ('severity', 'status')
        }),
        ('App Information', {
            'fields': ('app_version', 'os_version', 'device_model')
        }),
        ('Crash Data', {
            'fields': ('crash_data', 'user_actions'),
            'classes': ('collapse',)
        }),
        ('Resolution', {
            'fields': ('assigned_to', 'resolution_notes', 'fixed_in_version')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
