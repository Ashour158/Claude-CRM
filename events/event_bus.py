# events/event_bus.py
# Event Bus Implementation

import redis
import json
import logging
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.utils import timezone
from .models import Event, EventType, EventHandler, EventExecution
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class EventBus:
    """Event Bus for publishing and subscribing to events"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        self.event_stream_key = "events:stream"
        self.event_handlers_key = "events:handlers"
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def publish(self, event_type_name: str, data: Dict[str, Any], 
                company_id: str, user_id: Optional[str] = None,
                content_type: Optional[str] = None, object_id: Optional[str] = None,
                priority: int = 0, correlation_id: Optional[str] = None) -> str:
        """
        Publish an event to the event bus
        
        Args:
            event_type_name: Name of the event type
            data: Event data payload
            company_id: Company ID
            user_id: User ID who triggered the event
            content_type: Related entity type
            object_id: Related entity ID
            priority: Event priority
            correlation_id: Correlation ID for related events
            
        Returns:
            Event ID
        """
        try:
            # Get or create event type
            event_type, created = EventType.objects.get_or_create(
                name=event_type_name,
                company_id=company_id,
                defaults={
                    'description': f'Event type: {event_type_name}',
                    'category': 'business'
                }
            )
            
            # Create event
            event = Event.objects.create(
                event_type=event_type,
                name=f"{event_type_name} Event",
                description=f"Event of type {event_type_name}",
                data=data,
                metadata={
                    'published_at': timezone.now().isoformat(),
                    'source': 'event_bus'
                },
                company_id=company_id,
                triggered_by_id=user_id,
                priority=priority,
                correlation_id=correlation_id or str(uuid.uuid4()),
                content_type_id=content_type,
                object_id=object_id
            )
            
            # Publish to Redis stream
            event_data = {
                'event_id': str(event.id),
                'event_type': event_type_name,
                'company_id': company_id,
                'data': json.dumps(data),
                'priority': priority,
                'correlation_id': event.correlation_id,
                'timestamp': timezone.now().isoformat()
            }
            
            self.redis_client.xadd(self.event_stream_key, event_data)
            
            # Update event type statistics
            event_type.total_events += 1
            event_type.last_triggered = timezone.now()
            event_type.save()
            
            logger.info(f"Event published: {event_type_name} - {event.id}")
            return str(event.id)
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type_name}: {str(e)}")
            raise
    
    def subscribe(self, event_type_name: str, handler_function: callable,
                  company_id: str, conditions: Optional[Dict] = None) -> str:
        """
        Subscribe to events of a specific type
        
        Args:
            event_type_name: Name of the event type
            handler_function: Function to handle the event
            company_id: Company ID
            conditions: Conditions for event handling
            
        Returns:
            Handler ID
        """
        try:
            # Get event type
            event_type = EventType.objects.get(
                name=event_type_name,
                company_id=company_id
            )
            
            # Create event handler
            handler = EventHandler.objects.create(
                name=f"Handler for {event_type_name}",
                description=f"Handler for {event_type_name} events",
                handler_type='custom',
                handler_function=handler_function.__name__,
                conditions=conditions or {},
                company_id=company_id
            )
            
            # Add event type to handler
            handler.event_types.add(event_type)
            
            logger.info(f"Subscribed to {event_type_name} events")
            return str(handler.id)
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {event_type_name}: {str(e)}")
            raise
    
    def process_events(self, company_id: str, batch_size: int = 100):
        """
        Process events from the event stream
        
        Args:
            company_id: Company ID
            batch_size: Number of events to process at once
        """
        try:
            # Get pending events
            events = Event.objects.filter(
                company_id=company_id,
                status='pending'
            ).order_by('-priority', 'created_at')[:batch_size]
            
            for event in events:
                self._process_event(event)
                
        except Exception as e:
            logger.error(f"Failed to process events for company {company_id}: {str(e)}")
    
    def _process_event(self, event: Event):
        """Process a single event"""
        try:
            # Update event status
            event.status = 'processing'
            event.save()
            
            # Get handlers for this event type
            handlers = EventHandler.objects.filter(
                event_types=event.event_type,
                is_active=True,
                company_id=event.company_id
            )
            
            # Execute handlers
            for handler in handlers:
                self._execute_handler(event, handler)
            
            # Mark event as completed
            event.status = 'completed'
            event.processed_at = timezone.now()
            event.save()
            
        except Exception as e:
            logger.error(f"Failed to process event {event.id}: {str(e)}")
            event.status = 'failed'
            event.error_message = str(e)
            event.save()
    
    def _execute_handler(self, event: Event, handler: EventHandler):
        """Execute a handler for an event"""
        try:
            # Create execution record
            execution = EventExecution.objects.create(
                event=event,
                handler=handler,
                status='pending',
                company_id=event.company_id
            )
            
            # Check conditions
            if not self._check_conditions(event, handler):
                execution.status = 'completed'
                execution.save()
                return
            
            # Execute handler
            execution.status = 'running'
            execution.started_at = timezone.now()
            execution.save()
            
            # TODO: Implement actual handler execution
            # This would involve:
            # 1. Loading the handler function
            # 2. Executing with event data
            # 3. Handling results and errors
            
            # Simulate handler execution
            result = self._simulate_handler_execution(event, handler)
            
            # Update execution
            execution.status = 'completed'
            execution.completed_at = timezone.now()
            execution.duration_ms = int(
                (execution.completed_at - execution.started_at).total_seconds() * 1000
            )
            execution.result_data = result
            execution.save()
            
            # Update handler statistics
            handler.total_executions += 1
            handler.successful_executions += 1
            handler.last_executed = timezone.now()
            handler.save()
            
        except Exception as e:
            logger.error(f"Failed to execute handler {handler.id} for event {event.id}: {str(e)}")
            
            # Update execution
            execution.status = 'failed'
            execution.completed_at = timezone.now()
            execution.error_message = str(e)
            execution.save()
            
            # Update handler statistics
            handler.total_executions += 1
            handler.failed_executions += 1
            handler.save()
    
    def _check_conditions(self, event: Event, handler: EventHandler) -> bool:
        """Check if handler conditions are met"""
        if not handler.conditions:
            return True
        
        # TODO: Implement condition checking logic
        # This would involve evaluating conditions against event data
        
        return True
    
    def _simulate_handler_execution(self, event: Event, handler: EventHandler) -> Dict:
        """Simulate handler execution"""
        return {
            'status': 'success',
            'message': f'Handler {handler.name} executed successfully',
            'timestamp': timezone.now().isoformat()
        }
    
    def get_event_stream(self, company_id: str, event_types: Optional[List[str]] = None,
                        limit: int = 100) -> List[Dict]:
        """
        Get events from the stream
        
        Args:
            company_id: Company ID
            event_types: List of event type names to filter
            limit: Maximum number of events to return
            
        Returns:
            List of event data
        """
        try:
            events = Event.objects.filter(
                company_id=company_id
            ).order_by('-created_at')
            
            if event_types:
                events = events.filter(event_type__name__in=event_types)
            
            events = events[:limit]
            
            return [
                {
                    'id': str(event.id),
                    'event_type': event.event_type.name,
                    'name': event.name,
                    'data': event.data,
                    'status': event.status,
                    'created_at': event.created_at.isoformat(),
                    'correlation_id': str(event.correlation_id)
                }
                for event in events
            ]
            
        except Exception as e:
            logger.error(f"Failed to get event stream for company {company_id}: {str(e)}")
            return []
    
    def get_handler_statistics(self, company_id: str) -> Dict:
        """Get handler statistics"""
        try:
            handlers = EventHandler.objects.filter(company_id=company_id)
            
            total_handlers = handlers.count()
            active_handlers = handlers.filter(is_active=True).count()
            total_executions = sum(h.total_executions for h in handlers)
            successful_executions = sum(h.successful_executions for h in handlers)
            
            return {
                'total_handlers': total_handlers,
                'active_handlers': active_handlers,
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get handler statistics for company {company_id}: {str(e)}")
            return {}

# Global event bus instance
event_bus = EventBus()
