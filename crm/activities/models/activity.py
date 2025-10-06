# crm/activities/models/activity.py
# Timeline event model for activity tracking

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from crm.tenancy import TenantOwnedModel
from core.models import User


class TimelineEvent(TenantOwnedModel):
    """
    Timeline event model for tracking all activities and system events.
    Uses Generic Foreign Key to link to any model instance.
    """
    
    EVENT_TYPE_CHOICES = [
        # User actions
        ('note', 'Note'),
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('task_completed', 'Task Completed'),
        
        # System events
        ('lead_converted', 'Lead Converted'),
        ('status_change', 'Status Changed'),
        ('field_updated', 'Field Updated'),
        ('record_created', 'Record Created'),
        ('record_deleted', 'Record Deleted'),
        ('assignment_changed', 'Assignment Changed'),
        
        # Custom events
        ('custom', 'Custom Event'),
    ]
    
    # Event metadata
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of timeline event"
    )
    
    # Actor (user who performed the action)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timeline_events_v2',
        help_text="User who triggered this event"
    )
    
    # Target object (what the event is about)
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='timeline_events_v2'
    )
    target_object_id = models.IntegerField()
    target = GenericForeignKey('target_content_type', 'target_object_id')
    
    # Event data (stored as JSON for flexibility)
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional event data as JSON"
    )
    
    # Optional text description
    description = models.TextField(
        blank=True,
        help_text="Human-readable event description"
    )
    
    class Meta:
        db_table = 'crm_timeline_events'
        verbose_name = 'Timeline Event'
        verbose_name_plural = 'Timeline Events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'event_type', '-created_at']),
            models.Index(fields=['organization', 'target_content_type', 'target_object_id', '-created_at']),
            models.Index(fields=['organization', 'actor', '-created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        actor_str = self.actor.get_full_name() if self.actor else 'System'
        return f"{self.get_event_type_display()} by {actor_str} at {self.created_at}"
    
    def get_event_summary(self) -> str:
        """Generate a human-readable summary of the event"""
        actor_name = self.actor.get_full_name() if self.actor else 'System'
        
        if self.event_type == 'lead_converted':
            contact_name = self.data.get('contact_name', 'Unknown')
            return f"{actor_name} converted lead to {contact_name}"
        
        elif self.event_type == 'status_change':
            old_status = self.data.get('old_status', 'Unknown')
            new_status = self.data.get('new_status', 'Unknown')
            return f"{actor_name} changed status from {old_status} to {new_status}"
        
        elif self.event_type == 'note':
            return f"{actor_name} added a note"
        
        elif self.description:
            return self.description
        
        return f"{actor_name} {self.get_event_type_display().lower()}"
