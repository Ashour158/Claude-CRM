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
        'status', 'stage', 'is_active',
        'expected_close_date', 'created_at', 'company'
    ]
    search_fields = [
        'name', 'description', 'account__name', 'contact__first_name',
        'contact__last_name'
    ]
    ordering = ['-created_at']
    list_editable = ['status']
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
        ('Custom Data', {
            'fields': ('custom_fields', 'is_active'),
            'classes': ('collapse',)
        })
    )