# mobile/serializers.py
# Mobile Application Serializers

from rest_framework import serializers
from .models import (
    MobileDevice, MobileSession, OfflineData, PushNotification,
    MobileAppConfig, MobileAnalytics, MobileCrash
)

class MobileDeviceSerializer(serializers.ModelSerializer):
    """Mobile device serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = MobileDevice
        fields = [
            'id', 'device_id', 'device_name', 'device_type', 'operating_system',
            'os_version', 'app_version', 'device_model', 'manufacturer', 'user',
            'user_name', 'status', 'is_trusted', 'push_token', 'fingerprint',
            'encryption_key', 'last_seen', 'total_sessions', 'last_ip_address',
            'app_config', 'user_preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'device_id', 'created_at', 'updated_at']

class MobileSessionSerializer(serializers.ModelSerializer):
    """Mobile session serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = MobileSession
        fields = [
            'id', 'session_id', 'session_type', 'device', 'device_name',
            'user', 'user_name', 'app_version', 'ip_address', 'user_agent',
            'location', 'status', 'started_at', 'last_activity', 'expires_at',
            'terminated_at', 'is_secure', 'encryption_key', 'session_data',
            'offline_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'session_id', 'created_at', 'updated_at']

class OfflineDataSerializer(serializers.ModelSerializer):
    """Offline data serializer"""
    
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    session_id = serializers.CharField(source='session.session_id', read_only=True)
    
    class Meta:
        model = OfflineData
        fields = [
            'id', 'device', 'device_name', 'session', 'session_id',
            'sync_type', 'entity_type', 'entity_id', 'data', 'metadata',
            'status', 'created_at', 'synced_at', 'last_modified',
            'has_conflict', 'conflict_data', 'resolution_strategy',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PushNotificationSerializer(serializers.ModelSerializer):
    """Push notification serializer"""
    
    class Meta:
        model = PushNotification
        fields = [
            'id', 'title', 'message', 'notification_type', 'devices',
            'users', 'payload', 'action_url', 'scheduled_at', 'expires_at',
            'status', 'sent_at', 'delivered_at', 'opened_at', 'total_sent',
            'total_delivered', 'total_opened', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class MobileAppConfigSerializer(serializers.ModelSerializer):
    """Mobile app configuration serializer"""
    
    class Meta:
        model = MobileAppConfig
        fields = [
            'id', 'config_type', 'name', 'description', 'configuration',
            'version', 'target_devices', 'target_users', 'is_active',
            'is_required', 'effective_from', 'effective_until',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class MobileAnalyticsSerializer(serializers.ModelSerializer):
    """Mobile analytics serializer"""
    
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    session_id = serializers.CharField(source='session.session_id', read_only=True)
    
    class Meta:
        model = MobileAnalytics
        fields = [
            'id', 'device', 'device_name', 'session', 'session_id',
            'metric_type', 'metric_name', 'metric_value', 'metric_unit',
            'screen_name', 'action_name', 'user_id', 'properties',
            'context_data', 'timestamp', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class MobileCrashSerializer(serializers.ModelSerializer):
    """Mobile crash serializer"""
    
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    session_id = serializers.CharField(source='session.session_id', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = MobileCrash
        fields = [
            'id', 'device', 'device_name', 'session', 'session_id',
            'crash_id', 'error_type', 'error_message', 'stack_trace',
            'severity', 'status', 'app_version', 'os_version',
            'device_model', 'crash_data', 'user_actions', 'assigned_to',
            'assigned_to_name', 'resolution_notes', 'fixed_in_version',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'crash_id', 'created_at', 'updated_at']
