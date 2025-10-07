# system_config/admin.py
from django.contrib import admin
from .models import (
    SystemSetting, CustomField, WorkflowRule,
    NotificationTemplate, UserPreference, Integration, AuditLog
)

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'company', 'is_active']
    list_filter = ['company', 'is_active']
    search_fields = ['key', 'value', 'description']

@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'label', 'field_type', 'model_name', 'is_required', 'is_active']
    list_filter = ['field_type', 'model_name', 'is_required', 'is_active']
    search_fields = ['name', 'label']

@admin.register(WorkflowRule)
class WorkflowRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'entity_type', 'trigger_type', 'is_active']
    list_filter = ['entity_type', 'trigger_type', 'is_active']
    search_fields = ['name', 'description']

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject']

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'preference_key', 'company']
    list_filter = ['company']
    search_fields = ['user__email', 'preference_key']

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'integration_type', 'is_active']
    list_filter = ['integration_type', 'is_active']
    search_fields = ['name']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']
    search_fields = ['user__email', 'action', 'model_name']
    readonly_fields = ['created_at']
