# crm/activities/models/activity.py
# Unified Activity and TimelineEvent models for tracking all interactions

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.tenant_models import TenantOwnedModel
from core.models import User


class TimelineEvent(TenantOwnedModel):
    """
    Unified timeline event model for tracking all types of activities and events.
    Uses GenericForeignKey to relate to any model (Lead, Contact, Account, Deal, etc.)
    
    Event types:
    - note: General note/comment
    - email: Email sent/received
    - call: Phone call
    - meeting: Meeting held
    - task_completed: Task was completed
    - status_change: Status changed
    - lead_converted: Lead was converted
    - deal_won: Deal was won
    - deal_lost: Deal was lost
    - field_updated: Field value changed
    - file_attached: File was attached
    - custom: Custom event type
    """
    
    EVENT_TYPE_CHOICES = [
        ('note', 'Note'),
        ('email', 'Email'),
        ('call', 'Call'),
        ('meeting', 'Meeting'),
        ('task_completed', 'Task Completed'),
        ('status_change', 'Status Change'),
        ('lead_converted', 'Lead Converted'),
        ('deal_won', 'Deal Won'),
        ('deal_lost', 'Deal Lost'),
        ('field_updated', 'Field Updated'),
        ('file_attached', 'File Attached'),
        ('custom', 'Custom Event'),
    ]
    
    # Event metadata
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of event"
    )
    
    # Actor (who performed the action)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='timeline_events',
        help_text="User who triggered this event"
    )
    
    # Target object (what the event is about) - using GenericForeignKey
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='timeline_events',
        help_text="Type of object this event relates to"
    )
    target_object_id = models.UUIDField(
        db_index=True,
        help_text="ID of the object this event relates to"
    )
    target_object = GenericForeignKey('target_content_type', 'target_object_id')
    
    # Event data (flexible JSON storage)
    data = models.JSONField(
        default=dict,
        help_text="Event-specific data in JSON format"
    )
    
    # Optional text summary
    summary = models.TextField(
        blank=True,
        help_text="Human-readable summary of the event"
    )
    
    # Metadata
    is_system_generated = models.BooleanField(
        default=False,
        help_text="True if this event was automatically generated"
    )
    
    class Meta:
        db_table = 'crm_timeline_event'
        verbose_name = 'Timeline Event'
        verbose_name_plural = 'Timeline Events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['organization', 'event_type', '-created_at']),
            models.Index(fields=['organization', 'target_content_type', 'target_object_id', '-created_at']),
            models.Index(fields=['organization', 'actor', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def record(cls, event_type, target_object, actor=None, data=None, summary='', organization=None):
        """
        Convenience method to record a timeline event.
        
        Args:
            event_type: Type of event (from EVENT_TYPE_CHOICES)
            target_object: The object this event relates to
            actor: User who triggered the event (optional)
            data: Additional data dict (optional)
            summary: Human-readable summary (optional)
            organization: Organization context (optional, uses current if not provided)
        
        Returns:
            TimelineEvent instance
        """
        content_type = ContentType.objects.get_for_model(target_object)
        
        event = cls(
            event_type=event_type,
            actor=actor,
            target_content_type=content_type,
            target_object_id=target_object.id,
            data=data or {},
            summary=summary,
            is_system_generated=(actor is None)
        )
        
        if organization:
            event.organization = organization
        
        event.save()
        return event


# For backwards compatibility, create an Activity alias
Activity = TimelineEvent
