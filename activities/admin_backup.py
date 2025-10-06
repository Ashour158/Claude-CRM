# activities/admin.py
from django.contrib import admin
from activities.models import Activity, Task, Event, ActivityNote, TaskComment

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        'subject', 'activity_type', 'activity_date', 'status',
        'priority', 'assigned_to', 'is_overdue'
    ]
    list_filter = [
        'activity_type', 'status', 'priority', 'is_online',
        'is_active', 'activity_date', 'company'
    ]
    search_fields = [
        'subject', 'description', 'outcome', 'next_action',
        'location', 'meeting_url'
    ]
    ordering = ['-activity_date']
    list_editable = ['status', 'priority']
    raw_id_fields = ['assigned_to', 'content_type']
    filter_horizontal = ['participants', 'tags']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('activity_type', 'subject', 'description')
        }),
        ('Scheduling', {
            'fields': ('activity_date', 'duration_minutes', 'due_date')
        }),
        ('Status and Priority', {
            'fields': ('status', 'priority')
        }),
        ('Related Entity', {
            'fields': ('content_type', 'object_id')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'participants')
        }),
        ('Outcome', {
            'fields': ('outcome', 'next_action', 'next_action_date')
        }),
        ('Location', {
            'fields': ('location', 'is_online', 'meeting_url')
        }),
        ('Reminder', {
            'fields': ('reminder_minutes', 'reminder_sent')
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'task_type', 'due_date', 'status',
        'priority', 'progress_percentage', 'assigned_to', 'is_overdue'
    ]
    list_filter = [
        'task_type', 'status', 'priority', 'is_active',
        'due_date', 'start_date', 'company'
    ]
    search_fields = ['title', 'description']
    ordering = ['-due_date', '-created_at']
    list_editable = ['status', 'priority', 'progress_percentage']
    raw_id_fields = ['assigned_to', 'content_type']
    filter_horizontal = ['depends_on', 'tags']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'task_type')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'due_date', 'completed_date')
        }),
        ('Status and Priority', {
            'fields': ('status', 'priority', 'progress_percentage')
        }),
        ('Related Entity', {
            'fields': ('content_type', 'object_id')
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Dependencies', {
            'fields': ('depends_on',)
        }),
        ('Time Tracking', {
            'fields': ('estimated_hours', 'actual_hours')
        }),
        ('Reminder', {
            'fields': ('reminder_minutes', 'reminder_sent')
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'event_type', 'start_date', 'end_date',
        'organizer', 'is_online', 'is_recurring'
    ]
    list_filter = [
        'event_type', 'is_online', 'is_recurring', 'is_active',
        'start_date', 'end_date', 'company'
    ]
    search_fields = [
        'title', 'description', 'location', 'meeting_url'
    ]
    ordering = ['start_date']
    raw_id_fields = ['organizer', 'content_type']
    filter_horizontal = ['attendees', 'tags']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'event_type')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date', 'is_all_day')
        }),
        ('Location', {
            'fields': ('location', 'is_online', 'meeting_url')
        }),
        ('Related Entity', {
            'fields': ('content_type', 'object_id')
        }),
        ('Participants', {
            'fields': ('organizer', 'attendees')
        }),
        ('Recurrence', {
            'fields': ('is_recurring', 'recurrence_pattern', 'recurrence_end_date')
        }),
        ('Reminder', {
            'fields': ('reminder_minutes', 'reminder_sent')
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )

@admin.register(ActivityNote)
class ActivityNoteAdmin(admin.ModelAdmin):
    list_display = ['activity', 'content_preview', 'is_private', 'created_by', 'created_at']
    list_filter = ['is_private', 'created_at', 'activity__company']
    search_fields = ['content', 'activity__subject']
    ordering = ['-created_at']
    raw_id_fields = ['activity', 'created_by']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'content_preview', 'is_private', 'created_by', 'created_at']
    list_filter = ['is_private', 'created_at', 'task__company']
    search_fields = ['content', 'task__title']
    ordering = ['-created_at']
    raw_id_fields = ['task', 'created_by']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'