# crm/activities/models/activity.py
"""
Activity/Timeline model for tracking events
"""
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from crm.core.tenancy.mixins import TenantOwnedModel
from crm.core.tenancy.managers import TenantManager


class TimelineEvent(TenantOwnedModel):
    """
    TimelineEvent represents an activity or event in the system.
    Uses generic foreign key to link to any entity (Account, Contact, Lead, Deal, etc.)
    """
    
    EVENT_TYPE_CHOICES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('note', 'Note'),
        ('task', 'Task'),
        ('status_change', 'Status Change'),
        ('creation', 'Record Created'),
        ('update', 'Record Updated'),
        ('conversion', 'Lead Converted'),
        ('other', 'Other'),
    ]
    
    # Event details
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of event"
    )
    title = models.CharField(max_length=255, help_text="Event title/subject")
    description = models.TextField(blank=True, help_text="Event description")
    
    # Generic foreign key to any model
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="Content type of the related object"
    )
    target_object_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="ID of the related object"
    )
    target = GenericForeignKey('target_content_type', 'target_object_id')
    
    # Event metadata
    event_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the event occurred"
    )
    actor = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timeline_events',
        help_text="User who triggered the event"
    )
    
    # Additional data (flexible JSON storage)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional event metadata"
    )
    
    # Manager
    objects = TenantManager()
    
    class Meta:
        db_table = 'crm_timeline_event'
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['organization', '-event_date']),
            models.Index(fields=['target_content_type', 'target_object_id', '-event_date']),
            models.Index(fields=['event_type', '-event_date']),
        ]
        verbose_name = 'Timeline Event'
        verbose_name_plural = 'Timeline Events'
    
    def __str__(self):
        return f"{self.event_type}: {self.title}"
