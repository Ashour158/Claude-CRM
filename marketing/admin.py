# marketing/admin.py
from django.contrib import admin
from .models import (
    Campaign, EmailTemplate, EmailCampaign, LeadScore,
    MarketingList, MarketingListContact, EmailActivity,
    MarketingAutomation, MarketingAutomationExecution
)

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign_type', 'status', 'owner', 'start_date', 'end_date', 'budget', 'is_active']
    list_filter = ['campaign_type', 'status', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'owner__first_name', 'owner__last_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'campaign_type', 'status')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date')
        }),
        ('Budget', {
            'fields': ('budget', 'currency')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Metrics', {
            'fields': ('target_audience_size', 'actual_reach', 'clicks', 'conversions', 'cost_per_click', 'cost_per_conversion')
        }),
        ('Additional', {
            'fields': ('notes', 'tags', 'metadata', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'subject', 'owner', 'usage_count', 'is_active']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject', 'owner__first_name', 'owner__last_name']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'template_type', 'subject')
        }),
        ('Content', {
            'fields': ('html_content', 'text_content')
        }),
        ('Design', {
            'fields': ('header_image_url', 'footer_text')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Statistics', {
            'fields': ('usage_count',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'status', 'owner', 'scheduled_at', 'sent_at', 'total_recipients', 'is_active']
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['name', 'subject', 'owner__first_name', 'owner__last_name']
    readonly_fields = ['sent_at', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'subject', 'status')
        }),
        ('Template', {
            'fields': ('template',)
        }),
        ('Content', {
            'fields': ('html_content', 'text_content')
        }),
        ('Schedule', {
            'fields': ('scheduled_at', 'sent_at')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Metrics', {
            'fields': ('total_recipients', 'sent_count', 'delivered_count', 'opened_count', 'clicked_count', 'unsubscribed_count', 'bounced_count')
        }),
        ('Additional', {
            'fields': ('notes', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(LeadScore)
class LeadScoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'score_type', 'points', 'owner', 'is_active']
    list_filter = ['score_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'owner__first_name', 'owner__last_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'score_type')
        }),
        ('Scoring', {
            'fields': ('criteria', 'points', 'conditions')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(MarketingList)
class MarketingListAdmin(admin.ModelAdmin):
    list_display = ['name', 'list_type', 'owner', 'member_count', 'is_active']
    list_filter = ['list_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'owner__first_name', 'owner__last_name']
    readonly_fields = ['member_count', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'list_type')
        }),
        ('Criteria', {
            'fields': ('criteria',)
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Statistics', {
            'fields': ('member_count',)
        }),
        ('Additional', {
            'fields': ('tags', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(MarketingListContact)
class MarketingListContactAdmin(admin.ModelAdmin):
    list_display = ['contact', 'list', 'subscribed_at', 'unsubscribed_at', 'is_active']
    list_filter = ['is_active', 'subscribed_at', 'unsubscribed_at']
    search_fields = ['contact__first_name', 'contact__last_name', 'contact__email', 'list__name']
    readonly_fields = ['subscribed_at', 'created_at', 'updated_at']
    fieldsets = (
        ('Membership', {
            'fields': ('list', 'contact')
        }),
        ('Timeline', {
            'fields': ('subscribed_at', 'unsubscribed_at')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

# @admin.register(MarketingEvent)
# class MarketingEventAdmin(admin.ModelAdmin):
#     list_display = ['event_name', 'event_type', 'contact', 'event_date', 'created_by']
#     list_filter = ['event_type', 'event_date', 'created_at']
#     search_fields = ['event_name', 'description', 'contact__first_name', 'contact__last_name', 'contact__email']
#     readonly_fields = ['created_at', 'updated_at']
#     fieldsets = (
#         ('Event Information', {
#             'fields': ('event_type', 'event_name', 'description', 'event_date')
#         }),
#         ('Related Objects', {
#             'fields': ('contact', 'campaign', 'email_campaign')
#         }),
#         ('Event Data', {
#             'fields': ('event_data',)
#         }),
#         ('Assignment', {
#             'fields': ('created_by',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         })
#     )

# @admin.register(MarketingAnalytics)
# class MarketingAnalyticsAdmin(admin.ModelAdmin):
#     list_display = ['name', 'start_date', 'end_date', 'total_campaigns', 'active_campaigns', 'is_active']
#     list_filter = ['is_active', 'start_date', 'end_date', 'created_at']
#     search_fields = ['name', 'description']
#     readonly_fields = ['created_at', 'updated_at']
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('name', 'description', 'start_date', 'end_date')
#         }),
#         ('Campaign Metrics', {
#             'fields': ('total_campaigns', 'active_campaigns')
#         }),
#         ('Email Metrics', {
#             'fields': ('total_emails_sent', 'total_emails_delivered', 'total_emails_opened', 'total_clicks')
#         }),
#         ('Conversion Metrics', {
#             'fields': ('total_conversions', 'total_unsubscribes', 'total_bounces')
#         }),
#         ('Rate Metrics', {
#             'fields': ('overall_open_rate', 'overall_click_rate', 'overall_bounce_rate', 'overall_conversion_rate')
#         }),
#         ('Additional', {
#          'fields': ('metadata', 'is_active')
#      }),
#      ('Timestamps', {
#          'fields': ('created_at', 'updated_at'),
#          'classes': ('collapse',)
#      })
#    )
