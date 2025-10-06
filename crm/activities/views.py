# crm/activities/views.py
# Views for timeline events

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from crm.activities.models import TimelineEvent
from crm.activities.serializers import TimelineEventSerializer, TimelineResponseSerializer


class TimelineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for timeline events.
    
    Provides:
    - GET /api/v1/activities/timeline/?object_type=lead&object_id=123
    """
    
    serializer_class = TimelineEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter timeline events by object type and ID if provided"""
        queryset = TimelineEvent.objects.all()
        
        # Filter by object type and ID if provided
        object_type = self.request.query_params.get('object_type')
        object_id = self.request.query_params.get('object_id')
        
        if object_type and object_id:
            try:
                # Get content type for the model
                content_type = ContentType.objects.get(model=object_type.lower())
                queryset = queryset.filter(
                    target_content_type=content_type,
                    target_object_id=object_id
                )
            except ContentType.DoesNotExist:
                return TimelineEvent.objects.none()
        
        # Filter by event type if provided
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Order by created_at descending (most recent first)
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'], url_path='timeline')
    def timeline(self, request):
        """
        Get timeline events for a specific object.
        
        Query params:
        - object_type: Type of object (e.g., 'lead', 'account', 'contact')
        - object_id: ID of the object
        - event_type: Optional filter by event type
        - page: Page number (default: 1)
        - page_size: Results per page (default: 50)
        
        Response format:
        {
            "object": {"type": "lead", "id": "123"},
            "events": [
                {
                    "id": 55,
                    "event_type": "note",
                    "actor": {...},
                    "created_at": "...",
                    "data": {...}
                },
                ...
            ],
            "pagination": {
                "page": 1,
                "page_size": 50,
                "total": 100,
                "pages": 2
            }
        }
        """
        object_type = request.query_params.get('object_type')
        object_id = request.query_params.get('object_id')
        
        if not object_type or not object_id:
            return Response(
                {'error': 'object_type and object_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get events
        queryset = self.filter_queryset(self.get_queryset())
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 50))
        page_size = min(page_size, 100)  # Max 100 per page
        
        # Use DRF pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            
            # Build response
            response_data = {
                'object': {
                    'type': object_type,
                    'id': object_id
                },
                'events': serializer.data,
                'pagination': {
                    'page': self.paginator.page.number if hasattr(self.paginator, 'page') else 1,
                    'page_size': page_size,
                    'total': self.paginator.page.paginator.count if hasattr(self.paginator, 'page') else len(serializer.data),
                }
            }
            
            return Response(response_data)
        
        # No pagination
        serializer = self.get_serializer(queryset, many=True)
        response_data = {
            'object': {
                'type': object_type,
                'id': object_id
            },
            'events': serializer.data
        }
        
        return Response(response_data)
