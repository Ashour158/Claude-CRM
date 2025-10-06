# crm/admin.py
from django.contrib import admin
from crm.models import Tag, Account, Contact, Lead

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'company', 'created_at']
    list_filter = ['company', 'created_at']
    search_fields = ['name', 'description']

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_number', 'type', 'industry', 'owner', 'is_active', 'created_at']
    list_filter = ['type', 'industry', 'is_active', 'owner', 'territory', 'created_at', 'updated_at']
    search_fields = ['name', 'legal_name', 'email', 'phone']
    readonly_fields = ['account_number', 'created_at', 'updated_at']
    raw_id_fields = ['owner', 'territory', 'parent_account']

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'account', 'title', 'is_primary', 'owner', 'is_active', 'created_at']
    list_filter = ['title', 'is_primary', 'is_active', 'owner', 'account', 'created_at', 'updated_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['full_name', 'created_at', 'updated_at']
    raw_id_fields = ['account', 'owner', 'reports_to']

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'company_name', 'status', 'rating', 'lead_score', 'owner', 'created_at']
    list_filter = ['status', 'rating', 'source', 'owner', 'territory', 'created_at', 'updated_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'company_name']
    readonly_fields = ['full_name', 'created_at', 'updated_at']
    raw_id_fields = ['owner', 'territory', 'converted_account', 'converted_contact']
