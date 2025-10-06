# deals/admin.py
from django.contrib import admin
from deals.models import Deal

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'account', 'stage', 'status', 'amount', 'currency',
        'probability', 'expected_close_date', 'owner', 'priority'
    ]
    list_filter = [
        'status', 'stage', 'priority', 'source', 'is_active',
        'expected_close_date', 'created_at', 'company'
    ]
    search_fields = [
        'name', 'description', 'account__name', 'contact__first_name',
        'contact__last_name', 'next_step', 'notes'
    ]
    ordering = ['-created_at']
    list_editable = ['status', 'priority']
    raw_id_fields = ['account', 'contact', 'owner', 'territory']
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'account', 'contact', 'lead')
        }),
        ('Pipeline Information', {
            'fields': ('stage', 'status', 'probability')
        }),
        ('Financial Information', {
            'fields': ('amount', 'currency', 'expected_revenue', 'expected_close_date', 'actual_close_date')
        }),
        ('Assignment', {
            'fields': ('owner', 'territory')
        }),
        ('Additional Information', {
            'fields': ('priority', 'source', 'competitor', 'next_step', 'notes')
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )