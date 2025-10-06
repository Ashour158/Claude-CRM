# crm/activities/api/views.py
# API views for activities and timeline

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from crm.activities.selectors.timeline_selector import fetch_timeline, get_recent_timeline
from crm.tenancy import get_current_org


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def timeline_list(request):
    """
    Get timeline events for an object or organization.
    
    Query parameters:
    - object_type: Type of object ('account', 'contact', 'lead', 'deal')
    - object_id: ID of the object
    - limit: Number of events to return (default: 50, max: 100)
    - cursor: Pagination cursor
    - event_type: Filter by event type (optional)
    
    If object_type and object_id are provided, returns timeline for that object.
    Otherwise, returns recent timeline for the organization.
    """
    object_type = request.query_params.get('object_type')
    object_id = request.query_params.get('object_id')
    limit = min(int(request.query_params.get('limit', 50)), 100)
    cursor = request.query_params.get('cursor')
    event_type = request.query_params.get('event_type')
    
    org = get_current_org()
    if not org:
        return Response(
            {'error': 'Organization context not set'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        if object_type and object_id:
            # Get timeline for specific object
            cursor_id = int(cursor) if cursor else None
            events, next_cursor = fetch_timeline(
                object_type=object_type,
                object_id=int(object_id),
                limit=limit,
                cursor=cursor_id,
                event_type=event_type
            )
            
            return Response({
                'object_type': object_type,
                'object_id': int(object_id),
                'events': [serialize_event(e) for e in events],
                'next_cursor': next_cursor,
                'has_more': next_cursor is not None
            })
        else:
            # Get recent timeline for organization
            events = get_recent_timeline(
                organization_id=org.id,
                limit=limit,
                event_type=event_type
            )
            
            return Response({
                'events': [serialize_event(e) for e in events],
                'count': len(events)
            })
    
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch timeline: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def serialize_event(event):
    """Serialize a timeline event for API response"""
    return {
        'id': event.id,
        'event_type': event.event_type,
        'event_type_display': event.get_event_type_display(),
        'actor': {
            'id': event.actor.id,
            'name': event.actor.get_full_name(),
            'email': event.actor.email
        } if event.actor else None,
        'target_type': event.target_content_type.model,
        'target_id': event.target_object_id,
        'data': event.data,
        'description': event.description,
        'summary': event.get_event_summary(),
        'created_at': event.created_at.isoformat(),
    }
