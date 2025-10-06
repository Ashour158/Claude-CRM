# crm/activities/serializers.py
# Serializers for timeline events

from rest_framework import serializers
from crm.activities.models import TimelineEvent
from core.models import User


class ActorSerializer(serializers.ModelSerializer):
    """Serializer for event actor (user)"""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']


class TimelineEventSerializer(serializers.ModelSerializer):
    """Serializer for timeline events"""
    
    actor = ActorSerializer(read_only=True)
    object_type = serializers.SerializerMethodField()
    object_id = serializers.SerializerMethodField()
    
    class Meta:
        model = TimelineEvent
        fields = [
            'id',
            'event_type',
            'actor',
            'object_type',
            'object_id',
            'data',
            'summary',
            'is_system_generated',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields
    
    def get_object_type(self, obj):
        """Get the type of the target object"""
        if obj.target_content_type:
            return obj.target_content_type.model
        return None
    
    def get_object_id(self, obj):
        """Get the ID of the target object"""
        return str(obj.target_object_id) if obj.target_object_id else None


class TimelineResponseSerializer(serializers.Serializer):
    """Response serializer for timeline endpoint"""
    
    object = serializers.DictField()
    events = TimelineEventSerializer(many=True)
    pagination = serializers.DictField(required=False)
