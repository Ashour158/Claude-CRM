# audit/admin.py
# Audit Admin Interface

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import AuditLog, AuditPolicy, AuditReview, ComplianceReport, AuditExport

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Audit log admin interface"""
    
    list_display = [
        'action', 'content_object_str', 'user', 'ip_address', 
        'is_sensitive', 'requires_review', 'timestamp'
    ]
    list_filter = [
        'action', 'is_sensitive', 'requires_review', 'timestamp'
    ]
    search_fields = ['description', 'request_path', 'user__username']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Entity Information', {
            'fields': ('content_type', 'object_id', 'content_object')
        }),
        ('Action Details', {
            'fields': ('action', 'description', 'user', 'session_key')
        }),
        ('Request Context', {
            'fields': ('ip_address', 'user_agent', 'request_path', 'request_method')
        }),
        ('Change Details', {
            'fields': ('old_values', 'new_values', 'changed_fields')
        }),
        ('Compliance', {
            'fields': ('is_sensitive', 'requires_review', 'compliance_flags')
        }),
        ('Impersonation', {
            'fields': ('impersonated_by',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        })
    )
    
    def content_object_str(self, obj):
        """String representation of content object"""
        if obj.content_object:
            return str(obj.content_object)
        return 'N/A'
    content_object_str.short_description = 'Object'

@admin.register(AuditPolicy)
class AuditPolicyAdmin(admin.ModelAdmin):
    """Audit policy admin interface"""
    
    list_display = [
        'name', 'policy_type', 'is_active', 'priority', 
        'compliance_standard', 'created_by', 'created_at'
    ]
    list_filter = [
        'policy_type', 'is_active', 'compliance_standard', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('name', 'description', 'policy_type', 'is_active', 'priority')
        }),
        ('Monitoring Rules', {
            'fields': ('target_models', 'target_actions', 'conditions')
        }),
        ('Retention Settings', {
            'fields': ('retention_period', 'auto_archive', 'auto_delete')
        }),
        ('Alert Settings', {
            'fields': ('alert_enabled', 'alert_recipients', 'alert_threshold')
        }),
        ('Compliance Settings', {
            'fields': ('compliance_standard', 'review_required', 'review_frequency')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AuditReview)
class AuditReviewAdmin(admin.ModelAdmin):
    """Audit review admin interface"""
    
    list_display = [
        'audit_log', 'policy', 'status', 'reviewer', 
        'risk_assessment', 'assigned_at'
    ]
    list_filter = [
        'status', 'risk_assessment', 'follow_up_required', 'assigned_at'
    ]
    search_fields = ['review_notes', 'compliance_notes', 'reviewer__username']
    readonly_fields = ['assigned_at']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('audit_log', 'policy', 'status', 'reviewer')
        }),
        ('Review Details', {
            'fields': ('review_notes', 'compliance_notes', 'risk_assessment')
        }),
        ('Action Taken', {
            'fields': ('action_taken', 'follow_up_required', 'follow_up_date')
        }),
        ('Timestamps', {
            'fields': ('assigned_at', 'reviewed_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    """Compliance report admin interface"""
    
    list_display = [
        'name', 'report_type', 'status', 'compliance_standard',
        'compliance_score', 'violations_count', 'generated_by', 'generated_at'
    ]
    list_filter = [
        'report_type', 'status', 'compliance_standard', 'generated_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['generated_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('name', 'description', 'report_type', 'status')
        }),
        ('Date Range', {
            'fields': ('date_range_start', 'date_range_end', 'filters')
        }),
        ('Report Content', {
            'fields': ('summary', 'findings', 'recommendations')
        }),
        ('Compliance Details', {
            'fields': ('compliance_standard', 'compliance_score', 'violations_count', 'critical_issues')
        }),
        ('Export Options', {
            'fields': ('export_format', 'export_path')
        }),
        ('Metadata', {
            'fields': ('generated_by', 'generated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AuditExport)
class AuditExportAdmin(admin.ModelAdmin):
    """Audit export admin interface"""
    
    list_display = [
        'name', 'status', 'format', 'record_count', 'file_size',
        'requested_by', 'requested_at', 'completed_at'
    ]
    list_filter = [
        'status', 'format', 'include_sensitive', 'anonymize_data', 'requested_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['requested_at', 'started_at', 'completed_at']
    
    fieldsets = (
        ('Export Information', {
            'fields': ('name', 'description', 'status')
        }),
        ('Date Range', {
            'fields': ('date_range_start', 'date_range_end', 'filters')
        }),
        ('Export Settings', {
            'fields': ('format', 'include_sensitive', 'anonymize_data', 'compression_enabled')
        }),
        ('Results', {
            'fields': ('file_path', 'file_size', 'record_count')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('requested_by',),
            'classes': ('collapse',)
        })
    )
