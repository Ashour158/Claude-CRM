# api_versioning/serializers.py
# API Versioning Serializers

from rest_framework import serializers
from .models import APIVersion, APIEndpoint, APIClient, APIRequestLog, APIDeprecationNotice

class APIVersionSerializer(serializers.ModelSerializer):
    """API version serializer"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    endpoint_count = serializers.SerializerMethodField()
    client_count = serializers.SerializerMethodField()
    
    class Meta:
        model = APIVersion
        fields = [
            'id', 'version', 'name', 'description', 'status', 'release_date',
            'deprecation_date', 'retirement_date', 'is_default', 'is_public',
            'requires_auth', 'changelog', 'migration_guide', 'breaking_changes',
            'created_by_name', 'endpoint_count', 'client_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_endpoint_count(self, obj):
        """Get number of endpoints for this version"""
        return obj.endpoints.count()
    
    def get_client_count(self, obj):
        """Get number of clients using this version"""
        return obj.primary_clients.count() + obj.supported_clients.count()

class APIEndpointSerializer(serializers.ModelSerializer):
    """API endpoint serializer"""
    
    version_name = serializers.CharField(source='version.name', read_only=True)
    
    class Meta:
        model = APIEndpoint
        fields = [
            'id', 'version', 'version_name', 'path', 'method', 'is_active',
            'is_deprecated', 'deprecation_notice', 'rate_limit', 'timeout',
            'description', 'parameters', 'response_schema', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class APIClientSerializer(serializers.ModelSerializer):
    """API client serializer"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    primary_version_name = serializers.CharField(source='primary_version.name', read_only=True)
    supported_versions_list = serializers.SerializerMethodField()
    request_count = serializers.SerializerMethodField()
    
    class Meta:
        model = APIClient
        fields = [
            'id', 'name', 'description', 'client_type', 'client_id', 'client_secret',
            'primary_version', 'primary_version_name', 'supported_versions',
            'supported_versions_list', 'is_active', 'rate_limit', 'contact_email',
            'contact_name', 'created_by_name', 'request_count', 'created_at',
            'updated_at', 'last_used'
        ]
        read_only_fields = ['id', 'client_id', 'created_at', 'updated_at']
    
    def get_supported_versions_list(self, obj):
        """Get list of supported version names"""
        return [v.name for v in obj.supported_versions.all()]
    
    def get_request_count(self, obj):
        """Get total request count for this client"""
        return obj.request_logs.count()

class APIRequestLogSerializer(serializers.ModelSerializer):
    """API request log serializer"""
    
    client_name = serializers.CharField(source='client.name', read_only=True)
    version_name = serializers.CharField(source='version.name', read_only=True)
    endpoint_path = serializers.CharField(source='endpoint.path', read_only=True)
    
    class Meta:
        model = APIRequestLog
        fields = [
            'id', 'client', 'client_name', 'version', 'version_name', 'endpoint',
            'endpoint_path', 'method', 'path', 'query_params', 'headers',
            'status_code', 'response_time', 'response_size', 'ip_address',
            'user_agent', 'error_message', 'error_type', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']

class APIDeprecationNoticeSerializer(serializers.ModelSerializer):
    """API deprecation notice serializer"""
    
    version_name = serializers.CharField(source='version.name', read_only=True)
    endpoint_path = serializers.CharField(source='endpoint.path', read_only=True)
    affected_clients_count = serializers.SerializerMethodField()
    acknowledged_count = serializers.SerializerMethodField()
    
    class Meta:
        model = APIDeprecationNotice
        fields = [
            'id', 'version', 'version_name', 'endpoint', 'endpoint_path', 'title',
            'description', 'notice_date', 'deprecation_date', 'retirement_date',
            'migration_guide', 'alternative_endpoints', 'affected_clients',
            'affected_clients_count', 'severity', 'is_active', 'acknowledged_by',
            'acknowledged_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_affected_clients_count(self, obj):
        """Get number of affected clients"""
        return obj.affected_clients.count()
    
    def get_acknowledged_count(self, obj):
        """Get number of users who acknowledged"""
        return obj.acknowledged_by.count()
