# deals/admin.py
from django.contrib import admin
from deals.models import Deal

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'account', 'stage', 'status', 'amount',
        'probability', 'expected_close_date', 'owner'
    ]
    list_filter = [
        'status', 'stage',
        'expected_close_date', 'created_at', 'company'
    ]
    search_fields = [
        'name', 'description', 'account__name'
    ]
    ordering = ['-created_at']
    raw_id_fields = ['account', 'contact', 'owner']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'account', 'contact')
        }),
        ('Pipeline Information', {
            'fields': ('stage', 'status', 'probability')
        }),
        ('Financial Information', {
            'fields': ('amount', 'expected_close_date', 'actual_close_date')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Metadata', {
            'fields': ('custom_fields',),
            'classes': ('collapse',)
        })
    )
