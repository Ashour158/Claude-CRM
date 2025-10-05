# system_config/serializers.py
# System configuration serializers

from rest_framework import serializers
from .models import (
    SystemSetting, CustomField, WorkflowRule, NotificationTemplate,
    UserPreference, Integration, AuditLog
)
from core.serializers import UserSerializer

class SystemSettingSerializer(serializers.ModelSerializer):
    """System setting serializer"""
    
    class Meta:
        model = SystemSetting
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class CustomFieldSerializer(serializers.ModelSerializer):
    """Custom field serializer"""
    
    class Meta:
        model = CustomField
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class WorkflowRuleSerializer(serializers.ModelSerializer):
    """Workflow rule serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = WorkflowRule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Notification template serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserPreferenceSerializer(serializers.ModelSerializer):
    """User preference serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserPreference
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class IntegrationSerializer(serializers.ModelSerializer):
    """Integration serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Integration
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']