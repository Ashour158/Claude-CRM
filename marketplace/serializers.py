# marketplace/serializers.py
# Marketplace and Extensibility Serializers

from rest_framework import serializers
from .models import (
    MarketplaceApp, AppInstallation, AppReview, AppPermission,
    AppWebhook, AppExecution, AppAnalytics, AppSubscription
)

class MarketplaceAppSerializer(serializers.ModelSerializer):
    """Marketplace app serializer"""
    
    developer_name = serializers.CharField(source='developer.get_full_name', read_only=True)
    
    class Meta:
        model = MarketplaceApp
        fields = [
            'id', 'app_id', 'name', 'description', 'short_description',
            'app_type', 'version', 'latest_version', 'is_latest', 'developer',
            'developer_name', 'developer_email', 'developer_website',
            'manifest', 'permissions', 'dependencies', 'status', 'is_public',
            'is_featured', 'is_free', 'price', 'currency', 'download_count',
            'rating', 'review_count', 'install_count', 'is_verified',
            'security_scan_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'app_id', 'created_at', 'updated_at']

class AppInstallationSerializer(serializers.ModelSerializer):
    """App installation serializer"""
    
    app_name = serializers.CharField(source='app.name', read_only=True)
    installed_by_name = serializers.CharField(source='installed_by.get_full_name', read_only=True)
    
    class Meta:
        model = AppInstallation
        fields = [
            'id', 'app', 'app_name', 'installed_by', 'installed_by_name',
            'version', 'installation_config', 'status', 'is_active',
            'installed_at', 'last_updated', 'uninstalled_at', 'usage_count',
            'last_used', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AppReviewSerializer(serializers.ModelSerializer):
    """App review serializer"""
    
    app_name = serializers.CharField(source='app.name', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    
    class Meta:
        model = AppReview
        fields = [
            'id', 'app', 'app_name', 'reviewer', 'reviewer_name', 'rating',
            'title', 'content', 'is_verified', 'is_public', 'helpful_count',
            'not_helpful_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AppPermissionSerializer(serializers.ModelSerializer):
    """App permission serializer"""
    
    app_name = serializers.CharField(source='app.name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = AppPermission
        fields = [
            'id', 'app', 'app_name', 'requested_by', 'requested_by_name',
            'permission_type', 'resource', 'scope', 'status', 'approved_by',
            'approved_by_name', 'requested_at', 'approved_at', 'expires_at',
            'usage_count', 'last_used', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AppWebhookSerializer(serializers.ModelSerializer):
    """App webhook serializer"""
    
    app_name = serializers.CharField(source='app.name', read_only=True)
    
    class Meta:
        model = AppWebhook
        fields = [
            'id', 'app', 'app_name', 'name', 'description', 'webhook_type',
            'endpoint_url', 'events', 'headers', 'secret', 'status',
            'is_active', 'total_calls', 'successful_calls', 'failed_calls',
            'last_called', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AppExecutionSerializer(serializers.ModelSerializer):
    """App execution serializer"""
    
    app_name = serializers.CharField(source='app.name', read_only=True)
    installation_version = serializers.CharField(source='installation.version', read_only=True)
    
    class Meta:
        model = AppExecution
        fields = [
            'id', 'app', 'app_name', 'installation', 'installation_version',
            'execution_type', 'function_name', 'parameters', 'status',
            'started_at', 'completed_at', 'duration_ms', 'result_data',
            'error_message', 'error_traceback', 'memory_usage', 'cpu_usage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AppAnalyticsSerializer(serializers.ModelSerializer):
    """App analytics serializer"""
    
    app_name = serializers.CharField(source='app.name', read_only=True)
    
    class Meta:
        model = AppAnalytics
        fields = [
            'id', 'app', 'app_name', 'metric_type', 'metric_name', 'value',
            'unit', 'dimensions', 'period_start', 'period_end', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AppSubscriptionSerializer(serializers.ModelSerializer):
    """App subscription serializer"""
    
    app_name = serializers.CharField(source='app.name', read_only=True)
    subscriber_name = serializers.CharField(source='subscriber.get_full_name', read_only=True)
    
    class Meta:
        model = AppSubscription
        fields = [
            'id', 'app', 'app_name', 'subscriber', 'subscriber_name',
            'subscription_type', 'status', 'price', 'currency', 'billing_cycle',
            'started_at', 'expires_at', 'cancelled_at', 'usage_limits',
            'current_usage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
