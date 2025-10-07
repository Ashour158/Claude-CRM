# api_versioning/serializers.py
# Serializers for API versioning module

from rest_framework import serializers
from .models import APIVersion, APIEndpoint, APIClient, APIRequestLog

class APIVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIVersion
        fields = '__all__'
        read_only_fields = ['request_count', 'active_clients', 'created_at', 'updated_at']

class APIEndpointSerializer(serializers.ModelSerializer):
    version_number = serializers.CharField(source='api_version.version_number', read_only=True)
    
    class Meta:
        model = APIEndpoint
        fields = '__all__'

class APIClientSerializer(serializers.ModelSerializer):
    preferred_version_number = serializers.CharField(source='preferred_version.version_number', read_only=True)
    
    class Meta:
        model = APIClient
        fields = '__all__'
        read_only_fields = ['total_requests', 'last_request', 'created_at', 'updated_at']

class APIRequestLogSerializer(serializers.ModelSerializer):
    version_number = serializers.CharField(source='api_version.version_number', read_only=True)
    client_name = serializers.CharField(source='api_client.name', read_only=True)
    
    class Meta:
        model = APIRequestLog
        fields = '__all__'
        read_only_fields = ['timestamp']
