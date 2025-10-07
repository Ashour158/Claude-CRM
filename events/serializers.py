# events/serializers.py
# Event-Driven Architecture Serializers

from rest_framework import serializers
from .models import (
    EventType, Event, EventHandler, EventExecution,
    EventSubscription, EventStream
)

class EventTypeSerializer(serializers.ModelSerializer):
    """Event type serializer"""
    
    class Meta:
        model = EventType
        fields = [
            'id', 'name', 'description', 'category', 'schema',
            'is_active', 'is_public', 'total_events', 'last_triggered',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class EventSerializer(serializers.ModelSerializer):
    """Event serializer"""
    
    event_type_name = serializers.CharField(source='event_type.name', read_only=True)
    triggered_by_name = serializers.CharField(source='triggered_by.get_full_name', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'event_type', 'event_type_name', 'name', 'description',
            'data', 'metadata', 'content_type', 'object_id', 'status',
            'priority', 'triggered_by', 'triggered_by_name', 'processed_at',
            'processing_duration', 'error_message', 'retry_count',
            'max_retries', 'correlation_id', 'parent_event', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class EventHandlerSerializer(serializers.ModelSerializer):
    """Event handler serializer"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    success_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = EventHandler
        fields = [
            'id', 'name', 'description', 'handler_type', 'event_types',
            'conditions', 'endpoint_url', 'handler_function', 'configuration',
            'is_async', 'timeout_seconds', 'retry_on_failure', 'max_retries',
            'status', 'is_active', 'total_executions', 'successful_executions',
            'failed_executions', 'success_rate', 'last_executed', 'owner', 'owner_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class EventExecutionSerializer(serializers.ModelSerializer):
    """Event execution serializer"""
    
    event_name = serializers.CharField(source='event.name', read_only=True)
    handler_name = serializers.CharField(source='handler.name', read_only=True)
    
    class Meta:
        model = EventExecution
        fields = [
            'id', 'event', 'event_name', 'handler', 'handler_name',
            'status', 'started_at', 'completed_at', 'duration_ms',
            'result_data', 'error_message', 'error_traceback',
            'retry_count', 'is_retry', 'parent_execution', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class EventSubscriptionSerializer(serializers.ModelSerializer):
    """Event subscription serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = EventSubscription
        fields = [
            'id', 'name', 'description', 'subscription_type', 'event_types',
            'filters', 'endpoint_url', 'user', 'user_name', 'is_active',
            'last_activity', 'total_events', 'successful_deliveries',
            'failed_deliveries', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class EventStreamSerializer(serializers.ModelSerializer):
    """Event stream serializer"""
    
    class Meta:
        model = EventStream
        fields = [
            'id', 'name', 'description', 'stream_type', 'event_types',
            'filters', 'buffer_size', 'flush_interval', 'is_active',
            'is_processing', 'last_processed', 'total_events',
            'processed_events', 'failed_events', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
