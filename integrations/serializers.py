# integrations/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Integration, EmailIntegration, CalendarIntegration, Webhook, WebhookLog,
    APICredential, DataSync
)

User = get_user_model()

class IntegrationSerializer(serializers.ModelSerializer):
    """Serializer for Integration model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = Integration
        fields = [
            'id', 'name', 'integration_type', 'provider', 'description',
            'api_endpoint', 'api_key', 'api_secret', 'webhook_url',
            'settings', 'credentials', 'status', 'is_active', 'owner',
            'owner_name', 'last_sync', 'sync_frequency', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True},
            'credentials': {'write_only': True}
        }

class EmailIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for EmailIntegration model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = EmailIntegration
        fields = [
            'id', 'name', 'provider', 'smtp_host', 'smtp_port',
            'smtp_username', 'smtp_password', 'smtp_use_tls', 'smtp_use_ssl',
            'api_key', 'api_secret', 'api_url', 'from_email', 'from_name',
            'reply_to_email', 'rate_limit_per_hour', 'rate_limit_per_day',
            'is_active', 'is_verified', 'owner', 'owner_name',
            'emails_sent', 'emails_delivered', 'emails_bounced',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'emails_sent', 'emails_delivered', 'emails_bounced', 'created_at', 'updated_at']
        extra_kwargs = {
            'smtp_password': {'write_only': True},
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True}
        }

class CalendarIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for CalendarIntegration model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = CalendarIntegration
        fields = [
            'id', 'name', 'provider', 'client_id', 'client_secret',
            'redirect_uri', 'access_token', 'refresh_token', 'token_expires_at',
            'calendar_id', 'calendar_name', 'timezone', 'sync_events',
            'sync_tasks', 'sync_contacts', 'is_active', 'is_connected',
            'owner', 'owner_name', 'events_synced', 'last_sync',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'events_synced', 'last_sync', 'created_at', 'updated_at']
        extra_kwargs = {
            'client_secret': {'write_only': True},
            'access_token': {'write_only': True},
            'refresh_token': {'write_only': True}
        }

class WebhookSerializer(serializers.ModelSerializer):
    """Serializer for Webhook model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = Webhook
        fields = [
            'id', 'name', 'webhook_type', 'url', 'http_method',
            'auth_type', 'auth_username', 'auth_password', 'auth_token',
            'auth_header', 'headers', 'payload_template', 'trigger_events',
            'trigger_conditions', 'is_active', 'owner', 'owner_name',
            'total_calls', 'successful_calls', 'failed_calls', 'last_called',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_calls', 'successful_calls', 'failed_calls', 'last_called', 'created_at', 'updated_at']
        extra_kwargs = {
            'auth_password': {'write_only': True},
            'auth_token': {'write_only': True}
        }

class WebhookLogSerializer(serializers.ModelSerializer):
    """Serializer for WebhookLog model"""
    webhook_name = serializers.CharField(source='webhook.name', read_only=True)
    triggered_by_name = serializers.CharField(source='triggered_by.get_full_name', read_only=True)
    
    class Meta:
        model = WebhookLog
        fields = [
            'id', 'webhook', 'webhook_name', 'status', 'request_url',
            'request_method', 'request_headers', 'request_payload',
            'response_status_code', 'response_headers', 'response_body',
            'execution_time', 'error_message', 'retry_count', 'triggered_by',
            'triggered_by_name', 'object_type', 'object_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class APICredentialSerializer(serializers.ModelSerializer):
    """Serializer for APICredential model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = APICredential
        fields = [
            'id', 'name', 'service', 'credential_type', 'api_key', 'api_secret',
            'access_token', 'refresh_token', 'username', 'password',
            'client_id', 'client_secret', 'redirect_uri', 'scope',
            'base_url', 'headers', 'is_active', 'is_verified', 'owner',
            'owner_name', 'expires_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True},
            'access_token': {'write_only': True},
            'refresh_token': {'write_only': True},
            'password': {'write_only': True},
            'client_secret': {'write_only': True}
        }

class DataSyncSerializer(serializers.ModelSerializer):
    """Serializer for DataSync model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = DataSync
        fields = [
            'id', 'name', 'description', 'sync_type', 'source_system',
            'target_system', 'source_endpoint', 'target_endpoint',
            'sync_frequency', 'batch_size', 'sync_conditions', 'status',
            'is_active', 'owner', 'owner_name', 'total_records_synced',
            'last_sync', 'next_sync', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_records_synced', 'last_sync', 'next_sync', 'created_at', 'updated_at']

# Bulk operation serializers
class BulkIntegrationSerializer(serializers.Serializer):
    """Serializer for bulk integration operations"""
    integration_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of integration IDs"
    )
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'test', 'delete'],
        help_text="Action to perform"
    )

class BulkWebhookSerializer(serializers.Serializer):
    """Serializer for bulk webhook operations"""
    webhook_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of webhook IDs"
    )
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'test', 'delete'],
        help_text="Action to perform"
    )

# Integration specific serializers
class EmailServiceSerializer(serializers.Serializer):
    """Serializer for email service configuration"""
    provider = serializers.ChoiceField(choices=[
        ('smtp', 'SMTP'),
        ('sendgrid', 'SendGrid'),
        ('mailgun', 'Mailgun'),
        ('ses', 'Amazon SES'),
        ('mandrill', 'Mandrill'),
        ('postmark', 'Postmark'),
    ])
    smtp_host = serializers.CharField(required=False)
    smtp_port = serializers.IntegerField(required=False)
    smtp_username = serializers.CharField(required=False)
    smtp_password = serializers.CharField(required=False)
    api_key = serializers.CharField(required=False)
    api_secret = serializers.CharField(required=False)
    from_email = serializers.EmailField()
    from_name = serializers.CharField()

class CalendarServiceSerializer(serializers.Serializer):
    """Serializer for calendar service configuration"""
    provider = serializers.ChoiceField(choices=[
        ('google', 'Google Calendar'),
        ('outlook', 'Microsoft Outlook'),
        ('apple', 'Apple Calendar'),
        ('caldav', 'CalDAV'),
    ])
    client_id = serializers.CharField(required=False)
    client_secret = serializers.CharField(required=False)
    redirect_uri = serializers.URLField(required=False)
    calendar_id = serializers.CharField(required=False)
    timezone = serializers.CharField(default='UTC')

class WebhookTestSerializer(serializers.Serializer):
    """Serializer for webhook testing"""
    webhook_id = serializers.UUIDField()
    test_payload = serializers.JSONField(default=dict)
    test_headers = serializers.JSONField(default=dict)

class IntegrationTestSerializer(serializers.Serializer):
    """Serializer for integration testing"""
    integration_id = serializers.UUIDField()
    test_type = serializers.ChoiceField(choices=[
        ('connection', 'Connection Test'),
        ('authentication', 'Authentication Test'),
        ('permissions', 'Permissions Test'),
        ('data_sync', 'Data Sync Test'),
    ])

class DataSyncStatusSerializer(serializers.Serializer):
    """Serializer for data sync status"""
    sync_id = serializers.UUIDField()
    status = serializers.CharField()
    progress = serializers.DecimalField(max_digits=5, decimal_places=2)
    records_processed = serializers.IntegerField()
    records_total = serializers.IntegerField()
    last_sync_time = serializers.DateTimeField()
    next_sync_time = serializers.DateTimeField()
    error_message = serializers.CharField(required=False)

class IntegrationMetricsSerializer(serializers.Serializer):
    """Serializer for integration metrics"""
    total_integrations = serializers.IntegerField()
    active_integrations = serializers.IntegerField()
    total_webhooks = serializers.IntegerField()
    active_webhooks = serializers.IntegerField()
    total_api_calls = serializers.IntegerField()
    successful_api_calls = serializers.IntegerField()
    failed_api_calls = serializers.IntegerField()
    total_emails_sent = serializers.IntegerField()
    total_events_synced = serializers.IntegerField()
    average_response_time = serializers.DecimalField(max_digits=8, decimal_places=2)

class WebhookDeliverySerializer(serializers.Serializer):
    """Serializer for webhook delivery status"""
    webhook_id = serializers.UUIDField()
    delivery_id = serializers.UUIDField()
    status = serializers.CharField()
    attempts = serializers.IntegerField()
    last_attempt = serializers.DateTimeField()
    next_retry = serializers.DateTimeField(required=False)
    error_message = serializers.CharField(required=False)
