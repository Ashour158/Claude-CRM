# audit/admin.py
# Admin configuration for audit module

from django.contrib import admin
from .models import AuditLog, AuditLogExport, ComplianceReport, AuditPolicy

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['audit_id', 'user_email', 'action', 'entity_type', 'entity_name', 
                   'is_sensitive', 'requires_review', 'reviewed', 'timestamp']
    list_filter = ['action', 'entity_type', 'is_sensitive', 'requires_review', 'reviewed', 'timestamp']
    search_fields = ['user_email', 'entity_name', 'entity_id', 'action_description']
    readonly_fields = ['audit_id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_email', 'impersonated_by')
        }),
        ('Action', {
            'fields': ('action', 'action_description')
        }),
        ('Entity', {
            'fields': ('entity_type', 'entity_id', 'entity_name')
        }),
        ('Changes', {
            'fields': ('old_values', 'new_values', 'changed_fields'),
            'classes': ('collapse',)
        }),
        ('Request Context', {
            'fields': ('ip_address', 'user_agent', 'request_method', 'request_path', 'session_id'),
            'classes': ('collapse',)
        }),
        ('Additional Context', {
            'fields': ('reason', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Compliance', {
            'fields': ('is_sensitive', 'requires_review', 'reviewed', 'reviewed_by', 'reviewed_at')
        }),
    )

@admin.register(AuditLogExport)
class AuditLogExportAdmin(admin.ModelAdmin):
    list_display = ['export_id', 'name', 'format', 'status', 'record_count', 'requested_by', 'requested_at']
    list_filter = ['status', 'format', 'requested_at']
    search_fields = ['name', 'export_id']
    readonly_fields = ['export_id', 'requested_at', 'started_at', 'completed_at']

@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = ['report_id', 'name', 'report_type', 'period_start', 'period_end', 
                   'total_events', 'flagged_events', 'is_published', 'created_by']
    list_filter = ['report_type', 'is_published', 'created_at']
    search_fields = ['name', 'description', 'report_id']
    readonly_fields = ['report_id', 'created_at', 'updated_at', 'published_at']

@admin.register(AuditPolicy)
class AuditPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'priority', 'alert_on_violation', 
                   'violation_count', 'retention_days', 'owner']
    list_filter = ['is_active', 'alert_on_violation', 'priority']
    search_fields = ['name', 'description']
    readonly_fields = ['violation_count', 'last_violation', 'created_at', 'updated_at']
