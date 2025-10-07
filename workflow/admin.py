# workflow/admin.py
# Django admin for workflow models

from django.contrib import admin
from .models import (
    Workflow, WorkflowExecution, ApprovalProcess, ApprovalRequest,
    BusinessRule, BusinessRuleExecution, ProcessTemplate,
    ActionCatalog, WorkflowSuggestion, WorkflowSimulation,
    WorkflowSLA, SLABreach
)


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    """Admin for Workflow model"""
    list_display = ['name', 'workflow_type', 'status', 'is_active', 'execution_count', 'created_at']
    list_filter = ['workflow_type', 'status', 'is_active', 'is_global']
    search_fields = ['name', 'description']
    readonly_fields = ['execution_count', 'last_executed', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'workflow_type', 'company', 'owner')
        }),
        ('Configuration', {
            'fields': ('trigger_conditions', 'steps', 'rules')
        }),
        ('Status', {
            'fields': ('status', 'is_active', 'is_global')
        }),
        ('Execution Stats', {
            'fields': ('execution_count', 'last_executed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    """Admin for WorkflowExecution model"""
    list_display = ['workflow', 'status', 'triggered_by', 'current_step', 'total_steps', 'started_at']
    list_filter = ['status', 'workflow']
    search_fields = ['workflow__name']
    readonly_fields = ['started_at', 'completed_at', 'paused_at', 'created_at', 'updated_at']


@admin.register(ActionCatalog)
class ActionCatalogAdmin(admin.ModelAdmin):
    """Admin for ActionCatalog model"""
    list_display = ['name', 'action_type', 'is_idempotent', 'latency_class', 'success_rate', 'is_active']
    list_filter = ['action_type', 'is_idempotent', 'latency_class', 'is_active', 'is_global']
    search_fields = ['name', 'description']
    readonly_fields = ['execution_count', 'avg_execution_time_ms', 'success_rate', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'action_type', 'company')
        }),
        ('Metadata', {
            'fields': ('is_idempotent', 'latency_class', 'side_effects')
        }),
        ('Schema', {
            'fields': ('input_schema', 'output_schema'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('execution_count', 'avg_execution_time_ms', 'success_rate')
        }),
        ('Status', {
            'fields': ('is_active', 'is_global')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkflowSuggestion)
class WorkflowSuggestionAdmin(admin.ModelAdmin):
    """Admin for WorkflowSuggestion model"""
    list_display = ['title', 'source', 'confidence_score', 'pattern_frequency', 'status', 'created_at']
    list_filter = ['source', 'status']
    search_fields = ['title', 'description']
    readonly_fields = ['reviewed_at', 'created_at', 'updated_at']
    fieldsets = (
        ('Suggestion Details', {
            'fields': ('title', 'description', 'source', 'company')
        }),
        ('Workflow Template', {
            'fields': ('workflow_template', 'confidence_score')
        }),
        ('Supporting Data', {
            'fields': ('supporting_data', 'pattern_frequency'),
            'classes': ('collapse',)
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkflowSimulation)
class WorkflowSimulationAdmin(admin.ModelAdmin):
    """Admin for WorkflowSimulation model"""
    list_display = ['workflow', 'status', 'created_by', 'predicted_duration_ms', 'started_at']
    list_filter = ['status', 'workflow']
    search_fields = ['workflow__name']
    readonly_fields = ['started_at', 'completed_at', 'created_at', 'updated_at']
    fieldsets = (
        ('Simulation Details', {
            'fields': ('workflow', 'company', 'created_by', 'input_data', 'status')
        }),
        ('Results', {
            'fields': ('execution_path', 'branch_explorations', 'approval_chain', 'predicted_duration_ms')
        }),
        ('Validation', {
            'fields': ('validation_errors', 'warnings'),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkflowSLA)
class WorkflowSLAAdmin(admin.ModelAdmin):
    """Admin for WorkflowSLA model"""
    list_display = ['workflow', 'name', 'target_duration_seconds', 'current_slo_percentage', 
                   'total_executions', 'breached_executions', 'is_active']
    list_filter = ['is_active', 'workflow']
    search_fields = ['name', 'description', 'workflow__name']
    readonly_fields = ['total_executions', 'breached_executions', 'current_slo_percentage', 
                      'created_at', 'updated_at']
    fieldsets = (
        ('SLA Configuration', {
            'fields': ('workflow', 'company', 'name', 'description', 'is_active')
        }),
        ('Thresholds', {
            'fields': ('target_duration_seconds', 'warning_threshold_seconds', 'critical_threshold_seconds')
        }),
        ('SLO Window', {
            'fields': ('slo_window_hours', 'slo_target_percentage')
        }),
        ('Statistics', {
            'fields': ('total_executions', 'breached_executions', 'current_slo_percentage')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SLABreach)
class SLABreachAdmin(admin.ModelAdmin):
    """Admin for SLABreach model"""
    list_display = ['sla', 'workflow_execution', 'severity', 'breach_margin_seconds', 
                   'alert_sent', 'acknowledged', 'detected_at']
    list_filter = ['severity', 'alert_sent', 'acknowledged', 'sla']
    search_fields = ['sla__name', 'sla__workflow__name']
    readonly_fields = ['detected_at', 'alert_sent_at', 'acknowledged_at', 'created_at', 'updated_at']
    fieldsets = (
        ('Breach Details', {
            'fields': ('sla', 'workflow_execution', 'company', 'severity')
        }),
        ('Metrics', {
            'fields': ('actual_duration_seconds', 'target_duration_seconds', 'breach_margin_seconds')
        }),
        ('Alert', {
            'fields': ('alert_sent', 'alert_sent_at', 'alert_recipients')
        }),
        ('Resolution', {
            'fields': ('acknowledged', 'acknowledged_by', 'acknowledged_at', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('detected_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProcessTemplate)
class ProcessTemplateAdmin(admin.ModelAdmin):
    """Admin for ProcessTemplate model"""
    list_display = ['name', 'template_type', 'version', 'is_active', 'is_public', 'usage_count', 'created_at']
    list_filter = ['template_type', 'is_active', 'is_public']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'last_used', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'template_type', 'company', 'owner')
        }),
        ('Blueprint', {
            'fields': ('version', 'graph_spec')
        }),
        ('Configuration', {
            'fields': ('process_steps', 'variables', 'settings'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_public')
        }),
        ('Usage', {
            'fields': ('usage_count', 'last_used')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Register remaining models with simple admin
admin.site.register(ApprovalProcess)
admin.site.register(ApprovalRequest)
admin.site.register(BusinessRule)
admin.site.register(BusinessRuleExecution)
