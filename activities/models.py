# activities/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class TimelineEvent(CompanyIsolatedModel):
    """
    Timeline events for tracking history across all entities
    """
    EVENT_TYPES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('status_changed', 'Status Changed'),
        ('assigned', 'Assigned'),
        ('comment_added', 'Comment Added'),
        ('email_sent', 'Email Sent'),
        ('call_logged', 'Call Logged'),
        ('meeting_scheduled', 'Meeting Scheduled'),
        ('note_added', 'Note Added'),
        ('file_attached', 'File Attached'),
        ('converted', 'Converted'),
        ('other', 'Other'),
    ]
    
    # Event Information
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        help_text="Type of timeline event"
    )
    title = models.CharField(max_length=255, help_text="Event title")
    description = models.TextField(blank=True, help_text="Event description")
    
    # Event Data (JSON for flexibility)
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional event data"
    )
    
    # Related Entity (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Type of related entity"
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the related entity"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # User who triggered the event
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timeline_events',
        help_text="User who triggered this event"
    )
    
    # Additional metadata
    is_system_event = models.BooleanField(
        default=False,
        help_text="Is this a system-generated event?"
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'event_type']),
            models.Index(fields=['company', 'user']),
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.title}"


class Activity(CompanyIsolatedModel):
    """
    General activities (calls, emails, meetings, etc.) related to any entity
    """
    ACTIVITY_TYPES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('demo', 'Demo'),
        ('proposal', 'Proposal'),
        ('follow_up', 'Follow Up'),
        ('note', 'Note'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
        help_text="Type of activity"
    )
    subject = models.CharField(max_length=255, help_text="Activity subject/title")
    description = models.TextField(blank=True, help_text="Activity description")
    
    # Scheduling
    activity_date = models.DateTimeField(help_text="When the activity occurs")
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Activity duration in minutes"
    )
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Due date for follow-up"
    )
    
    # Status and Priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    # Related Entity (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Type of related entity (Account, Contact, Deal, etc.)"
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the related entity"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_activities',
        help_text="User assigned to this activity"
    )
    
    # Participants
    participants = models.ManyToManyField(
        User,
        blank=True,
        related_name='activity_participants',
        help_text="Users participating in this activity"
    )
    
    # Outcome
    outcome = models.TextField(blank=True, help_text="Activity outcome/result")
    next_action = models.TextField(blank=True, help_text="Next action required")
    next_action_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the next action should be completed"
    )
    
    # Location (for meetings)
    location = models.CharField(max_length=255, blank=True, help_text="Meeting location")
    is_online = models.BooleanField(default=False, help_text="Is this an online meeting?")
    meeting_url = models.URLField(blank=True, help_text="Online meeting URL")
    
    # Reminder
    reminder_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Reminder minutes before activity"
    )
    reminder_sent = models.BooleanField(default=False, help_text="Has reminder been sent?")
    
    # Metadata
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='activities')
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-activity_date']
        indexes = [
            models.Index(fields=['company', 'activity_type']),
            models.Index(fields=['company', 'assigned_to']),
            models.Index(fields=['company', 'activity_date']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'priority']),
        ]
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.subject}"
    
    @property
    def is_overdue(self):
        """Check if activity is overdue"""
        if self.due_date and self.status in ['planned', 'in_progress']:
            from django.utils import timezone
            return timezone.now() > self.due_date
        return False
    
    @property
    def is_due_soon(self):
        """Check if activity is due within 24 hours"""
        if self.due_date:
            from django.utils import timezone
            from datetime import timedelta
            return timezone.now() <= self.due_date <= timezone.now() + timedelta(hours=24)
        return False

class Task(CompanyIsolatedModel):
    """
    Specific tasks with due dates and completion tracking
    """
    TASK_TYPES = [
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('follow_up', 'Follow Up'),
        ('research', 'Research'),
        ('proposal', 'Proposal'),
        ('demo', 'Demo'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=255, help_text="Task title")
    description = models.TextField(blank=True, help_text="Task description")
    task_type = models.CharField(
        max_length=20,
        choices=TASK_TYPES,
        default='other'
    )
    
    # Scheduling
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the task should be completed"
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the task should start"
    )
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the task was completed"
    )
    
    # Status and Priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    # Progress
    progress_percentage = models.PositiveIntegerField(
        default=0,
        help_text="Task completion percentage (0-100)"
    )
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated hours to complete"
    )
    actual_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual hours spent"
    )
    
    # Related Entity (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Type of related entity"
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the related entity"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_tasks',
        help_text="User assigned to this task"
    )
    
    # Dependencies
    depends_on = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='dependent_tasks',
        help_text="Tasks this task depends on"
    )
    
    # Reminder
    reminder_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Reminder minutes before due date"
    )
    reminder_sent = models.BooleanField(default=False)
    
    # Metadata
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='tasks')
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-due_date', '-created_at']
        indexes = [
            models.Index(fields=['company', 'assigned_to']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'priority']),
            models.Index(fields=['company', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status in ['not_started', 'in_progress']:
            from django.utils import timezone
            return timezone.now() > self.due_date
        return False
    
    @property
    def is_due_soon(self):
        """Check if task is due within 24 hours"""
        if self.due_date:
            from django.utils import timezone
            from datetime import timedelta
            return timezone.now() <= self.due_date <= timezone.now() + timedelta(hours=24)
        return False
    
    def mark_completed(self):
        """Mark task as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_date = timezone.now()
        self.progress_percentage = 100
        self.save()

class Event(CompanyIsolatedModel):
    """
    Calendar events (meetings, appointments, etc.)
    """
    EVENT_TYPES = [
        ('meeting', 'Meeting'),
        ('appointment', 'Appointment'),
        ('demo', 'Demo'),
        ('presentation', 'Presentation'),
        ('training', 'Training'),
        ('conference', 'Conference'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=255, help_text="Event title")
    description = models.TextField(blank=True, help_text="Event description")
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        default='meeting'
    )
    
    # Scheduling
    start_date = models.DateTimeField(help_text="Event start date and time")
    end_date = models.DateTimeField(help_text="Event end date and time")
    is_all_day = models.BooleanField(default=False, help_text="Is this an all-day event?")
    
    # Location
    location = models.CharField(max_length=255, blank=True, help_text="Event location")
    is_online = models.BooleanField(default=False, help_text="Is this an online event?")
    meeting_url = models.URLField(blank=True, help_text="Online meeting URL")
    
    # Related Entity (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Type of related entity"
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the related entity"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Participants
    organizer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_events',
        help_text="Event organizer"
    )
    attendees = models.ManyToManyField(
        User,
        blank=True,
        related_name='attended_events',
        help_text="Event attendees"
    )
    
    # Recurrence
    is_recurring = models.BooleanField(default=False, help_text="Is this a recurring event?")
    recurrence_pattern = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        blank=True,
        help_text="Recurrence pattern"
    )
    recurrence_end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When recurrence ends"
    )
    
    # Reminder
    reminder_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Reminder minutes before event"
    )
    reminder_sent = models.BooleanField(default=False)
    
    # Metadata
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='events')
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['start_date']
        indexes = [
            models.Index(fields=['company', 'start_date']),
            models.Index(fields=['company', 'event_type']),
            models.Index(fields=['company', 'organizer']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_date}"
    
    @property
    def duration_minutes(self):
        """Calculate event duration in minutes"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            return int(delta.total_seconds() / 60)
        return 0
    
    @property
    def is_past(self):
        """Check if event is in the past"""
        from django.utils import timezone
        return timezone.now() > self.end_date
    
    @property
    def is_upcoming(self):
        """Check if event is upcoming (within 24 hours)"""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() <= self.start_date <= timezone.now() + timedelta(hours=24)

class ActivityNote(CompanyIsolatedModel):
    """
    Notes attached to activities
    """
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    content = models.TextField(help_text="Note content")
    is_private = models.BooleanField(
        default=False,
        help_text="Is this note private to the creator?"
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note for {self.activity.subject}"

class TaskComment(CompanyIsolatedModel):
    """
    Comments on tasks
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField(help_text="Comment content")
    is_private = models.BooleanField(
        default=False,
        help_text="Is this comment private to the creator?"
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on {self.task.title}"