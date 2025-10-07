# workflow/serializers.py
# Workflow serializers

from rest_framework import serializers
from .models import (
    Workflow, WorkflowExecution, ApprovalProcess, ApprovalRequest,
    BusinessRule, BusinessRuleExecution, ProcessTemplate,
    ActionCatalog, WorkflowSuggestion, WorkflowSimulation,
    WorkflowSLA, SLABreach
)
from core.serializers import UserSerializer

class WorkflowSerializer(serializers.ModelSerializer):
    """Workflow serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Workflow
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class WorkflowExecutionSerializer(serializers.ModelSerializer):
    """Workflow execution serializer"""
    triggered_by = UserSerializer(read_only=True)
    
    class Meta:
        model = WorkflowExecution
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ApprovalProcessSerializer(serializers.ModelSerializer):
    """Approval process serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = ApprovalProcess
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ApprovalRequestSerializer(serializers.ModelSerializer):
    """Approval request serializer"""
    requested_by = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ApprovalRequest
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class BusinessRuleSerializer(serializers.ModelSerializer):
    """Business rule serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = BusinessRule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class BusinessRuleExecutionSerializer(serializers.ModelSerializer):
    """Business rule execution serializer"""
    
    class Meta:
        model = BusinessRuleExecution
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ProcessTemplateSerializer(serializers.ModelSerializer):
    """Process template serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = ProcessTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ActionCatalogSerializer(serializers.ModelSerializer):
    """Action catalog serializer"""
    
    class Meta:
        model = ActionCatalog
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'execution_count', 
                           'avg_execution_time_ms', 'success_rate']


class WorkflowSuggestionSerializer(serializers.ModelSerializer):
    """Workflow suggestion serializer"""
    reviewed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = WorkflowSuggestion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkflowSimulationSerializer(serializers.ModelSerializer):
    """Workflow simulation serializer"""
    created_by = UserSerializer(read_only=True)
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    
    class Meta:
        model = WorkflowSimulation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'started_at']


class WorkflowSLASerializer(serializers.ModelSerializer):
    """Workflow SLA serializer"""
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    
    class Meta:
        model = WorkflowSLA
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_executions',
                           'breached_executions', 'current_slo_percentage']


class SLABreachSerializer(serializers.ModelSerializer):
    """SLA breach serializer"""
    sla_name = serializers.CharField(source='sla.name', read_only=True)
    workflow_name = serializers.CharField(source='sla.workflow.name', read_only=True)
    acknowledged_by_user = UserSerializer(source='acknowledged_by', read_only=True)
    
    class Meta:
        model = SLABreach
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'detected_at']
