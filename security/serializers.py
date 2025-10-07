# security/serializers.py
# Enterprise Security Serializers

from rest_framework import serializers
from .models import (
    SecurityPolicy, SSOConfiguration, SCIMConfiguration, IPAllowlist,
    DeviceManagement, SessionManagement, AuditLog, SecurityIncident,
    DataRetentionPolicy
)

class SecurityPolicySerializer(serializers.ModelSerializer):
    """Security policy serializer"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = SecurityPolicy
        fields = [
            'id', 'name', 'description', 'policy_type', 'configuration',
            'rules', 'status', 'is_active', 'enforcement_level', 'owner',
            'owner_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SSOConfigurationSerializer(serializers.ModelSerializer):
    """SSO configuration serializer"""
    
    class Meta:
        model = SSOConfiguration
        fields = [
            'id', 'name', 'description', 'provider_type', 'configuration',
            'credentials', 'status', 'is_active', 'last_test', 'test_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SCIMConfigurationSerializer(serializers.ModelSerializer):
    """SCIM configuration serializer"""
    
    class Meta:
        model = SCIMConfiguration
        fields = [
            'id', 'name', 'description', 'endpoint_url', 'bearer_token',
            'status', 'is_active', 'total_syncs', 'successful_syncs',
            'failed_syncs', 'last_sync', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class IPAllowlistSerializer(serializers.ModelSerializer):
    """IP allowlist serializer"""
    
    class Meta:
        model = IPAllowlist
        fields = [
            'id', 'name', 'description', 'allowlist_type', 'ip_addresses',
            'countries', 'is_active', 'total_requests', 'blocked_requests',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class DeviceManagementSerializer(serializers.ModelSerializer):
    """Device management serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = DeviceManagement
        fields = [
            'id', 'device_id', 'device_name', 'device_type', 'operating_system',
            'os_version', 'app_version', 'device_model', 'manufacturer', 'user',
            'user_name', 'status', 'is_trusted', 'push_token', 'fingerprint',
            'encryption_key', 'last_seen', 'total_sessions', 'last_ip_address',
            'app_config', 'user_preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'device_id', 'created_at', 'updated_at']

class SessionManagementSerializer(serializers.ModelSerializer):
    """Session management serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = SessionManagement
        fields = [
            'id', 'session_id', 'session_type', 'device', 'device_name',
            'user', 'user_name', 'app_version', 'ip_address', 'user_agent',
            'location', 'status', 'started_at', 'last_activity', 'expires_at',
            'terminated_at', 'is_secure', 'encryption_key', 'session_data',
            'offline_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'session_id', 'created_at', 'updated_at']

class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    session_id_display = serializers.CharField(source='session.session_id', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'event_type', 'event_name', 'description', 'user', 'user_name',
            'session', 'session_id_display', 'ip_address', 'user_agent', 'location',
            'severity', 'is_successful', 'event_data', 'metadata', 'content_type',
            'object_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SecurityIncidentSerializer(serializers.ModelSerializer):
    """Security incident serializer"""
    
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = SecurityIncident
        fields = [
            'id', 'incident_id', 'title', 'description', 'incident_type',
            'severity', 'status', 'affected_users', 'affected_systems',
            'assigned_to', 'assigned_to_name', 'investigation_notes',
            'detected_at', 'resolved_at', 'impact_assessment',
            'remediation_actions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'incident_id', 'created_at', 'updated_at']

class DataRetentionPolicySerializer(serializers.ModelSerializer):
    """Data retention policy serializer"""
    
    class Meta:
        model = DataRetentionPolicy
        fields = [
            'id', 'name', 'description', 'retention_type', 'retention_period_days',
            'auto_delete', 'archive_before_delete', 'is_active', 'total_records',
            'deleted_records', 'last_cleanup', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
