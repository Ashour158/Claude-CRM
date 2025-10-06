# core/events/bus.py
# Event bus abstraction for Phase 3

from typing import Any, Dict, List, Callable
from abc import ABC, abstractmethod
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class Event:
    """
    Base event class.
    """
    
    def __init__(self, event_type: str, data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """
        Initialize event.
        
        Args:
            event_type: Type of event (e.g., 'deal.stage_changed', 'lead.converted')
            data: Event data payload
            metadata: Additional metadata (user, timestamp, etc.)
        """
        self.event_type = event_type
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        
        # Add timestamp to metadata if not present
        if 'timestamp' not in self.metadata:
            self.metadata['timestamp'] = self.timestamp.isoformat()
    
    def __str__(self):
        return f"Event({self.event_type}, {self.timestamp})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_type': self.event_type,
            'data': self.data,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class EventBackend(ABC):
    """
    Abstract base class for event backends.
    Backends handle the actual publishing of events.
    """
    
    @abstractmethod
    def publish(self, event: Event, topics: List[str] = None):
        """
        Publish an event to specified topics.
        
        Args:
            event: Event instance
            topics: Optional list of topics to publish to
        """
        pass


class NoOpEventBackend(EventBackend):
    """
    No-op event backend that logs events but doesn't publish them.
    This is the default backend.
    """
    
    def publish(self, event: Event, topics: List[str] = None):
        """
        Log the event but don't publish it anywhere.
        """
        topics_str = ', '.join(topics) if topics else 'default'
        logger.debug(f"[NoOp] Event published: {event.event_type} to topics: {topics_str}")
        logger.debug(f"Event data: {event.data}")


class LoggingEventBackend(EventBackend):
    """
    Event backend that logs events to the logger.
    Useful for debugging and development.
    """
    
    def __init__(self, log_level: str = 'INFO'):
        """
        Initialize logging backend.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    def publish(self, event: Event, topics: List[str] = None):
        """
        Log the event.
        """
        topics_str = ', '.join(topics) if topics else 'default'
        logger.log(
            self.log_level,
            f"Event: {event.event_type} | Topics: {topics_str} | Data: {event.data}"
        )


class InMemoryEventBackend(EventBackend):
    """
    In-memory event backend that stores events in a list.
    Useful for testing.
    """
    
    def __init__(self):
        self.events = []
    
    def publish(self, event: Event, topics: List[str] = None):
        """
        Store the event in memory.
        """
        self.events.append({
            'event': event,
            'topics': topics or []
        })
    
    def get_events(self, event_type: str = None) -> List[Event]:
        """
        Get all stored events, optionally filtered by type.
        """
        if event_type:
            return [e['event'] for e in self.events if e['event'].event_type == event_type]
        return [e['event'] for e in self.events]
    
    def clear(self):
        """Clear all stored events."""
        self.events = []


class EventBus:
    """
    Central event bus for publishing and subscribing to events.
    """
    
    def __init__(self, backend: EventBackend = None):
        """
        Initialize event bus with a backend.
        
        Args:
            backend: Event backend instance (defaults to NoOpEventBackend)
        """
        self.backend = backend or NoOpEventBackend()
        self._subscribers = {}  # topic -> list of handlers
    
    def publish(self, event: Event, topics: List[str] = None):
        """
        Publish an event to the backend and notify subscribers.
        
        Args:
            event: Event instance
            topics: Optional list of topics
        """
        # Publish to backend
        try:
            self.backend.publish(event, topics)
        except Exception as e:
            logger.error(f"Error publishing event to backend: {e}")
        
        # Notify subscribers
        if topics:
            for topic in topics:
                self._notify_subscribers(topic, event)
        else:
            # Notify all subscribers if no topics specified
            for topic in self._subscribers:
                self._notify_subscribers(topic, event)
    
    def subscribe(self, topic: str, handler: Callable):
        """
        Subscribe a handler to a topic.
        
        Args:
            topic: Topic to subscribe to
            handler: Callable that accepts an Event instance
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        
        if handler not in self._subscribers[topic]:
            self._subscribers[topic].append(handler)
            logger.debug(f"Subscribed {handler.__name__} to topic: {topic}")
    
    def unsubscribe(self, topic: str, handler: Callable):
        """
        Unsubscribe a handler from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            handler: Handler to remove
        """
        if topic in self._subscribers and handler in self._subscribers[topic]:
            self._subscribers[topic].remove(handler)
            logger.debug(f"Unsubscribed {handler.__name__} from topic: {topic}")
    
    def _notify_subscribers(self, topic: str, event: Event):
        """
        Notify all subscribers of a topic about an event.
        
        Args:
            topic: Topic to notify
            event: Event instance
        """
        if topic not in self._subscribers:
            return
        
        for handler in self._subscribers[topic]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__}: {e}")


# Global event bus instance
_global_event_bus = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.
    Creates it if it doesn't exist.
    """
    global _global_event_bus
    
    if _global_event_bus is None:
        # Get backend from settings or use default
        backend_class = getattr(settings, 'EVENT_BUS_BACKEND', None)
        
        if backend_class:
            # Import and instantiate backend
            from django.utils.module_loading import import_string
            backend = import_string(backend_class)()
        else:
            # Use default no-op backend
            backend = NoOpEventBackend()
        
        _global_event_bus = EventBus(backend)
        logger.info(f"Initialized global event bus with backend: {backend.__class__.__name__}")
    
    return _global_event_bus


def publish_event(event_type: str, data: Dict[str, Any], topics: List[str] = None, metadata: Dict[str, Any] = None):
    """
    Convenience function to publish an event.
    
    Args:
        event_type: Type of event
        data: Event data payload
        topics: Optional list of topics
        metadata: Optional metadata
    """
    event = Event(event_type, data, metadata)
    bus = get_event_bus()
    bus.publish(event, topics)
