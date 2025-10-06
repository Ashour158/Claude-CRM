# system_config/admin.py
from django.contrib import admin
from .models import (
    SystemSetting, CustomField, WorkflowRule, NotificationTemplate,
    UserPreference, Integration, AuditLog
)

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'setting_type', 'is_required', 'is_editable']
    list_filter = ['setting_type', 'is_required', 'is_editable', 'is_public', 'company']
    search_fields = ['name', 'key', 'description']
    ordering = ['setting_type', 'name']

@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'label', 'field_type', 'entity_type', 'is_required', 'is_visible']
    list_filter = ['field_type', 'entity_type', 'is_required', 'is_visible', 'company']
    search_fields = ['name', 'label', 'description']
    ordering = ['entity_type', 'display_order']

@admin.register(WorkflowRule)
class WorkflowRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'entity_type', 'is_active', 'execution_count', 'last_executed']
    list_filter = ['rule_type', 'is_active', 'is_global', 'company']
    search_fields = ['name', 'description', 'entity_type']
    ordering = ['name']

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'is_global']
    list_filter = ['template_type', 'is_active', 'is_global', 'company']
    search_fields = ['name', 'description', 'subject']
    ordering = ['name']

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'language', 'timezone', 'email_notifications', 'push_notifications']
    list_filter = ['theme', 'language', 'email_notifications', 'push_notifications', 'company']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'integration_type', 'provider', 'status', 'is_active', 'last_sync']
    list_filter = ['integration_type', 'status', 'is_active', 'company']
    search_fields = ['name', 'description', 'provider']
    ordering = ['name']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'object_type', 'object_name', 'success', 'created_at']
    list_filter = ['action', 'success', 'created_at', 'company']
    search_fields = ['object_type', 'object_name', 'description', 'user__email']
    ordering = ['-created_at']
    raw_id_fields = ['user']
