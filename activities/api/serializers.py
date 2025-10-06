# activities/api/serializers.py
"""DRF serializers for activity-related models."""

from rest_framework import serializers
from activities.models import TimelineEvent


class TimelineEventSerializer(serializers.ModelSerializer):
    """Serializer for TimelineEvent model (list/read operations)."""
    
    class Meta:
        model = TimelineEvent
        fields = ['id', 'event_type', 'created_at', 'data', 'title', 'description', 'user', 'is_system_event']
        read_only_fields = ['id', 'created_at']
