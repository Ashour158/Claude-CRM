# system_config/admin.py
from django.contrib import admin
from .models import (
    CustomField, SystemSetting, WorkflowRule,
    UserPreference, NotificationTemplate, Integration, AuditLog
)

@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'label', 'field_type', 'model_name', 'is_required', 'is_active']
    list_filter = ['field_type', 'model_name', 'is_required', 'is_active', 'created_at']
    search_fields = ['name', 'label', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'label', 'field_type', 'description', 'model_name')
        }),
        ('Field Configuration', {
            'fields': ('is_required', 'is_unique', 'default_value', 'options')
        }),
        ('Validation', {
            'fields': ('min_length', 'max_length', 'min_value', 'max_value')
        }),
        ('Display', {
            'fields': ('sequence', 'is_visible', 'help_text')
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

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'category', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['company']

@admin.register(WorkflowRule)
class WorkflowRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'entity_type', 'trigger_event', 'is_active']
    list_filter = ['entity_type', 'trigger_event', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['company']

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'preference_key', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__first_name', 'user__last_name', 'preference_key']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user', 'company']

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'is_active']
    list_filter = ['notification_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['company']

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'integration_type', 'is_active', 'is_connected']
    list_filter = ['integration_type', 'is_active', 'is_connected', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['company']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'entity_type', 'created_at']
    list_filter = ['action', 'entity_type', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'entity_type', 'entity_id']
    readonly_fields = ['created_at']
    raw_id_fields = ['user', 'company']
