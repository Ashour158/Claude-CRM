# workflow/models.py
# Business Process Management for enterprise CRM

from django.db import models
from core.models import CompanyIsolatedModel, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
import json

class WorkflowDefinition(CompanyIsolatedModel):
    """Workflow definitions for business processes"""
    
    WORKFLOW_TYPES = [
        ('lead_management', 'Lead Management'),
        ('sales_process', 'Sales Process'),
        ('customer_onboarding', 'Customer Onboarding'),
        ('support_ticket', 'Support Ticket'),
        ('approval_process', 'Approval Process'),
        ('data_quality', 'Data Quality'),
        ('notification', 'Notification'),
    ]
    
    TRIGGER_TYPES = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('scheduled', 'Scheduled'),
        ('event_based', 'Event Based'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    workflow_type = models.CharField(max_length=50, choices=WORKFLOW_TYPES)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    trigger_conditions = models.JSONField(default=dict)  # Conditions for triggering
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=10, default='1.0')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_workflows')
    
    class Meta:
        unique_together = ('company', 'name', 'version')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class WorkflowStep(CompanyIsolatedModel):
    """Individual steps in a workflow"""
    
    STEP_TYPES = [
        ('action', 'Action'),
        ('condition', 'Condition'),
        ('approval', 'Approval'),
        ('notification', 'Notification'),
        ('data_update', 'Data Update'),
        ('integration', 'Integration'),
        ('delay', 'Delay'),
    ]
    
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=100)
    step_type = models.CharField(max_length=20, choices=STEP_TYPES)
    description = models.TextField(blank=True, null=True)
    step_order = models.IntegerField()
    configuration = models.JSONField(default=dict)  # Step-specific configuration
    is_required = models.BooleanField(default=True)
    timeout_minutes = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ('workflow', 'step_order')
        ordering = ['step_order']
    
    def __str__(self):
        return f"{self.workflow.name} - Step {self.step_order}: {self.name}"


class WorkflowInstance(CompanyIsolatedModel):
    """Running instances of workflows"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('paused', 'Paused'),
    ]
    
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='instances')
    instance_id = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='started_workflows')
    context_data = models.JSONField(default=dict)  # Workflow context and variables
    current_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_instances')
    
    # Generic foreign key to related object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.workflow.name} - {self.instance_id} - {self.status}"
    
    def get_next_step(self):
        """Get the next step in the workflow"""
        if self.current_step:
            return self.workflow.steps.filter(step_order__gt=self.current_step.step_order).first()
        else:
            return self.workflow.steps.filter(step_order=1).first()
    
    def advance_to_next_step(self):
        """Advance to the next step"""
        next_step = self.get_next_step()
        if next_step:
            self.current_step = next_step
            self.save(update_fields=['current_step'])
            return True
        else:
            # Workflow completed
            self.status = 'completed'
            self.completed_at = models.DateTimeField(auto_now=True)
            self.save(update_fields=['status', 'completed_at'])
            return False


class WorkflowStepExecution(CompanyIsolatedModel):
    """Execution records for workflow steps"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='step_executions')
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='executed_steps')
    result_data = models.JSONField(default=dict)  # Step execution results
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('instance', 'step')
        ordering = ['started_at']
    
    def __str__(self):
        return f"{self.instance} - {self.step.name} - {self.status}"


class ApprovalProcess(CompanyIsolatedModel):
    """Approval processes for business workflows"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approvals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    
    class Meta:
        unique_together = ('workflow_instance', 'approver')
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.workflow_instance} - {self.approver.email} - {self.status}"


class BusinessRule(CompanyIsolatedModel):
    """Business rules for workflow automation"""
    
    RULE_TYPES = [
        ('validation', 'Validation'),
        ('assignment', 'Assignment'),
        ('notification', 'Notification'),
        ('escalation', 'Escalation'),
        ('routing', 'Routing'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    conditions = models.JSONField(default=dict)  # Rule conditions
    actions = models.JSONField(default=dict)  # Actions to take when conditions are met
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_business_rules')
    
    class Meta:
        unique_together = ('company', 'name')
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.rule_type})"


class RuleExecution(CompanyIsolatedModel):
    """Execution records for business rules"""
    
    rule = models.ForeignKey(BusinessRule, on_delete=models.CASCADE, related_name='executions')
    triggered_by = models.CharField(max_length=100)  # What triggered the rule
    context_data = models.JSONField(default=dict)  # Context when rule was triggered
    executed_at = models.DateTimeField(auto_now_add=True)
    result = models.JSONField(default=dict)  # Rule execution result
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-executed_at']
    
    def __str__(self):
        return f"{self.rule.name} - {self.executed_at} - {'SUCCESS' if self.success else 'FAILED'}"


class WorkflowTemplate(CompanyIsolatedModel):
    """Templates for common workflows"""
    
    TEMPLATE_CATEGORIES = [
        ('sales', 'Sales'),
        ('marketing', 'Marketing'),
        ('support', 'Support'),
        ('hr', 'Human Resources'),
        ('finance', 'Finance'),
        ('operations', 'Operations'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=TEMPLATE_CATEGORIES)
    template_data = models.JSONField(default=dict)  # Template configuration
    is_public = models.BooleanField(default=False)  # Available to other companies
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_templates')
    usage_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('company', 'name')
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class WorkflowMetrics(CompanyIsolatedModel):
    """Metrics and analytics for workflows"""
    
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField()
    instances_started = models.IntegerField(default=0)
    instances_completed = models.IntegerField(default=0)
    instances_failed = models.IntegerField(default=0)
    average_duration_minutes = models.FloatField(default=0)
    step_executions = models.IntegerField(default=0)
    step_failures = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('workflow', 'date')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.workflow.name} - {self.date} - {self.instances_completed} completed"
