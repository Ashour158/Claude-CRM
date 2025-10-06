# integrations/admin.py
from django.contrib import admin
from .models import (
    APICredential, Webhook, WebhookLog,
    DataSync, DataSyncLog
)

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'integration_type', 'provider', 'status', 'is_active', 'owner']
    list_filter = ['integration_type', 'provider', 'status', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'provider']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'integration_type', 'provider', 'description')
        }),
        ('API Configuration', {
            'fields': ('api_endpoint', 'api_key', 'api_secret', 'webhook_url')
        }),
        ('Settings', {
            'fields': ('settings', 'credentials')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Sync Information', {
            'fields': ('last_sync', 'sync_frequency')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(EmailIntegration)
class EmailIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'from_email', 'is_active', 'is_verified', 'owner']
    list_filter = ['provider', 'is_active', 'is_verified', 'created_at']
    search_fields = ['name', 'from_email', 'from_name']
    readonly_fields = ['emails_sent', 'emails_delivered', 'emails_bounced', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider')
        }),
        ('SMTP Configuration', {
            'fields': ('smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_use_tls', 'smtp_use_ssl')
        }),
        ('API Configuration', {
            'fields': ('api_key', 'api_secret', 'api_url')
        }),
        ('Email Settings', {
            'fields': ('from_email', 'from_name', 'reply_to_email')
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_per_hour', 'rate_limit_per_day')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Statistics', {
            'fields': ('emails_sent', 'emails_delivered', 'emails_bounced')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(CalendarIntegration)
class CalendarIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'calendar_name', 'is_active', 'is_connected', 'owner']
    list_filter = ['provider', 'is_active', 'is_connected', 'created_at']
    search_fields = ['name', 'calendar_name']
    readonly_fields = ['events_synced', 'last_sync', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider')
        }),
        ('OAuth Configuration', {
            'fields': ('client_id', 'client_secret', 'redirect_uri', 'access_token', 'refresh_token', 'token_expires_at')
        }),
        ('Calendar Settings', {
            'fields': ('calendar_id', 'calendar_name', 'timezone')
        }),
        ('Sync Settings', {
            'fields': ('sync_events', 'sync_tasks', 'sync_contacts')
        }),
        ('Status', {
            'fields': ('is_active', 'is_connected')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Statistics', {
            'fields': ('events_synced', 'last_sync')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ['name', 'webhook_type', 'url', 'is_active', 'total_calls', 'owner']
    list_filter = ['webhook_type', 'is_active', 'created_at']
    search_fields = ['name', 'url']
    readonly_fields = ['total_calls', 'successful_calls', 'failed_calls', 'last_called', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'webhook_type', 'url', 'http_method')
        }),
        ('Authentication', {
            'fields': ('auth_type', 'auth_username', 'auth_password', 'auth_token', 'auth_header')
        }),
        ('Configuration', {
            'fields': ('headers', 'payload_template')
        }),
        ('Triggers', {
            'fields': ('trigger_events', 'trigger_conditions')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Statistics', {
            'fields': ('total_calls', 'successful_calls', 'failed_calls', 'last_called')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['webhook', 'status', 'request_method', 'response_status_code', 'execution_time', 'created_at']
    list_filter = ['status', 'request_method', 'created_at']
    search_fields = ['webhook__name', 'request_url', 'error_message']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Log Information', {
            'fields': ('webhook', 'status')
        }),
        ('Request Details', {
            'fields': ('request_url', 'request_method', 'request_headers', 'request_payload')
        }),
        ('Response Details', {
            'fields': ('response_status_code', 'response_headers', 'response_body')
        }),
        ('Execution Details', {
            'fields': ('execution_time', 'error_message', 'retry_count')
        }),
        ('Context', {
            'fields': ('triggered_by', 'object_type', 'object_id')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )

@admin.register(APICredential)
class APICredentialAdmin(admin.ModelAdmin):
    list_display = ['name', 'service', 'credential_type', 'is_active', 'is_verified', 'owner']
    list_filter = ['service', 'credential_type', 'is_active', 'is_verified', 'created_at']
    search_fields = ['name', 'service']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'service', 'credential_type')
        }),
        ('Credentials', {
            'fields': ('api_key', 'api_secret', 'access_token', 'refresh_token', 'username', 'password')
        }),
        ('OAuth Configuration', {
            'fields': ('client_id', 'client_secret', 'redirect_uri', 'scope')
        }),
        ('Additional Configuration', {
            'fields': ('base_url', 'headers')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Expiration', {
            'fields': ('expires_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(DataSync)
class DataSyncAdmin(admin.ModelAdmin):
    list_display = ['name', 'sync_type', 'source_system', 'target_system', 'status', 'is_active', 'owner']
    list_filter = ['sync_type', 'source_system', 'target_system', 'status', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['total_records_synced', 'last_sync', 'next_sync', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'sync_type')
        }),
        ('Source and Target', {
            'fields': ('source_system', 'target_system', 'source_endpoint', 'target_endpoint')
        }),
        ('Configuration', {
            'fields': ('sync_frequency', 'batch_size', 'sync_conditions')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Statistics', {
            'fields': ('total_records_synced', 'last_sync', 'next_sync')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
