# activities/admin.py
from django.contrib import admin
from activities.models import Activity, Task, Event, ActivityNote, TaskComment

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['subject', 'activity_type', 'activity_date', 'status', 'priority', 'assigned_to']
    list_filter = ['activity_type', 'status', 'priority', 'is_online', 'is_active', 'activity_date', 'company']
    search_fields = ['subject', 'description', 'assigned_to__email']
    ordering = ['-activity_date']
    list_editable = ['status', 'priority']
    raw_id_fields = ['assigned_to', 'content_type']
    filter_horizontal = ['participants', 'tags']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task_type', 'due_date', 'status', 'priority', 'progress_percentage', 'assigned_to']
    list_filter = ['task_type', 'status', 'priority', 'is_active', 'due_date', 'start_date', 'company']
    search_fields = ['title', 'description', 'assigned_to__email']
    ordering = ['-due_date', '-created_at']
    list_editable = ['status', 'priority', 'progress_percentage']
    raw_id_fields = ['assigned_to', 'content_type']
    filter_horizontal = ['depends_on', 'tags']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'start_date', 'end_date', 'organizer', 'is_online', 'is_active']
    list_filter = ['event_type', 'is_online', 'is_active', 'start_date', 'company']
    search_fields = ['title', 'description', 'organizer__email', 'location']
    ordering = ['start_date']
    raw_id_fields = ['organizer', 'content_type']
    filter_horizontal = ['attendees', 'tags']

@admin.register(ActivityNote)
class ActivityNoteAdmin(admin.ModelAdmin):
    list_display = ['activity', 'content_short', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at']
    search_fields = ['content', 'activity__subject']
    ordering = ['-created_at']
    raw_id_fields = ['activity']
    
    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = 'Content'

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'content_short', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at']
    search_fields = ['content', 'task__title']
    ordering = ['-created_at']
    raw_id_fields = ['task']
    
    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = 'Content'
