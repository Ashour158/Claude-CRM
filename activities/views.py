# activities/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from activities.models import Activity, Task, Event, ActivityNote, TaskComment
from activities.serializers import (
    ActivitySerializer, ActivityListSerializer, ActivityNoteSerializer,
    TaskSerializer, TaskListSerializer, TaskCommentSerializer,
    EventSerializer, EventListSerializer,
    ActivityStatsSerializer, TaskStatsSerializer, EventStatsSerializer
)
from core.permissions import IsCompanyMember
from core.cache import cache_api_response

class ActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Activity CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'activity_type', 'status', 'priority', 'assigned_to',
        'is_active', 'is_online'
    ]
    search_fields = [
        'subject', 'description', 'outcome', 'next_action',
        'location', 'meeting_url'
    ]
    ordering_fields = [
        'activity_date', 'due_date', 'created_at', 'priority'
    ]
    ordering = ['-activity_date']
    
    def get_queryset(self):
        queryset = Activity.objects.filter(
            company=self.request.active_company
        ).select_related(
            'assigned_to', 'created_by', 'content_type'
        ).prefetch_related('participants', 'notes', 'tags')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(activity_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(activity_date__date__lte=end_date)
        
        # Filter by due date
        due_start = self.request.query_params.get('due_start_date')
        due_end = self.request.query_params.get('due_end_date')
        
        if due_start:
            queryset = queryset.filter(due_date__gte=due_start)
        if due_end:
            queryset = queryset.filter(due_date__lte=due_end)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ActivityListSerializer
        return ActivitySerializer
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark activity as completed"""
        activity = self.get_object()
        activity.status = 'completed'
        activity.save()
        
        return Response({'message': 'Activity marked as completed'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel activity"""
        activity = self.get_object()
        activity.status = 'cancelled'
        activity.save()
        
        return Response({'message': 'Activity cancelled'})
    
    @action(detail=True, methods=['get'])
    def notes(self, request, pk=None):
        """Get activity notes"""
        activity = self.get_object()
        notes = activity.notes.all().order_by('-created_at')
        serializer = ActivityNoteSerializer(notes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """Add note to activity"""
        activity = self.get_object()
        serializer = ActivityNoteSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                activity=activity,
                company=request.active_company,
                created_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_activities(self, request):
        """Get current user's activities"""
        queryset = self.get_queryset().filter(assigned_to=request.user)
        serializer = ActivityListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue activities"""
        queryset = self.get_queryset().filter(
            status__in=['planned', 'in_progress'],
            due_date__lt=timezone.now()
        )
        serializer = ActivityListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        """Get activities due within 24 hours"""
        from datetime import timedelta
        soon = timezone.now() + timedelta(hours=24)
        queryset = self.get_queryset().filter(
            status__in=['planned', 'in_progress'],
            due_date__lte=soon,
            due_date__gte=timezone.now()
        )
        serializer = ActivityListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @cache_api_response(timeout=300)
    def stats(self, request):
        """Get activity statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_activities = queryset.count()
        completed_activities = queryset.filter(status='completed').count()
        overdue_activities = queryset.filter(
            status__in=['planned', 'in_progress'],
            due_date__lt=timezone.now()
        ).count()
        
        # Due soon (within 24 hours)
        from datetime import timedelta
        soon = timezone.now() + timedelta(hours=24)
        due_soon_activities = queryset.filter(
            status__in=['planned', 'in_progress'],
            due_date__lte=soon,
            due_date__gte=timezone.now()
        ).count()
        
        # Activities by type
        activities_by_type = {}
        for activity_type, _ in Activity.ACTIVITY_TYPES:
            count = queryset.filter(activity_type=activity_type).count()
            activities_by_type[activity_type] = count
        
        # Activities by priority
        activities_by_priority = {}
        for priority, _ in Activity.PRIORITY_CHOICES:
            count = queryset.filter(priority=priority).count()
            activities_by_priority[priority] = count
        
        # Activities by status
        activities_by_status = {}
        for status_choice, _ in Activity.STATUS_CHOICES:
            count = queryset.filter(status=status_choice).count()
            activities_by_status[status_choice] = count
        
        # Activities by assignee
        activities_by_assignee = {}
        for activity in queryset.select_related('assigned_to'):
            if activity.assigned_to:
                assignee_name = activity.assigned_to.full_name
                activities_by_assignee[assignee_name] = activities_by_assignee.get(assignee_name, 0) + 1
        
        # Monthly trend (last 12 months)
        monthly_trend = []
        for i in range(12):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_activities = queryset.filter(
                created_at__date__range=[month_start.date(), month_end.date()]
            )
            
            monthly_trend.append({
                'month': month_start.strftime('%Y-%m'),
                'activities': month_activities.count(),
                'completed': month_activities.filter(status='completed').count()
            })
        
        monthly_trend.reverse()
        
        stats_data = {
            'total_activities': total_activities,
            'completed_activities': completed_activities,
            'overdue_activities': overdue_activities,
            'due_soon_activities': due_soon_activities,
            'activities_by_type': activities_by_type,
            'activities_by_priority': activities_by_priority,
            'activities_by_status': activities_by_status,
            'activities_by_assignee': activities_by_assignee,
            'monthly_trend': monthly_trend
        }
        
        serializer = ActivityStatsSerializer(stats_data)
        return Response(serializer.data)

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'task_type', 'status', 'priority', 'assigned_to',
        'is_active'
    ]
    search_fields = [
        'title', 'description'
    ]
    ordering_fields = [
        'due_date', 'start_date', 'created_at', 'priority'
    ]
    ordering = ['-due_date', '-created_at']
    
    def get_queryset(self):
        queryset = Task.objects.filter(
            company=self.request.active_company
        ).select_related(
            'assigned_to', 'created_by', 'content_type'
        ).prefetch_related('comments', 'tags', 'depends_on')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(due_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(due_date__lte=end_date)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        return TaskSerializer
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed"""
        task = self.get_object()
        task.mark_completed()
        
        return Response({'message': 'Task marked as completed'})
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update task progress"""
        task = self.get_object()
        progress = request.data.get('progress_percentage', 0)
        
        if not 0 <= progress <= 100:
            return Response(
                {'error': 'Progress must be between 0 and 100'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.progress_percentage = progress
        if progress == 100:
            task.status = 'completed'
            task.completed_date = timezone.now()
        elif progress > 0:
            task.status = 'in_progress'
        task.save()
        
        return Response({'message': 'Task progress updated'})
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get task comments"""
        task = self.get_object()
        comments = task.comments.all().order_by('-created_at')
        serializer = TaskCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add comment to task"""
        task = self.get_object()
        serializer = TaskCommentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                task=task,
                company=request.active_company,
                created_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get current user's tasks"""
        queryset = self.get_queryset().filter(assigned_to=request.user)
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks"""
        queryset = self.get_queryset().filter(
            status__in=['not_started', 'in_progress'],
            due_date__lt=timezone.now()
        )
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        """Get tasks due within 24 hours"""
        from datetime import timedelta
        soon = timezone.now() + timedelta(hours=24)
        queryset = self.get_queryset().filter(
            status__in=['not_started', 'in_progress'],
            due_date__lte=soon,
            due_date__gte=timezone.now()
        )
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get tasks due today"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            due_date__date=today,
            status__in=['not_started', 'in_progress']
        )
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @cache_api_response(timeout=300)
    def stats(self, request):
        """Get task statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_tasks = queryset.count()
        completed_tasks = queryset.filter(status='completed').count()
        overdue_tasks = queryset.filter(
            status__in=['not_started', 'in_progress'],
            due_date__lt=timezone.now()
        ).count()
        
        # Due soon (within 24 hours)
        from datetime import timedelta
        soon = timezone.now() + timedelta(hours=24)
        due_soon_tasks = queryset.filter(
            status__in=['not_started', 'in_progress'],
            due_date__lte=soon,
            due_date__gte=timezone.now()
        ).count()
        
        # Tasks by type
        tasks_by_type = {}
        for task_type, _ in Task.TASK_TYPES:
            count = queryset.filter(task_type=task_type).count()
            tasks_by_type[task_type] = count
        
        # Tasks by priority
        tasks_by_priority = {}
        for priority, _ in Task.PRIORITY_CHOICES:
            count = queryset.filter(priority=priority).count()
            tasks_by_priority[priority] = count
        
        # Tasks by status
        tasks_by_status = {}
        for status_choice, _ in Task.STATUS_CHOICES:
            count = queryset.filter(status=status_choice).count()
            tasks_by_status[status_choice] = count
        
        # Tasks by assignee
        tasks_by_assignee = {}
        for task in queryset.select_related('assigned_to'):
            if task.assigned_to:
                assignee_name = task.assigned_to.full_name
                tasks_by_assignee[assignee_name] = tasks_by_assignee.get(assignee_name, 0) + 1
        
        # Average completion time
        completed_tasks_with_dates = queryset.filter(
            status='completed',
            completed_date__isnull=False,
            start_date__isnull=False
        )
        completion_times = []
        for task in completed_tasks_with_dates:
            if task.start_date and task.completed_date:
                time_diff = task.completed_date - task.start_date
                completion_times.append(time_diff.days)
        
        average_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # Productivity score (completed tasks / total tasks * 100)
        productivity_score = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        stats_data = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'overdue_tasks': overdue_tasks,
            'due_soon_tasks': due_soon_tasks,
            'tasks_by_type': tasks_by_type,
            'tasks_by_priority': tasks_by_priority,
            'tasks_by_status': tasks_by_status,
            'tasks_by_assignee': tasks_by_assignee,
            'average_completion_time': int(average_completion_time),
            'productivity_score': round(productivity_score, 2)
        }
        
        serializer = TaskStatsSerializer(stats_data)
        return Response(serializer.data)

class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Event CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'event_type', 'organizer', 'is_online', 'is_recurring',
        'is_active'
    ]
    search_fields = [
        'title', 'description', 'location', 'meeting_url'
    ]
    ordering_fields = [
        'start_date', 'end_date', 'created_at'
    ]
    ordering = ['start_date']
    
    def get_queryset(self):
        queryset = Event.objects.filter(
            company=self.request.active_company
        ).select_related(
            'organizer', 'created_by', 'content_type'
        ).prefetch_related('attendees', 'tags')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Get calendar view with date filters"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            start_date__gte=start_date,
            end_date__lte=end_date
        )
        
        serializer = EventListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events"""
        queryset = self.get_queryset().filter(
            start_date__gte=timezone.now()
        ).order_by('start_date')
        serializer = EventListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """Get current user's events (organized or attending)"""
        queryset = self.get_queryset().filter(
            Q(organizer=request.user) | Q(attendees=request.user)
        ).distinct()
        serializer = EventListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @cache_api_response(timeout=300)
    def stats(self, request):
        """Get event statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_events = queryset.count()
        upcoming_events = queryset.filter(start_date__gte=timezone.now()).count()
        past_events = queryset.filter(end_date__lt=timezone.now()).count()
        
        # Events by type
        events_by_type = {}
        for event_type, _ in Event.EVENT_TYPES:
            count = queryset.filter(event_type=event_type).count()
            events_by_type[event_type] = count
        
        # Events by organizer
        events_by_organizer = {}
        for event in queryset.select_related('organizer'):
            if event.organizer:
                organizer_name = event.organizer.full_name
                events_by_organizer[organizer_name] = events_by_organizer.get(organizer_name, 0) + 1
        
        # Monthly calendar (current month)
        current_month = timezone.now().replace(day=1)
        monthly_calendar = []
        
        # Get all days in current month
        from calendar import monthrange
        year, month = current_month.year, current_month.month
        days_in_month = monthrange(year, month)[1]
        
        for day in range(1, days_in_month + 1):
            day_date = current_month.replace(day=day)
            day_events = queryset.filter(
                start_date__date=day_date.date()
            )
            
            monthly_calendar.append({
                'date': day_date.strftime('%Y-%m-%d'),
                'day': day,
                'events': EventListSerializer(day_events, many=True).data
            })
        
        stats_data = {
            'total_events': total_events,
            'upcoming_events': upcoming_events,
            'past_events': past_events,
            'events_by_type': events_by_type,
            'events_by_organizer': events_by_organizer,
            'monthly_calendar': monthly_calendar
        }
        
        serializer = EventStatsSerializer(stats_data)
        return Response(serializer.data)