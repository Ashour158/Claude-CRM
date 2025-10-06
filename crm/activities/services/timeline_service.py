# crm/activities/services/timeline_service.py
# Timeline service for recording events

from typing import Optional, Dict, Any
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from crm.activities.models import TimelineEvent
from crm.tenancy import get_current_org
from core.models import User


@transaction.atomic
def record_event(
    *,
    event_type: str,
    target: Any,
    actor: Optional[User] = None,
    data: Optional[Dict] = None,
    description: str = ''
) -> TimelineEvent:
    """
    Record a timeline event.
    
    Args:
        event_type: Type of event (from TimelineEvent.EVENT_TYPE_CHOICES)
        target: The object this event is about (Account, Contact, Lead, etc.)
        actor: User who performed the action (None for system events)
        data: Additional event data as dictionary
        description: Optional human-readable description
        
    Returns:
        Created TimelineEvent instance
    """
    # Get organization from context or target
    org = get_current_org()
    if not org and hasattr(target, 'organization'):
        org = target.organization
    
    if not org:
        raise ValueError("Cannot record event without organization context")
    
    # Get content type for target
    content_type = ContentType.objects.get_for_model(target)
    
    event = TimelineEvent.objects.create(
        organization=org,
        event_type=event_type,
        actor=actor,
        target_content_type=content_type,
        target_object_id=target.pk,
        data=data or {},
        description=description
    )
    
    return event


def record_status_change(
    *,
    target: Any,
    old_status: str,
    new_status: str,
    actor: Optional[User] = None
) -> TimelineEvent:
    """Record a status change event"""
    return record_event(
        event_type='status_change',
        target=target,
        actor=actor,
        data={
            'old_status': old_status,
            'new_status': new_status,
        },
        description=f"Status changed from {old_status} to {new_status}"
    )


def record_assignment_change(
    *,
    target: Any,
    old_owner: Optional[User],
    new_owner: Optional[User],
    actor: Optional[User] = None
) -> TimelineEvent:
    """Record an assignment change event"""
    old_name = old_owner.get_full_name() if old_owner else 'Unassigned'
    new_name = new_owner.get_full_name() if new_owner else 'Unassigned'
    
    return record_event(
        event_type='assignment_changed',
        target=target,
        actor=actor,
        data={
            'old_owner_id': old_owner.id if old_owner else None,
            'old_owner_name': old_name,
            'new_owner_id': new_owner.id if new_owner else None,
            'new_owner_name': new_name,
        },
        description=f"Assigned from {old_name} to {new_name}"
    )


def record_note(
    *,
    target: Any,
    note_text: str,
    actor: User
) -> TimelineEvent:
    """Record a note event"""
    return record_event(
        event_type='note',
        target=target,
        actor=actor,
        data={'note': note_text},
        description=note_text[:200]  # Truncate to 200 chars
    )
