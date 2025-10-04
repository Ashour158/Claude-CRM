# deals/admin.py
from django.contrib import admin
from deals.models import PipelineStage, Deal, DealProduct, DealActivity, DealForecast

@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ['name', 'sequence', 'probability', 'is_closed', 'is_won', 'is_active']
    list_filter = ['is_closed', 'is_won', 'is_active', 'company']
    search_fields = ['name', 'description']
    ordering = ['sequence']
    list_editable = ['sequence', 'probability', 'is_closed', 'is_won', 'is_active']

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

@admin.register(DealProduct)
class DealProductAdmin(admin.ModelAdmin):
    list_display = ['deal', 'product', 'quantity', 'unit_price', 'total_price']
    list_filter = ['deal__company', 'created_at']
    search_fields = ['deal__name', 'product__name']
    ordering = ['-created_at']
    raw_id_fields = ['deal', 'product']

@admin.register(DealActivity)
class DealActivityAdmin(admin.ModelAdmin):
    list_display = [
        'deal', 'activity_type', 'subject', 'activity_date',
        'duration_minutes', 'created_by'
    ]
    list_filter = ['activity_type', 'activity_date', 'deal__company']
    search_fields = ['subject', 'description', 'deal__name']
    ordering = ['-activity_date']
    raw_id_fields = ['deal', 'created_by']
    filter_horizontal = ['participants']

@admin.register(DealForecast)
class DealForecastAdmin(admin.ModelAdmin):
    list_display = ['deal', 'forecast_period', 'forecast_date', 'forecast_amount', 'confidence_level']
    list_filter = ['forecast_period', 'forecast_date', 'deal__company']
    search_fields = ['deal__name', 'notes']
    ordering = ['-forecast_date']
    raw_id_fields = ['deal']