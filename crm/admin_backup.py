# crm/admin.py
# Django Admin Configuration for CRM Models

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum

from .models import Account, Contact, Lead


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """Account admin interface"""
    list_display = [
        'name', 'account_number', 'type', 'industry', 'owner', 
        'contacts_count', 'deals_count', 'is_active', 'created_at'
    ]
    list_filter = [
        'type', 'industry', 'is_active', 'owner', 'territory', 
        'created_at', 'updated_at'
    ]
    search_fields = [
        'name', 'account_number', 'email', 'phone', 'website'
    ]
    readonly_fields = [
        'account_number', 'contacts_count', 'deals_count', 
        'open_deals_value', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['owner', 'territory', 'parent_account']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'account_number', 'description', 'type', 'industry')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'website', 'fax')
        }),
        ('Address Information', {
            'fields': ('billing_address_line1', 'billing_address_line2', 
                      'billing_city', 'billing_state', 'billing_postal_code', 
                      'billing_country', 'shipping_address_line1', 
                      'shipping_address_line2', 'shipping_city', 
                      'shipping_state', 'shipping_postal_code', 'shipping_country')
        }),
        ('Business Information', {
            'fields': ('annual_revenue', 'employee_count', 'parent_account')
        }),
        ('Assignment', {
            'fields': ('owner', 'territory')
        }),
        ('Financial Settings', {
            'fields': ('payment_terms', 'credit_limit', 'currency'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('contacts_count', 'deals_count', 'open_deals_value'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def contacts_count(self, obj):
        """Display number of contacts"""
        count = obj.contacts.count()
        if count > 0:
            url = reverse('admin:crm_contact_changelist') + f'?account__id__exact={obj.id}'
            return format_html('<a href="{}">{} contacts</a>', url, count)
        return '0 contacts'
    contacts_count.short_description = 'Contacts'
    
    def deals_count(self, obj):
        """Display number of deals"""
        count = obj.deals.count()
        if count > 0:
            url = reverse('admin:deals_deal_changelist') + f'?account__id__exact={obj.id}'
            return format_html('<a href="{}">{} deals</a>', url, count)
        return '0 deals'
    deals_count.short_description = 'Deals'


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Contact admin interface"""
    list_display = [
        'full_name', 'email', 'phone', 'account', 'title', 
        'is_primary', 'owner', 'is_active', 'created_at'
    ]
    list_filter = [
        'title', 'is_primary', 'is_active', 'owner', 'account', 
        'created_at', 'updated_at'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'phone', 'account__name'
    ]
    readonly_fields = [
        'full_name', 'activities_count', 'deals_count', 'age',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['account', 'owner', 'reports_to']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'full_name', 'title', 
                      'email', 'phone', 'mobile', 'fax')
        }),
        ('Social Media', {
            'fields': ('linkedin_url', 'twitter_url', 'facebook_url'),
            'classes': ('collapse',)
        }),
        ('Account Information', {
            'fields': ('account', 'is_primary', 'reports_to')
        }),
        ('Address Information', {
            'fields': ('mailing_address_line1', 'mailing_address_line2', 
                      'mailing_city', 'mailing_state', 'mailing_postal_code', 
                      'mailing_country', 'other_address_line1', 
                      'other_address_line2', 'other_city', 'other_state', 
                      'other_postal_code', 'other_country')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Preferences', {
            'fields': ('preferred_contact_method', 'preferred_language', 
                      'timezone', 'date_format', 'time_format'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('birth_date', 'anniversary_date'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('activities_count', 'deals_count', 'age'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Lead admin interface"""
    list_display = [
        'full_name', 'email', 'phone', 'company', 'status', 
        'rating', 'lead_score', 'owner', 'is_qualified', 'created_at'
    ]
    list_filter = [
        'status', 'rating', 'source', 'is_qualified', 'owner', 
        'territory', 'created_at', 'updated_at'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'phone', 'company'
    ]
    readonly_fields = [
        'full_name', 'is_hot', 'is_qualified', 'days_since_creation',
        'activities_count', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['owner', 'territory']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'full_name', 'email', 'phone')
        }),
        ('Company Information', {
            'fields': ('company', 'title', 'website', 'industry', 
                      'annual_revenue', 'employee_count')
        }),
        ('Lead Details', {
            'fields': ('status', 'rating', 'lead_score', 'source', 
                      'description', 'is_qualified')
        }),
        ('Address Information', {
            'fields': ('address_line1', 'address_line2', 'city', 
                      'state', 'postal_code', 'country')
        }),
        ('Assignment', {
            'fields': ('owner', 'territory')
        }),
        ('Qualification', {
            'fields': ('budget', 'timeline', 'decision_makers'),
            'classes': ('collapse',)
        }),
        ('Campaign Tracking', {
            'fields': ('campaign_source', 'campaign_medium', 'campaign_name', 
                      'campaign_term', 'campaign_content'),
            'classes': ('collapse',)
        }),
        ('Conversion Tracking', {
            'fields': ('converted_at', 'converted_to_account', 
                      'converted_to_contact', 'converted_to_deal'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('is_hot', 'is_qualified', 'days_since_creation', 
                      'activities_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_qualified(self, obj):
        """Display qualification status"""
        if obj.is_qualified:
            return format_html('<span style="color: green;">✓ Qualified</span>')
        return format_html('<span style="color: red;">✗ Not Qualified</span>')
    is_qualified.short_description = 'Qualified'
