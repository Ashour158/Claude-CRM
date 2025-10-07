# marketplace/admin.py
# Marketplace and Extensibility Admin Configuration

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    MarketplaceApp, AppInstallation, AppReview, AppPermission,
    AppWebhook, AppExecution, AppAnalytics, AppSubscription
)

@admin.register(MarketplaceApp)
class MarketplaceAppAdmin(admin.ModelAdmin):
    """Marketplace app admin interface"""
    list_display = [
        'name', 'app_type', 'developer', 'status', 'is_public',
        'is_featured', 'download_count', 'rating', 'created_at'
    ]
    list_filter = [
        'app_type', 'status', 'is_public', 'is_featured', 'is_verified',
        'security_scan_status', 'developer', 'created_at'
    ]
    search_fields = ['name', 'description', 'short_description', 'developer__first_name', 'developer__last_name']
    readonly_fields = [
        'app_id', 'download_count', 'rating', 'review_count', 'install_count',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['developer']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('app_id', 'name', 'description', 'short_description', 'app_type')
        }),
        ('Version Information', {
            'fields': ('version', 'latest_version', 'is_latest')
        }),
        ('Developer Information', {
            'fields': ('developer', 'developer_name', 'developer_email', 'developer_website')
        }),
        ('App Configuration', {
            'fields': ('manifest', 'permissions', 'dependencies')
        }),
        ('Status', {
            'fields': ('status', 'is_public', 'is_featured')
        }),
        ('Pricing', {
            'fields': ('is_free', 'price', 'currency')
        }),
        ('Statistics', {
            'fields': ('download_count', 'rating', 'review_count', 'install_count'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('is_verified', 'security_scan_status'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AppInstallation)
class AppInstallationAdmin(admin.ModelAdmin):
    """App installation admin interface"""
    list_display = [
        'app', 'installed_by', 'version', 'status', 'is_active',
        'installed_at', 'usage_count'
    ]
    list_filter = [
        'status', 'is_active', 'app', 'installed_by', 'installed_at'
    ]
    search_fields = ['app__name', 'installed_by__first_name', 'installed_by__last_name']
    readonly_fields = [
        'installed_at', 'last_updated', 'uninstalled_at', 'usage_count',
        'last_used', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['app', 'installed_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('app', 'installed_by', 'version')
        }),
        ('Installation Configuration', {
            'fields': ('installation_config',)
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('installed_at', 'last_updated', 'uninstalled_at')
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AppReview)
class AppReviewAdmin(admin.ModelAdmin):
    """App review admin interface"""
    list_display = [
        'app', 'reviewer', 'rating', 'title', 'is_verified',
        'helpful_count', 'created_at'
    ]
    list_filter = [
        'rating', 'is_verified', 'is_public', 'app', 'reviewer', 'created_at'
    ]
    search_fields = ['title', 'content', 'app__name', 'reviewer__first_name', 'reviewer__last_name']
    readonly_fields = [
        'helpful_count', 'not_helpful_count', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['app', 'reviewer']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('app', 'reviewer', 'rating', 'title', 'content')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_public')
        }),
        ('Helpfulness', {
            'fields': ('helpful_count', 'not_helpful_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AppPermission)
class AppPermissionAdmin(admin.ModelAdmin):
    """App permission admin interface"""
    list_display = [
        'app', 'permission_type', 'resource', 'status', 'requested_by',
        'requested_at', 'approved_at'
    ]
    list_filter = [
        'permission_type', 'status', 'app', 'requested_by', 'requested_at'
    ]
    search_fields = ['resource', 'app__name', 'requested_by__first_name', 'requested_by__last_name']
    readonly_fields = [
        'requested_at', 'approved_at', 'usage_count', 'last_used',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['app', 'requested_by', 'approved_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('app', 'requested_by', 'permission_type', 'resource')
        }),
        ('Permission Details', {
            'fields': ('scope', 'status')
        }),
        ('Approval', {
            'fields': ('approved_by', 'requested_at', 'approved_at', 'expires_at')
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AppWebhook)
class AppWebhookAdmin(admin.ModelAdmin):
    """App webhook admin interface"""
    list_display = [
        'name', 'app', 'webhook_type', 'status', 'is_active',
        'total_calls', 'successful_calls', 'last_called'
    ]
    list_filter = [
        'webhook_type', 'status', 'is_active', 'app', 'created_at'
    ]
    search_fields = ['name', 'description', 'app__name']
    readonly_fields = [
        'total_calls', 'successful_calls', 'failed_calls', 'last_called',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['app']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('app', 'name', 'description', 'webhook_type')
        }),
        ('Webhook Configuration', {
            'fields': ('endpoint_url', 'events', 'headers', 'secret')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_calls', 'successful_calls', 'failed_calls', 'last_called'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AppExecution)
class AppExecutionAdmin(admin.ModelAdmin):
    """App execution admin interface"""
    list_display = [
        'app', 'function_name', 'execution_type', 'status',
        'started_at', 'completed_at', 'duration_ms'
    ]
    list_filter = [
        'execution_type', 'status', 'app', 'started_at', 'completed_at'
    ]
    search_fields = ['function_name', 'app__name']
    readonly_fields = [
        'started_at', 'completed_at', 'duration_ms', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['app', 'installation']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('app', 'installation', 'execution_type', 'function_name')
        }),
        ('Execution Details', {
            'fields': ('parameters', 'status')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'duration_ms')
        }),
        ('Results', {
            'fields': ('result_data', 'error_message', 'error_traceback'),
            'classes': ('collapse',)
        }),
        ('Resource Usage', {
            'fields': ('memory_usage', 'cpu_usage'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AppAnalytics)
class AppAnalyticsAdmin(admin.ModelAdmin):
    """App analytics admin interface"""
    list_display = [
        'app', 'metric_type', 'metric_name', 'value', 'unit',
        'period_start', 'period_end'
    ]
    list_filter = [
        'metric_type', 'app', 'period_start', 'period_end'
    ]
    search_fields = ['metric_name', 'app__name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['app']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('app', 'metric_type', 'metric_name')
        }),
        ('Metric Data', {
            'fields': ('value', 'unit', 'dimensions')
        }),
        ('Time Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AppSubscription)
class AppSubscriptionAdmin(admin.ModelAdmin):
    """App subscription admin interface"""
    list_display = [
        'app', 'subscriber', 'subscription_type', 'status',
        'price', 'currency', 'started_at', 'expires_at'
    ]
    list_filter = [
        'subscription_type', 'status', 'billing_cycle', 'app', 'subscriber', 'started_at'
    ]
    search_fields = ['app__name', 'subscriber__first_name', 'subscriber__last_name']
    readonly_fields = [
        'started_at', 'expires_at', 'cancelled_at', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['app', 'subscriber']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('app', 'subscriber', 'subscription_type', 'status')
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'billing_cycle')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'expires_at', 'cancelled_at')
        }),
        ('Usage', {
            'fields': ('usage_limits', 'current_usage'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
