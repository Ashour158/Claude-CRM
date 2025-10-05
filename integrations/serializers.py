# integrations/serializers.py
# Integrations serializers

from rest_framework import serializers
from .models import (
    APICredential, Webhook, WebhookLog, DataSync, DataSyncLog,
    EmailIntegration, CalendarIntegration
)
from core.serializers import UserSerializer

class APICredentialSerializer(serializers.ModelSerializer):
    """API credential serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = APICredential
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class WebhookSerializer(serializers.ModelSerializer):
    """Webhook serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Webhook
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class WebhookLogSerializer(serializers.ModelSerializer):
    """Webhook log serializer"""
    
    class Meta:
        model = WebhookLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class DataSyncSerializer(serializers.ModelSerializer):
    """Data sync serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = DataSync
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class DataSyncLogSerializer(serializers.ModelSerializer):
    """Data sync log serializer"""
    
    class Meta:
        model = DataSyncLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class EmailIntegrationSerializer(serializers.ModelSerializer):
    """Email integration serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = EmailIntegration
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class CalendarIntegrationSerializer(serializers.ModelSerializer):
    """Calendar integration serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = CalendarIntegration
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']