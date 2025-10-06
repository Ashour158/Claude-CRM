# crm/activities/selectors/timeline_selector.py
# Timeline selector for retrieving events

from typing import Optional, List, Tuple
from django.contrib.contenttypes.models import ContentType
from crm.activities.models import TimelineEvent


def fetch_timeline(
    *,
    object_type: str,
    object_id: int,
    limit: int = 50,
    cursor: Optional[int] = None,
    event_type: Optional[str] = None
) -> Tuple[List[TimelineEvent], Optional[int]]:
    """
    Fetch timeline events for an object with cursor-based pagination.
    
    Args:
        object_type: Type of object (e.g., 'account', 'contact', 'lead')
        object_id: ID of the object
        limit: Maximum number of events to return
        cursor: Pagination cursor (last event ID from previous page)
        event_type: Optional filter by event type
        
    Returns:
        Tuple of (list of TimelineEvent instances, next cursor)
    """
    # Map object type string to model class
    from django.apps import apps
    
    model_mapping = {
        'account': 'accounts.Account',
        'contact': 'contacts.Contact',
        'lead': 'leads.Lead',
        'deal': 'deals.Deal',
    }
    
    if object_type not in model_mapping:
        raise ValueError(f"Invalid object_type: {object_type}")
    
    try:
        model_class = apps.get_model(model_mapping[object_type])
        content_type = ContentType.objects.get_for_model(model_class)
    except Exception as e:
        raise ValueError(f"Could not get content type for {object_type}: {e}")
    
    # Build query
    qs = TimelineEvent.objects.filter(
        target_content_type=content_type,
        target_object_id=object_id
    )
    
    if event_type:
        qs = qs.filter(event_type=event_type)
    
    if cursor:
        # Cursor is the ID of the last event from previous page
        qs = qs.filter(id__lt=cursor)
    
    # Order by created_at desc, then by ID desc for stable ordering
    qs = qs.order_by('-created_at', '-id')
    
    # Fetch limit + 1 to check if there are more results
    events = list(qs[:limit + 1])
    
    # Determine next cursor
    has_more = len(events) > limit
    if has_more:
        events = events[:limit]
        next_cursor = events[-1].id if events else None
    else:
        next_cursor = None
    
    return events, next_cursor


def get_recent_timeline(
    *,
    organization_id: int,
    limit: int = 20,
    event_type: Optional[str] = None
) -> List[TimelineEvent]:
    """
    Get recent timeline events across all objects for an organization.
    
    Args:
        organization_id: The organization ID
        limit: Maximum number of events to return
        event_type: Optional filter by event type
        
    Returns:
        List of recent TimelineEvent instances
    """
    qs = TimelineEvent.objects.filter(organization_id=organization_id)
    
    if event_type:
        qs = qs.filter(event_type=event_type)
    
    return list(qs.order_by('-created_at')[:limit])
