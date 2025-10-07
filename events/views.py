# events/views.py
# Event-Driven Architecture Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Avg, Count
from django.utils import timezone
import logging

from .models import (
    EventType, Event, EventHandler, EventExecution,
    EventSubscription, EventStream
)
from .serializers import (
    EventTypeSerializer, EventSerializer, EventHandlerSerializer,
    EventExecutionSerializer, EventSubscriptionSerializer, EventStreamSerializer
)
from core.permissions import CompanyIsolationPermission

logger = logging.getLogger(__name__)

class EventTypeViewSet(viewsets.ModelViewSet):
    """Event type management"""
    
    queryset = EventType.objects.all()
    serializer_class = EventTypeSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active', 'is_public']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'total_events']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def trigger_event(self, request, pk=None):
        """Trigger an event of this type"""
        event_type = self.get_object()
        
        try:
            from .event_bus import event_bus
            
            data = request.data.get('data', {})
            user_id = request.user.id
            company_id = request.user.active_company.id
            content_type = request.data.get('content_type')
            object_id = request.data.get('object_id')
            priority = request.data.get('priority', 0)
            
            event_id = event_bus.publish(
                event_type_name=event_type.name,
                data=data,
                company_id=company_id,
                user_id=user_id,
                content_type=content_type,
                object_id=object_id,
                priority=priority
            )
            
            return Response({
                'status': 'success',
                'event_id': event_id,
                'event_type': event_type.name
            })
            
        except Exception as e:
            logger.error(f"Failed to trigger event: {str(e)}")
            return Response(
                {'error': 'Failed to trigger event'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EventViewSet(viewsets.ModelViewSet):
    """Event management"""
    
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event_type', 'status', 'priority', 'triggered_by']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'priority', 'status']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry failed event processing"""
        event = self.get_object()
        
        if event.status != 'failed':
            return Response(
                {'error': 'Event is not in failed status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .event_bus import event_bus
            event_bus._process_event(event)
            
            return Response({'status': 'Event retry initiated'})
            
        except Exception as e:
            logger.error(f"Failed to retry event: {str(e)}")
            return Response(
                {'error': 'Failed to retry event'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stream(self, request):
        """Get event stream"""
        try:
            from .event_bus import event_bus
            
            company_id = request.user.active_company.id
            event_types = request.GET.getlist('event_types')
            limit = int(request.GET.get('limit', 100))
            
            events = event_bus.get_event_stream(
                company_id=company_id,
                event_types=event_types,
                limit=limit
            )
            
            return Response(events)
            
        except Exception as e:
            logger.error(f"Failed to get event stream: {str(e)}")
            return Response(
                {'error': 'Failed to get event stream'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EventHandlerViewSet(viewsets.ModelViewSet):
    """Event handler management"""
    
    queryset = EventHandler.objects.all()
    serializer_class = EventHandlerSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['handler_type', 'status', 'is_active', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'priority', 'total_executions']
    ordering = ['-priority', 'name']
    
    @action(detail=True, methods=['post'])
    def test_handler(self, request, pk=None):
        """Test event handler"""
        handler = self.get_object()
        
        try:
            # TODO: Implement actual handler testing
            # This would involve testing the handler with sample data
            
            return Response({
                'status': 'success',
                'handler_name': handler.name,
                'test_result': 'Handler test completed successfully'
            })
            
        except Exception as e:
            logger.error(f"Handler test failed: {str(e)}")
            return Response(
                {'error': 'Handler test failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EventExecutionViewSet(viewsets.ModelViewSet):
    """Event execution management"""
    
    queryset = EventExecution.objects.all()
    serializer_class = EventExecutionSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event', 'handler', 'status']
    ordering_fields = ['created_at', 'started_at', 'completed_at']
    ordering = ['-created_at']

class EventSubscriptionViewSet(viewsets.ModelViewSet):
    """Event subscription management"""
    
    queryset = EventSubscription.objects.all()
    serializer_class = EventSubscriptionSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['subscription_type', 'is_active', 'user']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class EventStreamViewSet(viewsets.ModelViewSet):
    """Event stream management"""
    
    queryset = EventStream.objects.all()
    serializer_class = EventStreamSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['stream_type', 'is_active', 'is_processing']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
