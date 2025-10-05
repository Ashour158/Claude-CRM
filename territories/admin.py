# territories/admin.py
# Django Admin Configuration for Territory Models

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Territory


@admin.register(Territory)
class TerritoryAdmin(admin.ModelAdmin):
    """Territory admin interface"""
    list_display = [
        'name', 'code', 'type', 'manager', 'parent', 
        'users_count', 'is_active', 'created_at'
    ]
    list_filter = [
        'type', 'is_active', 'manager', 'parent', 
        'created_at', 'updated_at'
    ]
    search_fields = ['name', 'code', 'description']
    readonly_fields = [
        'users_count', 'accounts_count', 'leads_count', 
        'deals_count', 'total_deal_value', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['manager', 'parent']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'type', 'parent')
        }),
        ('Manager', {
            'fields': ('manager',)
        }),
        ('Geographic Criteria', {
            'fields': ('countries', 'states', 'cities', 'postal_codes'),
            'classes': ('collapse',)
        }),
        ('Product Criteria', {
            'fields': ('product_categories', 'product_ids'),
            'classes': ('collapse',)
        }),
        ('Customer Criteria', {
            'fields': ('customer_types', 'revenue_min', 'revenue_max', 'industries'),
            'classes': ('collapse',)
        }),
        ('Territory Settings', {
            'fields': ('currency', 'quota_amount', 'quota_period')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('users_count', 'accounts_count', 'leads_count', 
                      'deals_count', 'total_deal_value'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def users_count(self, obj):
        """Display number of users in territory"""
        count = obj.get_all_users().count()
        if count > 0:
            url = reverse('admin:core_user_changelist') + f'?territory__id__exact={obj.id}'
            return format_html('<a href="{}">{} users</a>', url, count)
        return '0 users'
    users_count.short_description = 'Users'


# TerritoryRule and TerritoryAssignment models are not implemented yet
# Admin classes will be added when these models are created
