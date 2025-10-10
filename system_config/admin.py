# system_config/admin.py
from django.contrib import admin
from .models import (
    CustomField, WorkflowRule, NotificationTemplate,
    UserPreference, SystemSetting, Integration, AuditLog
)

@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'label', 'field_type', 'model_name', 'is_required', 'is_active']
    list_filter = ['field_type', 'model_name', 'is_required', 'is_active', 'created_at']
    search_fields = ['name', 'label', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'key', 'value', 'category']
    list_filter = ['category', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'key', 'value']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'category', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(WorkflowRule)
class WorkflowRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'trigger_type', 'is_active']
    list_filter = ['trigger_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'is_active']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['name', 'subject']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'is_active']
    list_filter = ['provider', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'model_name', 'user', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']
    search_fields = ['user__email', 'description']
    readonly_fields = ['created_at']
