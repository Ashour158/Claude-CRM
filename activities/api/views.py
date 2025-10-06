# activities/api/views.py
"""DRF views for activity-related endpoints."""

from rest_framework import viewsets, permissions
from activities.models import TimelineEvent
from activities.api.serializers import TimelineEventSerializer
from activities.api.pagination import TimelinePagination


class TimelineEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for timeline events.
    
    Provides list and retrieve operations with pagination.
    GET /api/activities/timeline/ - List timeline events with pagination
    GET /api/activities/timeline/{id}/ - Retrieve a specific timeline event
    """
    queryset = TimelineEvent.objects.all()
    serializer_class = TimelineEventSerializer
    pagination_class = TimelinePagination
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter timeline events by company from request context."""
        queryset = super().get_queryset()
        # Multi-tenant filtering would go here if middleware sets company context
        # For now, return all events
        return queryset.order_by('-created_at')
