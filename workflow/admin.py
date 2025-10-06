# workflow/admin.py
# Django Admin Configuration for Workflow Models

from django.contrib import admin
from .models import (
    Workflow, WorkflowExecution, ApprovalProcess, ApprovalRequest,
    BusinessRule, BusinessRuleExecution, ProcessTemplate, WorkflowApproval
)


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    """Workflow admin interface"""
    list_display = ['name', 'workflow_type', 'status', 'is_active', 'execution_count', 'created_at']
    list_filter = ['workflow_type', 'status', 'is_active', 'is_global', 'company']
    search_fields = ['name', 'description']
    ordering = ['name']
    raw_id_fields = ['owner']


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    """Workflow execution admin interface"""
    list_display = ['workflow', 'status', 'current_step', 'total_steps', 'started_at', 'completed_at']
    list_filter = ['status', 'workflow__company']
    search_fields = ['workflow__name']
    ordering = ['-started_at']
    raw_id_fields = ['workflow', 'triggered_by']


@admin.register(ApprovalProcess)
class ApprovalProcessAdmin(admin.ModelAdmin):
    """Approval process admin interface"""
    list_display = ['name', 'process_type', 'status', 'is_active', 'entity_type', 'created_at']
    list_filter = ['process_type', 'status', 'is_active', 'company']
    search_fields = ['name', 'description', 'entity_type']
    ordering = ['name']
    raw_id_fields = ['owner']


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    """Approval request admin interface"""
    list_display = ['approval_process', 'entity_type', 'entity_id', 'status', 'requested_by', 'requested_at']
    list_filter = ['status', 'approval_process__company']
    search_fields = ['entity_type', 'entity_id']
    ordering = ['-requested_at']
    raw_id_fields = ['approval_process', 'requested_by', 'approved_by']


@admin.register(BusinessRule)
class BusinessRuleAdmin(admin.ModelAdmin):
    """Business rule admin interface"""
    list_display = ['name', 'rule_type', 'entity_type', 'priority', 'is_active', 'execution_count']
    list_filter = ['rule_type', 'is_active', 'is_global', 'company']
    search_fields = ['name', 'description', 'entity_type']
    ordering = ['-priority', 'name']
    raw_id_fields = ['owner']


@admin.register(BusinessRuleExecution)
class BusinessRuleExecutionAdmin(admin.ModelAdmin):
    """Business rule execution admin interface"""
    list_display = ['business_rule', 'entity_type', 'entity_id', 'success', 'executed_at']
    list_filter = ['success', 'business_rule__company']
    search_fields = ['entity_type', 'entity_id']
    ordering = ['-executed_at']
    raw_id_fields = ['business_rule']


@admin.register(ProcessTemplate)
class ProcessTemplateAdmin(admin.ModelAdmin):
    """Process template admin interface"""
    list_display = ['name', 'template_type', 'is_active', 'is_public', 'usage_count', 'created_at']
    list_filter = ['template_type', 'is_active', 'is_public', 'company']
    search_fields = ['name', 'description']
    ordering = ['name']
    raw_id_fields = ['owner']


@admin.register(WorkflowApproval)
class WorkflowApprovalAdmin(admin.ModelAdmin):
    """Workflow approval admin interface"""
    list_display = [
        'id', 'workflow_run_id', 'action_run_id', 'status',
        'approver_role', 'escalate_role', 'expires_at',
        'resolved_at', 'created_at'
    ]
    list_filter = ['status', 'approver_role', 'company', 'created_at']
    search_fields = ['workflow_run_id', 'action_run_id', 'approver_role', 'escalate_role']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    
    fieldsets = (
        ('Workflow References', {
            'fields': ('company', 'workflow_run_id', 'action_run_id')
        }),
        ('Approval Configuration', {
            'fields': ('approver_role', 'escalate_role', 'expires_at')
        }),
        ('Status', {
            'fields': ('status', 'resolved_at', 'actor_id')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Allow adding approvals through admin for testing"""
        return True
    
    def has_change_permission(self, request, obj=None):
        """Allow changing approvals through admin for testing"""
        return True
