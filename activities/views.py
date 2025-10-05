# activities/views.py
# Activities Views

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Activity, Task, Event
from .serializers import ActivitySerializer, TaskSerializer, EventSerializer

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['subject', 'description']
    filterset_fields = ['activity_type', 'status', 'assigned_to']
    ordering_fields = ['activity_date', 'created_at']
    ordering = ['-activity_date']

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['status', 'priority', 'assigned_to']
    ordering_fields = ['due_date', 'created_at']
    ordering = ['-due_date']

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = 'completed'
        task.save()
        return Response({'message': 'Task completed'})

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        task = self.get_object()
        task.status = 'in_progress'
        task.save()
        return Response({'message': 'Task reopened'})

    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        tasks = Task.objects.filter(assigned_to=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        from django.utils import timezone
        today = timezone.now().date()
        tasks = Task.objects.filter(due_date=today)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        from django.utils import timezone
        today = timezone.now().date()
        tasks = Task.objects.filter(due_date__lt=today, status__in=['not_started', 'in_progress'])
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['status', 'assigned_to']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['start_date']

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        # Calendar view with filters
        events = self.get_queryset()
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)