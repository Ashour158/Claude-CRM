# workflow/models.py
# Workflow and business process management models

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class Workflow(CompanyIsolatedModel):
    """Workflow definitions"""
    
    WORKFLOW_TYPES = [
        ('approval', 'Approval Workflow'),
        ('notification', 'Notification Workflow'),
        ('automation', 'Automation Workflow'),
        ('escalation', 'Escalation Workflow'),
        ('custom', 'Custom Workflow'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    workflow_type = models.CharField(
        max_length=20,
        choices=WORKFLOW_TYPES,
        default='custom'
    )
    
    # Workflow Configuration
    trigger_conditions = models.JSONField(
        default=dict,
        help_text="Workflow trigger conditions"
    )
    steps = models.JSONField(
        default=list,
        help_text="Workflow steps configuration"
    )
    rules = models.JSONField(
        default=dict,
        help_text="Workflow business rules"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_active = models.BooleanField(default=True)
    is_global = models.BooleanField(
        default=False,
        help_text="Available to all companies"
    )
    
    # Execution
    execution_count = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_workflows'
    )
    
    class Meta:
        db_table = 'workflow'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class WorkflowTrigger(CompanyIsolatedModel):
    """Workflow triggers - defines when a workflow should execute"""
    
    EVENT_TYPES = [
        ('timeline.event', 'Timeline Event'),
        ('lead.created', 'Lead Created'),
        ('lead.converted', 'Lead Converted'),
        ('deal.stage_changed', 'Deal Stage Changed'),
        ('deal.won', 'Deal Won'),
        ('deal.lost', 'Deal Lost'),
        ('contact.created', 'Contact Created'),
        ('account.created', 'Account Created'),
        ('custom', 'Custom Event'),
    ]
    
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='triggers'
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        db_index=True,
        help_text="Type of event that triggers this workflow"
    )
    conditions = models.JSONField(
        default=dict,
        help_text="Conditions that must be met for trigger to fire (DSL format)"
    )
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Trigger priority for ordering")
    
    class Meta:
        db_table = 'workflow_trigger'
        ordering = ['-priority', 'event_type']
    
    def __str__(self):
        return f"{self.workflow.name} - {self.event_type}"

class WorkflowAction(CompanyIsolatedModel):
    """Workflow actions - defines what to do when workflow executes"""
    
    ACTION_TYPES = [
        ('send_email', 'Send Email'),
        ('add_note', 'Add Note'),
        ('update_field', 'Update Field'),
        ('enqueue_export', 'Enqueue Export'),
        ('create_task', 'Create Task'),
        ('send_notification', 'Send Notification'),
        ('call_webhook', 'Call Webhook'),
        ('custom', 'Custom Action'),
    ]
    
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='actions'
    )
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        help_text="Type of action to execute"
    )
    payload = models.JSONField(
        default=dict,
        help_text="Action configuration and parameters"
    )
    ordering = models.IntegerField(
        default=0,
        help_text="Order of execution within workflow"
    )
    is_active = models.BooleanField(default=True)
    allow_failure = models.BooleanField(
        default=False,
        help_text="Whether workflow should continue if this action fails"
    )
    
    class Meta:
        db_table = 'workflow_action'
        ordering = ['ordering', 'action_type']
    
    def __str__(self):
        return f"{self.workflow.name} - {self.action_type} (#{self.ordering})"

class WorkflowRun(CompanyIsolatedModel):
    """Workflow run instance - tracks execution of a workflow"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='runs'
    )
    trigger = models.ForeignKey(
        WorkflowTrigger,
        on_delete=models.SET_NULL,
        null=True,
        related_name='runs'
    )
    
    # Execution context
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='workflow_runs'
    )
    trigger_data = models.JSONField(
        default=dict,
        help_text="Data that triggered the workflow"
    )
    context_data = models.JSONField(
        default=dict,
        help_text="Additional context for workflow execution"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True, help_text="Execution duration in milliseconds")
    
    # Results
    success = models.BooleanField(default=False)
    result_data = models.JSONField(
        default=dict,
        help_text="Workflow execution results"
    )
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'workflow_run'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow', 'status', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.workflow.name} run at {self.created_at}"

class WorkflowActionRun(CompanyIsolatedModel):
    """Workflow action run - tracks execution of individual actions"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    workflow_run = models.ForeignKey(
        WorkflowRun,
        on_delete=models.CASCADE,
        related_name='action_runs'
    )
    action = models.ForeignKey(
        WorkflowAction,
        on_delete=models.CASCADE,
        related_name='runs'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    
    # Results
    success = models.BooleanField(default=False)
    result_data = models.JSONField(
        default=dict,
        help_text="Action execution results"
    )
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'workflow_action_run'
        ordering = ['action__ordering', 'created_at']
    
    def __str__(self):
        return f"{self.action.action_type} for run {self.workflow_run.id}"

class WorkflowExecution(CompanyIsolatedModel):
    """Workflow execution instances"""
    
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('paused', 'Paused'),
    ]
    
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    
    # Execution Details
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='triggered_workflows'
    )
    trigger_data = models.JSONField(
        default=dict,
        help_text="Data that triggered the workflow"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='running'
    )
    current_step = models.IntegerField(default=0)
    total_steps = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    result_data = models.JSONField(
        default=dict,
        help_text="Workflow execution results"
    )
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'workflow_execution'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.workflow.name} - {self.started_at}"

class ApprovalProcess(CompanyIsolatedModel):
    """Approval processes for records"""
    
    PROCESS_TYPES = [
        ('sequential', 'Sequential Approval'),
        ('parallel', 'Parallel Approval'),
        ('conditional', 'Conditional Approval'),
        ('escalation', 'Escalation Approval'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    process_type = models.CharField(
        max_length=20,
        choices=PROCESS_TYPES,
        default='sequential'
    )
    
    # Process Configuration
    entity_type = models.CharField(
        max_length=100,
        help_text="Entity type this process applies to"
    )
    approval_rules = models.JSONField(
        default=dict,
        help_text="Approval rules and conditions"
    )
    approvers = models.JSONField(
        default=list,
        help_text="List of approvers"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_active = models.BooleanField(default=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_approval_processes'
    )
    
    class Meta:
        db_table = 'approval_process'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ApprovalRequest(CompanyIsolatedModel):
    """Approval requests for records"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    approval_process = models.ForeignKey(
        ApprovalProcess,
        on_delete=models.CASCADE,
        related_name='requests'
    )
    
    # Request Details
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    entity_data = models.JSONField(
        default=dict,
        help_text="Entity data being approved"
    )
    
    # Requestor
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approval_requests'
    )
    request_reason = models.TextField(blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Timing
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_requests'
    )
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'approval_request'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.approval_process.name} - {self.entity_type} {self.entity_id}"

class BusinessRule(CompanyIsolatedModel):
    """Business rules for automation"""
    
    RULE_TYPES = [
        ('validation', 'Validation Rule'),
        ('calculation', 'Calculation Rule'),
        ('assignment', 'Assignment Rule'),
        ('notification', 'Notification Rule'),
        ('escalation', 'Escalation Rule'),
        ('custom', 'Custom Rule'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPES,
        default='custom'
    )
    
    # Rule Configuration
    entity_type = models.CharField(
        max_length=100,
        help_text="Entity type this rule applies to"
    )
    conditions = models.JSONField(
        default=dict,
        help_text="Rule conditions"
    )
    actions = models.JSONField(
        default=list,
        help_text="Rule actions"
    )
    priority = models.IntegerField(
        default=0,
        help_text="Rule priority (higher number = higher priority)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_global = models.BooleanField(
        default=False,
        help_text="Apply to all companies"
    )
    
    # Execution
    execution_count = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_business_rules'
    )
    
    class Meta:
        db_table = 'business_rule'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return self.name

class BusinessRuleExecution(CompanyIsolatedModel):
    """Business rule execution logs"""
    
    business_rule = models.ForeignKey(
        BusinessRule,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    
    # Execution Details
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    execution_data = models.JSONField(
        default=dict,
        help_text="Data used in rule execution"
    )
    
    # Results
    success = models.BooleanField(default=True)
    result_data = models.JSONField(
        default=dict,
        help_text="Rule execution results"
    )
    error_message = models.TextField(blank=True)
    
    # Timing
    executed_at = models.DateTimeField(auto_now_add=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'business_rule_execution'
        ordering = ['-executed_at']
    
    def __str__(self):
        return f"{self.business_rule.name} - {self.executed_at}"

class ProcessTemplate(CompanyIsolatedModel):
    """Process templates for common workflows"""
    
    TEMPLATE_TYPES = [
        ('onboarding', 'Onboarding'),
        ('offboarding', 'Offboarding'),
        ('approval', 'Approval'),
        ('notification', 'Notification'),
        ('escalation', 'Escalation'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPES,
        default='custom'
    )
    
    # Template Configuration
    process_steps = models.JSONField(
        default=list,
        help_text="Process steps configuration"
    )
    variables = models.JSONField(
        default=list,
        help_text="Template variables"
    )
    settings = models.JSONField(
        default=dict,
        help_text="Template settings"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(
        default=False,
        help_text="Available to all companies"
    )
    
    # Usage
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_process_templates'
    )
    
    class Meta:
        db_table = 'process_template'
        ordering = ['name']
    
    def __str__(self):
        return self.name