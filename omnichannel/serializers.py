# omnichannel/serializers.py
# Omnichannel Communication Serializers

from rest_framework import serializers
from .models import (
    CommunicationChannel, Conversation, Message, ConversationTemplate,
    ConversationRule, ConversationMetric, ConversationAnalytics
)

class CommunicationChannelSerializer(serializers.ModelSerializer):
    """Communication channel serializer"""
    
    class Meta:
        model = CommunicationChannel
        fields = [
            'id', 'name', 'channel_type', 'description', 'configuration',
            'credentials', 'status', 'is_active', 'response_time_sla',
            'resolution_time_sla', 'total_conversations', 'active_conversations',
            'average_response_time', 'customer_satisfaction', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ConversationSerializer(serializers.ModelSerializer):
    """Conversation serializer"""
    
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    assigned_agent_name = serializers.CharField(source='assigned_agent.get_full_name', read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'conversation_id', 'subject', 'description', 'channel',
            'channel_name', 'external_id', 'customer', 'customer_name',
            'assigned_agent', 'assigned_agent_name', 'status', 'priority',
            'sla_deadline', 'first_response_time', 'resolution_time',
            'tags', 'metadata', 'last_activity', 'resolved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'conversation_id', 'created_at', 'updated_at']

class ConversationCreateSerializer(serializers.ModelSerializer):
    """Conversation creation serializer"""
    
    class Meta:
        model = Conversation
        fields = [
            'subject', 'description', 'channel', 'customer', 'priority',
            'tags', 'metadata'
        ]

class MessageSerializer(serializers.ModelSerializer):
    """Message serializer"""
    
    conversation_subject = serializers.CharField(source='conversation.subject', read_only=True)
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'conversation_subject', 'message_type',
            'direction', 'content', 'content_type', 'sender', 'sender_name',
            'recipient', 'recipient_name', 'external_id', 'thread_id',
            'is_read', 'is_delivered', 'is_sent', 'attachments', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class MessageCreateSerializer(serializers.ModelSerializer):
    """Message creation serializer"""
    
    class Meta:
        model = Message
        fields = [
            'conversation', 'content', 'content_type', 'attachments', 'metadata'
        ]

class ConversationTemplateSerializer(serializers.ModelSerializer):
    """Conversation template serializer"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = ConversationTemplate
        fields = [
            'id', 'name', 'description', 'template_type', 'subject_template',
            'content_template', 'variables', 'channels', 'usage_count',
            'last_used', 'is_active', 'is_public', 'owner', 'owner_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ConversationRuleSerializer(serializers.ModelSerializer):
    """Conversation rule serializer"""
    
    class Meta:
        model = ConversationRule
        fields = [
            'id', 'name', 'description', 'rule_type', 'trigger_condition',
            'conditions', 'actions', 'channels', 'is_active', 'priority',
            'execution_count', 'success_count', 'last_executed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ConversationMetricSerializer(serializers.ModelSerializer):
    """Conversation metric serializer"""
    
    class Meta:
        model = ConversationMetric
        fields = [
            'id', 'metric_type', 'name', 'description', 'calculation_method',
            'aggregation_period', 'filters', 'target_value', 'warning_threshold',
            'critical_threshold', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ConversationAnalyticsSerializer(serializers.ModelSerializer):
    """Conversation analytics serializer"""
    
    metric_name = serializers.CharField(source='metric.name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    
    class Meta:
        model = ConversationAnalytics
        fields = [
            'id', 'metric', 'metric_name', 'period_start', 'period_end',
            'current_value', 'previous_value', 'target_value', 'trend_direction',
            'trend_percentage', 'status', 'insights', 'recommendations',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
