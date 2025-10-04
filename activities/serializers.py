# activities/serializers.py
from rest_framework import serializers
from activities.models import Activity, Task, Event, ActivityNote, TaskComment
from core.serializers import UserBasicSerializer

class ActivityNoteSerializer(serializers.ModelSerializer):
    """Serializer for ActivityNote"""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = ActivityNote
        fields = [
            'id', 'content', 'is_private', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TaskCommentSerializer(serializers.ModelSerializer):
    """Serializer for TaskComment"""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = TaskComment
        fields = [
            'id', 'content', 'is_private', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ActivityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for activity lists"""
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    content_object_name = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    is_due_soon = serializers.ReadOnlyField()
    
    class Meta:
        model = Activity
        fields = [
            'id', 'activity_type', 'subject', 'activity_date',
            'duration_minutes', 'due_date', 'status', 'priority',
            'assigned_to', 'assigned_to_name', 'content_object_name',
            'is_overdue', 'is_due_soon', 'created_at'
        ]
    
    def get_content_object_name(self, obj):
        if obj.content_object:
            if hasattr(obj.content_object, 'name'):
                return obj.content_object.name
            elif hasattr(obj.content_object, 'title'):
                return obj.content_object.title
            elif hasattr(obj.content_object, 'full_name'):
                return obj.content_object.full_name
        return None

class ActivitySerializer(serializers.ModelSerializer):
    """Full serializer for Activity"""
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    assigned_to_detail = UserBasicSerializer(source='assigned_to', read_only=True)
    participants_detail = UserBasicSerializer(source='participants', many=True, read_only=True)
    content_object_name = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    is_due_soon = serializers.ReadOnlyField()
    notes = ActivityNoteSerializer(many=True, read_only=True)
    note_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Activity
        fields = [
            'id', 'activity_type', 'subject', 'description',
            'activity_date', 'duration_minutes', 'due_date',
            'status', 'priority', 'content_type', 'object_id',
            'content_object_name', 'assigned_to', 'assigned_to_name',
            'assigned_to_detail', 'participants', 'participants_detail',
            'outcome', 'next_action', 'next_action_date',
            'location', 'is_online', 'meeting_url',
            'reminder_minutes', 'reminder_sent',
            'tags', 'metadata', 'is_active',
            'notes', 'note_count', 'is_overdue', 'is_due_soon',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'is_overdue', 'is_due_soon', 'created_at', 'updated_at'
        ]
    
    def get_content_object_name(self, obj):
        if obj.content_object:
            if hasattr(obj.content_object, 'name'):
                return obj.content_object.name
            elif hasattr(obj.content_object, 'title'):
                return obj.content_object.title
            elif hasattr(obj.content_object, 'full_name'):
                return obj.content_object.full_name
        return None
    
    def get_note_count(self, obj):
        return obj.notes.count()
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class TaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for task lists"""
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    content_object_name = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    is_due_soon = serializers.ReadOnlyField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'task_type', 'due_date', 'start_date',
            'status', 'priority', 'progress_percentage',
            'assigned_to', 'assigned_to_name', 'content_object_name',
            'is_overdue', 'is_due_soon', 'created_at'
        ]
    
    def get_content_object_name(self, obj):
        if obj.content_object:
            if hasattr(obj.content_object, 'name'):
                return obj.content_object.name
            elif hasattr(obj.content_object, 'title'):
                return obj.content_object.title
            elif hasattr(obj.content_object, 'full_name'):
                return obj.content_object.full_name
        return None

class TaskSerializer(serializers.ModelSerializer):
    """Full serializer for Task"""
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    assigned_to_detail = UserBasicSerializer(source='assigned_to', read_only=True)
    content_object_name = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    is_due_soon = serializers.ReadOnlyField()
    comments = TaskCommentSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    depends_on_titles = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'task_type',
            'due_date', 'start_date', 'completed_date',
            'status', 'priority', 'progress_percentage',
            'estimated_hours', 'actual_hours',
            'content_type', 'object_id', 'content_object_name',
            'assigned_to', 'assigned_to_name', 'assigned_to_detail',
            'depends_on', 'depends_on_titles',
            'reminder_minutes', 'reminder_sent',
            'tags', 'metadata', 'is_active',
            'comments', 'comment_count', 'is_overdue', 'is_due_soon',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'completed_date', 'is_overdue', 'is_due_soon',
            'created_at', 'updated_at'
        ]
    
    def get_content_object_name(self, obj):
        if obj.content_object:
            if hasattr(obj.content_object, 'name'):
                return obj.content_object.name
            elif hasattr(obj.content_object, 'title'):
                return obj.content_object.title
            elif hasattr(obj.content_object, 'full_name'):
                return obj.content_object.full_name
        return None
    
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    def get_depends_on_titles(self, obj):
        return [task.title for task in obj.depends_on.all()]
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for event lists"""
    organizer_name = serializers.CharField(source='organizer.full_name', read_only=True)
    content_object_name = serializers.SerializerMethodField()
    duration_minutes = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'event_type', 'start_date', 'end_date',
            'is_all_day', 'location', 'is_online', 'meeting_url',
            'organizer', 'organizer_name', 'content_object_name',
            'duration_minutes', 'is_past', 'is_upcoming', 'created_at'
        ]
    
    def get_content_object_name(self, obj):
        if obj.content_object:
            if hasattr(obj.content_object, 'name'):
                return obj.content_object.name
            elif hasattr(obj.content_object, 'title'):
                return obj.content_object.title
            elif hasattr(obj.content_object, 'full_name'):
                return obj.content_object.full_name
        return None

class EventSerializer(serializers.ModelSerializer):
    """Full serializer for Event"""
    organizer_name = serializers.CharField(source='organizer.full_name', read_only=True)
    organizer_detail = UserBasicSerializer(source='organizer', read_only=True)
    attendees_detail = UserBasicSerializer(source='attendees', many=True, read_only=True)
    content_object_name = serializers.SerializerMethodField()
    duration_minutes = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_type',
            'start_date', 'end_date', 'is_all_day',
            'location', 'is_online', 'meeting_url',
            'content_type', 'object_id', 'content_object_name',
            'organizer', 'organizer_name', 'organizer_detail',
            'attendees', 'attendees_detail',
            'is_recurring', 'recurrence_pattern', 'recurrence_end_date',
            'reminder_minutes', 'reminder_sent',
            'tags', 'metadata', 'is_active',
            'duration_minutes', 'is_past', 'is_upcoming',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'duration_minutes', 'is_past', 'is_upcoming',
            'created_at', 'updated_at'
        ]
    
    def get_content_object_name(self, obj):
        if obj.content_object:
            if hasattr(obj.content_object, 'name'):
                return obj.content_object.name
            elif hasattr(obj.content_object, 'title'):
                return obj.content_object.title
            elif hasattr(obj.content_object, 'full_name'):
                return obj.content_object.full_name
        return None
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class ActivityStatsSerializer(serializers.Serializer):
    """Serializer for activity statistics"""
    total_activities = serializers.IntegerField()
    completed_activities = serializers.IntegerField()
    overdue_activities = serializers.IntegerField()
    due_soon_activities = serializers.IntegerField()
    activities_by_type = serializers.DictField()
    activities_by_priority = serializers.DictField()
    activities_by_status = serializers.DictField()
    activities_by_assignee = serializers.DictField()
    monthly_trend = serializers.ListField()

class TaskStatsSerializer(serializers.Serializer):
    """Serializer for task statistics"""
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    due_soon_tasks = serializers.IntegerField()
    tasks_by_type = serializers.DictField()
    tasks_by_priority = serializers.DictField()
    tasks_by_status = serializers.DictField()
    tasks_by_assignee = serializers.DictField()
    average_completion_time = serializers.IntegerField()
    productivity_score = serializers.DecimalField(max_digits=5, decimal_places=2)

class EventStatsSerializer(serializers.Serializer):
    """Serializer for event statistics"""
    total_events = serializers.IntegerField()
    upcoming_events = serializers.IntegerField()
    past_events = serializers.IntegerField()
    events_by_type = serializers.DictField()
    events_by_organizer = serializers.DictField()
    monthly_calendar = serializers.ListField()