# realtime/event_bus.py
# Event bus abstraction with pluggable backends

import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime
from django.conf import settings
import redis

logger = logging.getLogger(__name__)


class EventBusBackend(ABC):
    """Abstract base class for event bus backends"""
    
    @abstractmethod
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a channel"""
        pass
    
    @abstractmethod
    def subscribe(self, channels: List[str], callback: Callable) -> None:
        """Subscribe to channels and handle messages with callback"""
        pass
    
    @abstractmethod
    def unsubscribe(self, channels: List[str]) -> None:
        """Unsubscribe from channels"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the connection"""
        pass


class RedisEventBus(EventBusBackend):
    """Redis Pub/Sub implementation of event bus"""
    
    def __init__(self):
        redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.client.pubsub()
        logger.info(f"Redis Event Bus initialized with URL: {redis_url}")
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a Redis channel"""
        try:
            message_json = json.dumps(message)
            result = self.client.publish(channel, message_json)
            logger.debug(f"Published to {channel}: {result} subscribers")
            return result >= 0
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")
            return False
    
    def subscribe(self, channels: List[str], callback: Callable) -> None:
        """Subscribe to Redis channels"""
        try:
            self.pubsub.subscribe(**{channel: callback for channel in channels})
            logger.info(f"Subscribed to channels: {channels}")
            
            # Start listening in a thread
            thread = self.pubsub.run_in_thread(sleep_time=0.001)
            return thread
        except Exception as e:
            logger.error(f"Error subscribing to channels: {e}")
            raise
    
    def unsubscribe(self, channels: List[str]) -> None:
        """Unsubscribe from Redis channels"""
        try:
            self.pubsub.unsubscribe(*channels)
            logger.info(f"Unsubscribed from channels: {channels}")
        except Exception as e:
            logger.error(f"Error unsubscribing from channels: {e}")
    
    def close(self) -> None:
        """Close Redis connection"""
        try:
            self.pubsub.close()
            self.client.close()
            logger.info("Redis Event Bus connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


class NATSEventBus(EventBusBackend):
    """NATS implementation placeholder for future"""
    
    def __init__(self):
        raise NotImplementedError("NATS backend not yet implemented")
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        raise NotImplementedError("NATS backend not yet implemented")
    
    def subscribe(self, channels: List[str], callback: Callable) -> None:
        raise NotImplementedError("NATS backend not yet implemented")
    
    def unsubscribe(self, channels: List[str]) -> None:
        raise NotImplementedError("NATS backend not yet implemented")
    
    def close(self) -> None:
        raise NotImplementedError("NATS backend not yet implemented")


class KafkaEventBus(EventBusBackend):
    """Kafka implementation placeholder for future"""
    
    def __init__(self):
        raise NotImplementedError("Kafka backend not yet implemented")
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        raise NotImplementedError("Kafka backend not yet implemented")
    
    def subscribe(self, channels: List[str], callback: Callable) -> None:
        raise NotImplementedError("Kafka backend not yet implemented")
    
    def unsubscribe(self, channels: List[str]) -> None:
        raise NotImplementedError("Kafka backend not yet implemented")
    
    def close(self) -> None:
        raise NotImplementedError("Kafka backend not yet implemented")


class EventBus:
    """Main event bus interface with pluggable backends"""
    
    _instance = None
    _backend = None
    
    BACKENDS = {
        'redis': RedisEventBus,
        'nats': NATSEventBus,
        'kafka': KafkaEventBus,
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            backend_name = getattr(settings, 'EVENT_BUS_BACKEND', 'redis')
            backend_class = cls.BACKENDS.get(backend_name)
            
            if not backend_class:
                raise ValueError(f"Unknown event bus backend: {backend_name}")
            
            cls._backend = backend_class()
            logger.info(f"Event Bus initialized with backend: {backend_name}")
        
        return cls._instance
    
    def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        region: Optional[str] = None,
        gdpr_context: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> bool:
        """
        Publish an event with metadata
        
        Args:
            event_type: Event type (e.g., 'deal.stage.updated', 'timeline.object.created')
            data: Event payload
            region: Region identifier for multi-region support
            gdpr_context: GDPR compliance metadata
            idempotency_key: Key for idempotent delivery
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Build event envelope
        event = {
            'event_id': event_id,
            'event_type': event_type,
            'timestamp': timestamp,
            'data': data,
            'metadata': {
                'region': region or getattr(settings, 'DEFAULT_REGION', 'us-east-1'),
                'idempotency_key': idempotency_key or event_id,
                'gdpr_context': gdpr_context or {},
            }
        }
        
        # Log event emission
        logger.info(
            f"Event emitted",
            extra={
                'event_id': event_id,
                'event_type': event_type,
                'region': event['metadata']['region'],
                'timestamp': timestamp
            }
        )
        
        # Publish to topic channel
        channel = self._get_channel_name(event_type)
        result = self._backend.publish(channel, event)
        
        # Track metrics
        self._track_metric('event.published', {
            'event_type': event_type,
            'success': result
        })
        
        return result
    
    def subscribe_to_topics(
        self,
        patterns: List[str],
        callback: Callable
    ) -> None:
        """
        Subscribe to event topics using patterns
        
        Args:
            patterns: Topic patterns (e.g., ['deal.stage.*', 'timeline.object.*'])
            callback: Function to handle received events
        """
        channels = [self._get_channel_name(pattern) for pattern in patterns]
        self._backend.subscribe(channels, callback)
        
        logger.info(f"Subscribed to topics: {patterns}")
        
        self._track_metric('subscription.created', {
            'patterns': patterns,
            'channel_count': len(channels)
        })
    
    def unsubscribe_from_topics(self, patterns: List[str]) -> None:
        """Unsubscribe from event topics"""
        channels = [self._get_channel_name(pattern) for pattern in patterns]
        self._backend.unsubscribe(channels)
        
        logger.info(f"Unsubscribed from topics: {patterns}")
    
    def close(self) -> None:
        """Close event bus connection"""
        if self._backend:
            self._backend.close()
    
    @staticmethod
    def _get_channel_name(topic: str) -> str:
        """Convert topic to channel name"""
        prefix = getattr(settings, 'EVENT_BUS_CHANNEL_PREFIX', 'crm.events')
        return f"{prefix}.{topic}"
    
    @staticmethod
    def _track_metric(metric_name: str, data: Dict[str, Any]) -> None:
        """Track metrics for monitoring"""
        # This will be enhanced with actual metrics backend (Prometheus, etc.)
        logger.info(f"Metric: {metric_name}", extra=data)


# Convenience function to get event bus instance
def get_event_bus() -> EventBus:
    """Get the singleton event bus instance"""
    return EventBus()
