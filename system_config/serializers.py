# system_config/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    CustomField, CustomFieldValue, SystemPreference, WorkflowConfiguration,
    UserPreference, SystemLog, SystemHealth, DataBackup
)

User = get_user_model()

class CustomFieldSerializer(serializers.ModelSerializer):
    """Serializer for CustomField model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = CustomField
        fields = [
            'id', 'name', 'label', 'field_type', 'description', 'model_name',
            'is_required', 'is_unique', 'default_value', 'options',
            'min_length', 'max_length', 'min_value', 'max_value',
            'sequence', 'is_visible', 'help_text', 'owner', 'owner_name',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CustomFieldValueSerializer(serializers.ModelSerializer):
    """Serializer for CustomFieldValue model"""
    field_name = serializers.CharField(source='field.name', read_only=True)
    field_label = serializers.CharField(source='field.label', read_only=True)
    field_type = serializers.CharField(source='field.field_type', read_only=True)
    
    class Meta:
        model = CustomFieldValue
        fields = [
            'id', 'field', 'field_name', 'field_label', 'field_type',
            'object_id', 'value', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SystemPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for SystemPreference model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = SystemPreference
        fields = [
            'id', 'key', 'value', 'category', 'description', 'data_type',
            'owner', 'owner_name', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class WorkflowConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowConfiguration model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = WorkflowConfiguration
        fields = [
            'id', 'name', 'description', 'workflow_type', 'trigger_model',
            'trigger_conditions', 'actions', 'owner', 'owner_name',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for UserPreference model"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = UserPreference
        fields = [
            'id', 'user', 'user_name', 'key', 'value', 'category',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SystemLogSerializer(serializers.ModelSerializer):
    """Serializer for SystemLog model"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = SystemLog
        fields = [
            'id', 'level', 'category', 'message', 'user', 'user_name',
            'object_type', 'object_id', 'metadata', 'ip_address',
            'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class SystemHealthSerializer(serializers.ModelSerializer):
    """Serializer for SystemHealth model"""
    
    class Meta:
        model = SystemHealth
        fields = [
            'id', 'component', 'status', 'message', 'response_time',
            'memory_usage', 'cpu_usage', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class DataBackupSerializer(serializers.ModelSerializer):
    """Serializer for DataBackup model"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = DataBackup
        fields = [
            'id', 'name', 'description', 'backup_type', 'status',
            'scheduled_at', 'started_at', 'completed_at', 'file_path',
            'file_size', 'created_by', 'created_by_name', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

# Bulk operation serializers
class BulkCustomFieldSerializer(serializers.Serializer):
    """Serializer for bulk custom field operations"""
    field_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of custom field IDs"
    )
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'delete'],
        help_text="Action to perform"
    )

class BulkSystemPreferenceSerializer(serializers.Serializer):
    """Serializer for bulk system preference operations"""
    preference_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of preference IDs"
    )
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'delete'],
        help_text="Action to perform"
    )

# Configuration serializers
class SystemConfigurationSerializer(serializers.Serializer):
    """Serializer for system configuration"""
    company_name = serializers.CharField()
    company_logo = serializers.URLField(required=False)
    timezone = serializers.CharField()
    currency = serializers.CharField()
    date_format = serializers.CharField()
    time_format = serializers.CharField()
    language = serializers.CharField()
    email_signature = serializers.CharField(required=False)
    notification_settings = serializers.JSONField()
    security_settings = serializers.JSONField()
    integration_settings = serializers.JSONField()

class UserConfigurationSerializer(serializers.Serializer):
    """Serializer for user configuration"""
    theme = serializers.CharField()
    language = serializers.CharField()
    timezone = serializers.CharField()
    date_format = serializers.CharField()
    time_format = serializers.CharField()
    email_notifications = serializers.BooleanField()
    sms_notifications = serializers.BooleanField()
    dashboard_layout = serializers.JSONField()
    notification_preferences = serializers.JSONField()

class WorkflowTriggerSerializer(serializers.Serializer):
    """Serializer for workflow triggers"""
    model_name = serializers.CharField()
    action = serializers.ChoiceField(choices=['create', 'update', 'delete'])
    conditions = serializers.JSONField()
    actions = serializers.JSONField()

class SystemMetricsSerializer(serializers.Serializer):
    """Serializer for system metrics"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_records = serializers.IntegerField()
    storage_used = serializers.IntegerField()
    api_calls_today = serializers.IntegerField()
    error_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    response_time = serializers.DecimalField(max_digits=8, decimal_places=2)
    uptime = serializers.DecimalField(max_digits=5, decimal_places=2)

class BackupConfigurationSerializer(serializers.Serializer):
    """Serializer for backup configuration"""
    backup_frequency = serializers.ChoiceField(choices=['daily', 'weekly', 'monthly'])
    retention_days = serializers.IntegerField()
    backup_location = serializers.CharField()
    encryption_enabled = serializers.BooleanField()
    compression_enabled = serializers.BooleanField()
    notification_emails = serializers.ListField(child=serializers.EmailField())

class SystemDiagnosticsSerializer(serializers.Serializer):
    """Serializer for system diagnostics"""
    database_status = serializers.CharField()
    cache_status = serializers.CharField()
    email_status = serializers.CharField()
    storage_status = serializers.CharField()
    api_status = serializers.CharField()
    worker_status = serializers.CharField()
    overall_health = serializers.CharField()
    recommendations = serializers.ListField(child=serializers.CharField())
