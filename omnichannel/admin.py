# omnichannel/admin.py
# Omnichannel Communication Admin Configuration

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    CommunicationChannel, Conversation, Message, ConversationTemplate,
    ConversationRule, ConversationMetric, ConversationAnalytics
)

@admin.register(CommunicationChannel)
class CommunicationChannelAdmin(admin.ModelAdmin):
    """Communication channel admin interface"""
    list_display = [
        'name', 'channel_type', 'status', 'is_active',
        'total_conversations', 'active_conversations', 'customer_satisfaction'
    ]
    list_filter = [
        'channel_type', 'status', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'total_conversations', 'active_conversations', 'average_response_time',
        'customer_satisfaction', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'channel_type', 'description')
        }),
        ('Configuration', {
            'fields': ('configuration', 'credentials')
        }),
        ('SLA Settings', {
            'fields': ('response_time_sla', 'resolution_time_sla')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_conversations', 'active_conversations', 
                      'average_response_time', 'customer_satisfaction'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Conversation admin interface"""
    list_display = [
        'subject', 'channel', 'customer', 'assigned_agent', 'status',
        'priority', 'created_at'
    ]
    list_filter = [
        'channel', 'status', 'priority', 'assigned_agent', 'created_at'
    ]
    search_fields = ['subject', 'description', 'customer__first_name', 'customer__last_name']
    readonly_fields = [
        'conversation_id', 'first_response_time', 'resolution_time',
        'last_activity', 'resolved_at', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['channel', 'customer', 'assigned_agent']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('conversation_id', 'subject', 'description', 'channel')
        }),
        ('Participants', {
            'fields': ('customer', 'assigned_agent')
        }),
        ('Status and Priority', {
            'fields': ('status', 'priority')
        }),
        ('SLA Tracking', {
            'fields': ('sla_deadline', 'first_response_time', 'resolution_time'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('external_id', 'tags', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Activity', {
            'fields': ('last_activity', 'resolved_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Message admin interface"""
    list_display = [
        'conversation', 'sender', 'recipient', 'message_type',
        'direction', 'is_read', 'is_delivered', 'created_at'
    ]
    list_filter = [
        'message_type', 'direction', 'is_read', 'is_delivered', 'is_sent', 'created_at'
    ]
    search_fields = ['content', 'sender__first_name', 'sender__last_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['conversation', 'sender', 'recipient']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('conversation', 'message_type', 'direction')
        }),
        ('Content', {
            'fields': ('content', 'content_type', 'attachments')
        }),
        ('Participants', {
            'fields': ('sender', 'recipient')
        }),
        ('External References', {
            'fields': ('external_id', 'thread_id'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'is_delivered', 'is_sent')
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

@admin.register(ConversationTemplate)
class ConversationTemplateAdmin(admin.ModelAdmin):
    """Conversation template admin interface"""
    list_display = [
        'name', 'template_type', 'is_active', 'is_public',
        'usage_count', 'owner', 'created_at'
    ]
    list_filter = [
        'template_type', 'is_active', 'is_public', 'owner', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'usage_count', 'last_used', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['owner']
    filter_horizontal = ['channels']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'template_type')
        }),
        ('Template Content', {
            'fields': ('subject_template', 'content_template', 'variables')
        }),
        ('Channels', {
            'fields': ('channels',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_public')
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used'),
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

@admin.register(ConversationRule)
class ConversationRuleAdmin(admin.ModelAdmin):
    """Conversation rule admin interface"""
    list_display = [
        'name', 'rule_type', 'trigger_condition', 'is_active',
        'priority', 'execution_count', 'created_at'
    ]
    list_filter = [
        'rule_type', 'trigger_condition', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'execution_count', 'success_count', 'last_executed',
        'created_at', 'updated_at'
    ]
    filter_horizontal = ['channels']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'rule_type', 'trigger_condition')
        }),
        ('Rule Configuration', {
            'fields': ('conditions', 'actions')
        }),
        ('Channels', {
            'fields': ('channels',)
        }),
        ('Status', {
            'fields': ('is_active', 'priority')
        }),
        ('Statistics', {
            'fields': ('execution_count', 'success_count', 'last_executed'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ConversationMetric)
class ConversationMetricAdmin(admin.ModelAdmin):
    """Conversation metric admin interface"""
    list_display = [
        'name', 'metric_type', 'calculation_method', 'aggregation_period',
        'target_value', 'is_active', 'created_at'
    ]
    list_filter = [
        'metric_type', 'aggregation_period', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('metric_type', 'name', 'description')
        }),
        ('Configuration', {
            'fields': ('calculation_method', 'aggregation_period', 'filters')
        }),
        ('Targets and Thresholds', {
            'fields': ('target_value', 'warning_threshold', 'critical_threshold')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ConversationAnalytics)
class ConversationAnalyticsAdmin(admin.ModelAdmin):
    """Conversation analytics admin interface"""
    list_display = [
        'metric', 'period_start', 'period_end', 'current_value',
        'trend_direction', 'status', 'created_at'
    ]
    list_filter = [
        'metric', 'trend_direction', 'status', 'created_at'
    ]
    search_fields = ['metric__name', 'insights']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['metric']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('metric', 'period_start', 'period_end')
        }),
        ('Values', {
            'fields': ('current_value', 'previous_value', 'target_value')
        }),
        ('Trend Analysis', {
            'fields': ('trend_direction', 'trend_percentage', 'status')
        }),
        ('Analysis', {
            'fields': ('insights', 'recommendations')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
