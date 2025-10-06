# core/event_bus.py
# Event bus abstraction for Phase 3

import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class EventBus:
    """
    Event bus abstraction for publishing domain events.
    Default implementation is no-op, can be extended for real-time features.
    """
    
    def __init__(self):
        self.backend = getattr(settings, 'EVENT_BUS_BACKEND', 'noop')
    
    def publish_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        data: Optional[Dict[str, Any]] = None,
        user=None
    ):
        """
        Publish an event to the event bus.
        
        Args:
            event_type: Type of event (create, update, stage_change, etc.)
            entity_type: Type of entity (deal, contact, account, etc.)
            entity_id: ID of the entity
            data: Additional event data
            user: User who triggered the event
        """
        topic = f"{entity_type}.{event_type}"
        
        event_payload = {
            'topic': topic,
            'event_type': event_type,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'data': data or {},
            'user_id': str(user.id) if user else None,
        }
        
        logger.info(
            f"Event published: {topic} for {entity_type}:{entity_id}",
            extra={'event': event_payload}
        )
        
        # Call backend-specific implementation
        if self.backend == 'noop':
            self._noop_publish(event_payload)
        # Future implementations can add redis, kafka, etc.
        # elif self.backend == 'redis':
        #     self._redis_publish(event_payload)
        # elif self.backend == 'kafka':
        #     self._kafka_publish(event_payload)
    
    def _noop_publish(self, event_payload: Dict[str, Any]):
        """No-op implementation - just logs the event."""
        logger.debug(f"[EventBus:NoOp] {event_payload['topic']}")


# Global event bus instance
_event_bus = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def publish_event(
    event_type: str,
    entity_type: str,
    entity_id: str,
    data: Optional[Dict[str, Any]] = None,
    user=None
):
    """
    Convenience function to publish an event.
    
    Usage:
        from core.event_bus import publish_event
        publish_event('stage_change', 'deal', deal.id, {'old_stage': 'x', 'new_stage': 'y'}, user=request.user)
    """
    bus = get_event_bus()
    bus.publish_event(event_type, entity_type, entity_id, data, user)
