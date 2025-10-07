# events/admin.py
# Event-Driven Architecture Admin Configuration

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    EventType, Event, EventHandler, EventExecution,
    EventSubscription, EventStream
)

@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    """Event type admin interface"""
    list_display = [
        'name', 'category', 'is_active', 'is_public', 
        'total_events', 'last_triggered', 'created_at'
    ]
    list_filter = [
        'category', 'is_active', 'is_public', 
        'created_at', 'updated_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'total_events', 'last_triggered', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Schema', {
            'fields': ('schema',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_public')
        }),
        ('Statistics', {
            'fields': ('total_events', 'last_triggered'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Event admin interface"""
    list_display = [
        'name', 'event_type', 'status', 'priority', 
        'triggered_by', 'created_at'
    ]
    list_filter = [
        'event_type', 'status', 'priority', 'triggered_by',
        'created_at', 'updated_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'correlation_id', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['event_type', 'triggered_by', 'parent_event']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('event_type', 'name', 'description')
        }),
        ('Event Data', {
            'fields': ('data', 'metadata')
        }),
        ('Related Entity', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Status and Priority', {
            'fields': ('status', 'priority')
        }),
        ('Processing', {
            'fields': ('triggered_by', 'processed_at', 'processing_duration'),
            'classes': ('collapse',)
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count', 'max_retries'),
            'classes': ('collapse',)
        }),
        ('Correlation', {
            'fields': ('correlation_id', 'parent_event'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(EventHandler)
class EventHandlerAdmin(admin.ModelAdmin):
    """Event handler admin interface"""
    list_display = [
        'name', 'handler_type', 'status', 'is_active',
        'total_executions', 'success_rate', 'owner', 'created_at'
    ]
    list_filter = [
        'handler_type', 'status', 'is_active', 'owner',
        'created_at', 'updated_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'total_executions', 'successful_executions', 'failed_executions',
        'last_executed', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['owner']
    filter_horizontal = ['event_types']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'handler_type')
        }),
        ('Event Configuration', {
            'fields': ('event_types', 'conditions')
        }),
        ('Handler Configuration', {
            'fields': ('endpoint_url', 'handler_function', 'configuration')
        }),
        ('Execution Settings', {
            'fields': ('is_async', 'timeout_seconds', 'retry_on_failure', 'max_retries')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_executions', 'successful_executions', 'failed_executions', 'last_executed'),
            'classes': ('collapse',)
        }),
        ('Owner', {
            'fields': ('owner',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def success_rate(self, obj):
        """Display success rate"""
        if obj.total_executions == 0:
            return 'N/A'
        rate = (obj.successful_executions / obj.total_executions) * 100
        return f"{rate:.1f}%"
    success_rate.short_description = 'Success Rate'

@admin.register(EventExecution)
class EventExecutionAdmin(admin.ModelAdmin):
    """Event execution admin interface"""
    list_display = [
        'event', 'handler', 'status', 'started_at',
        'completed_at', 'duration_ms', 'created_at'
    ]
    list_filter = [
        'status', 'started_at', 'completed_at', 'created_at'
    ]
    search_fields = ['event__name', 'handler__name']
    readonly_fields = [
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['event', 'handler', 'parent_execution']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('event', 'handler')
        }),
        ('Execution Details', {
            'fields': ('status', 'started_at', 'completed_at', 'duration_ms')
        }),
        ('Results', {
            'fields': ('result_data', 'error_message', 'error_traceback'),
            'classes': ('collapse',)
        }),
        ('Retry Information', {
            'fields': ('retry_count', 'is_retry', 'parent_execution'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(EventSubscription)
class EventSubscriptionAdmin(admin.ModelAdmin):
    """Event subscription admin interface"""
    list_display = [
        'name', 'subscription_type', 'user', 'is_active',
        'total_events', 'successful_deliveries', 'created_at'
    ]
    list_filter = [
        'subscription_type', 'is_active', 'user', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'total_events', 'successful_deliveries', 'failed_deliveries',
        'last_activity', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['user']
    filter_horizontal = ['event_types']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'subscription_type')
        }),
        ('Event Configuration', {
            'fields': ('event_types', 'filters')
        }),
        ('Subscription Details', {
            'fields': ('endpoint_url', 'user')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('total_events', 'successful_deliveries', 'failed_deliveries', 'last_activity'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(EventStream)
class EventStreamAdmin(admin.ModelAdmin):
    """Event stream admin interface"""
    list_display = [
        'name', 'stream_type', 'is_active', 'is_processing',
        'total_events', 'processed_events', 'created_at'
    ]
    list_filter = [
        'stream_type', 'is_active', 'is_processing', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'total_events', 'processed_events', 'failed_events',
        'last_processed', 'created_at', 'updated_at'
    ]
    filter_horizontal = ['event_types']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'stream_type')
        }),
        ('Stream Configuration', {
            'fields': ('event_types', 'filters', 'buffer_size', 'flush_interval')
        }),
        ('Status', {
            'fields': ('is_active', 'is_processing')
        }),
        ('Statistics', {
            'fields': ('total_events', 'processed_events', 'failed_events', 'last_processed'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
