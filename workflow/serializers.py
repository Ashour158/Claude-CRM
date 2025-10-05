# workflow/serializers.py
# Workflow serializers

from rest_framework import serializers
from .models import (
    Workflow, WorkflowExecution, ApprovalProcess, ApprovalRequest,
    BusinessRule, BusinessRuleExecution, ProcessTemplate
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
