# deals/admin.py
from django.contrib import admin
from deals.models import Deal

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['name', 'account', 'stage', 'status', 'amount', 'expected_close_date', 'owner']
    list_filter = ['status', 'stage', 'expected_close_date', 'created_at', 'company']
    search_fields = ['name', 'description', 'account__name', 'contact__first_name', 'contact__last_name']
    ordering = ['-created_at']
    list_editable = ['status']
    raw_id_fields = ['account', 'contact', 'owner']
