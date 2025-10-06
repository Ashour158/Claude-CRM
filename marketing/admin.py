# marketing/admin.py
from django.contrib import admin
from .models import (
    Campaign, EmailTemplate, EmailCampaign,
    MarketingList, MarketingListContact
)

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'start_date', 'end_date', 'is_active', 'created_at']
    list_filter = ['status', 'is_active', 'created_at', 'company']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'company']
    search_fields = ['name', 'subject', 'body']
    ordering = ['-created_at']

@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign', 'template', 'status', 'scheduled_date', 'sent_date']
    list_filter = ['status', 'scheduled_date', 'sent_date', 'company']
    search_fields = ['name', 'subject']
    ordering = ['-created_at']
    raw_id_fields = ['campaign', 'template']

@admin.register(MarketingList)
class MarketingListAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'company']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

@admin.register(MarketingListContact)
class MarketingListContactAdmin(admin.ModelAdmin):
    list_display = ['marketing_list', 'contact', 'is_subscribed', 'added_date']
    list_filter = ['is_subscribed', 'added_date', 'marketing_list__company']
    search_fields = ['contact__first_name', 'contact__last_name', 'contact__email']
    ordering = ['-added_date']
    raw_id_fields = ['marketing_list', 'contact']
