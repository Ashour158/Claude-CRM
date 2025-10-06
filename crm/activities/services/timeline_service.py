# crm/activities/services/timeline_service.py
"""
Timeline service for recording and managing timeline events
"""
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from crm.activities.models import TimelineEvent


class TimelineService:
    """Service for timeline operations"""
    
    @staticmethod
    @transaction.atomic
    def record_event(organization, target, event_type, title, description='', actor=None, metadata=None):
        """
        Record a timeline event for any entity
        
        Args:
            organization: Company instance
            target: The object this event relates to (Account, Contact, Lead, etc.)
            event_type: Type of event
            title: Event title
            description: Event description
            actor: User who triggered the event
            metadata: Additional event data
            
        Returns:
            TimelineEvent instance
        """
        content_type = ContentType.objects.get_for_model(target)
        
        event = TimelineEvent(
            organization=organization,
            event_type=event_type,
            title=title,
            description=description,
            target_content_type=content_type,
            target_object_id=str(target.pk),
            actor=actor,
            metadata=metadata or {},
        )
        
        if actor:
            event.created_by = actor
            event.updated_by = actor
        
        event.save()
        return event
    
    @staticmethod
    def record_creation(organization, target, actor=None):
        """Record object creation event"""
        return TimelineService.record_event(
            organization=organization,
            target=target,
            event_type='creation',
            title=f"{target.__class__.__name__} created",
            description=f"{target.__class__.__name__} {target} was created",
            actor=actor
        )
    
    @staticmethod
    def record_update(organization, target, actor=None, changes=None):
        """Record object update event"""
        return TimelineService.record_event(
            organization=organization,
            target=target,
            event_type='update',
            title=f"{target.__class__.__name__} updated",
            description=f"{target.__class__.__name__} {target} was updated",
            actor=actor,
            metadata={'changes': changes} if changes else {}
        )
    
    @staticmethod
    def record_status_change(organization, target, old_status, new_status, actor=None):
        """Record status change event"""
        return TimelineService.record_event(
            organization=organization,
            target=target,
            event_type='status_change',
            title=f"Status changed: {old_status} → {new_status}",
            description=f"Status changed from {old_status} to {new_status}",
            actor=actor,
            metadata={'old_status': old_status, 'new_status': new_status}
        )
