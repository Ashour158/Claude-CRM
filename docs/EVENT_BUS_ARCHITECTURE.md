# Event Bus Architecture

## Overview

The Event Bus provides a flexible, extensible system for publishing and subscribing to application events with pluggable backends for future real-time integration.

## Architecture

```
Event Publisher → Event Bus → Backend → Subscribers
                              ↓
                         [NoOp, Logging, Redis, WebSocket]
```

## Core Components

### Event

Base event class representing an application event.

```python
from core.events import Event

event = Event(
    event_type='deal.stage_changed',
    data={
        'deal_id': 'uuid',
        'old_stage': 'prospecting',
        'new_stage': 'qualification'
    },
    metadata={
        'user_id': 'uuid',
        'ip_address': '192.168.1.1'
    }
)
```

### EventBackend

Abstract base class for event backends.

**Built-in Backends:**

1. **NoOpEventBackend** (default): Logs events without publishing
2. **LoggingEventBackend**: Logs events to Django logger
3. **InMemoryEventBackend**: Stores events in memory (testing)

### EventBus

Central event bus for managing event flow.

```python
from core.events import EventBus, NoOpEventBackend

bus = EventBus(backend=NoOpEventBackend())
bus.publish(event, topics=['deals', 'notifications'])
```

## Usage

### Publishing Events

#### Simple Publishing

```python
from core.events import publish_event

publish_event(
    event_type='lead.converted',
    data={
        'lead_id': lead.id,
        'account_id': account.id
    },
    topics=['leads', 'conversions']
)
```

#### With Metadata

```python
from core.events import publish_event

publish_event(
    event_type='deal.won',
    data={
        'deal_id': deal.id,
        'amount': str(deal.amount)
    },
    metadata={
        'user_id': str(request.user.id),
        'company_id': str(company.id),
        'timestamp': datetime.utcnow().isoformat()
    },
    topics=['deals', 'sales']
)
```

### Subscribing to Events

```python
from core.events import get_event_bus

def handle_deal_stage_change(event):
    print(f"Deal {event.data['deal_id']} moved to {event.data['new_stage']}")
    # Send notification, update dashboard, etc.

bus = get_event_bus()
bus.subscribe('deals', handle_deal_stage_change)
```

### Unsubscribing

```python
bus.unsubscribe('deals', handle_deal_stage_change)
```

## Standard Event Types

### Deal Events

| Event Type | Description | Data Fields |
|------------|-------------|-------------|
| `deal.created` | New deal created | deal_id, name, amount |
| `deal.updated` | Deal updated | deal_id, changed_fields |
| `deal.stage_changed` | Deal moved to new stage | deal_id, old_stage, new_stage |
| `deal.won` | Deal marked as won | deal_id, amount, close_date |
| `deal.lost` | Deal marked as lost | deal_id, reason |
| `deal.deleted` | Deal deleted | deal_id, name |

### Lead Events

| Event Type | Description | Data Fields |
|------------|-------------|-------------|
| `lead.created` | New lead created | lead_id, name, source |
| `lead.qualified` | Lead qualified | lead_id, score |
| `lead.converted` | Lead converted to account | lead_id, account_id, contact_id |
| `lead.rejected` | Lead rejected | lead_id, reason |

### Account Events

| Event Type | Description | Data Fields |
|------------|-------------|-------------|
| `account.created` | New account created | account_id, name |
| `account.updated` | Account updated | account_id, changed_fields |
| `account.merged` | Accounts merged | source_id, target_id |

### Contact Events

| Event Type | Description | Data Fields |
|------------|-------------|-------------|
| `contact.created` | New contact created | contact_id, name, email |
| `contact.updated` | Contact updated | contact_id, changed_fields |
| `contact.bounced` | Email bounced | contact_id, email |

## Event Backends

### NoOp Backend (Default)

Logs events but doesn't publish them. Useful for development without external dependencies.

```python
from core.events import NoOpEventBackend

backend = NoOpEventBackend()
```

### Logging Backend

Logs events to Django logger at specified level.

```python
from core.events import LoggingEventBackend

backend = LoggingEventBackend(log_level='INFO')
```

**Log Output:**

```
INFO: Event: deal.stage_changed | Topics: deals, notifications | Data: {...}
```

### In-Memory Backend (Testing)

Stores events in memory for testing purposes.

```python
from core.events import InMemoryEventBackend

backend = InMemoryEventBackend()

# Publish event
bus = EventBus(backend)
bus.publish(event)

# Retrieve events
all_events = backend.get_events()
deal_events = backend.get_events('deal.stage_changed')

# Clear events
backend.clear()
```

### Custom Backend

Implement your own backend:

```python
from core.events import EventBackend

class RedisEventBackend(EventBackend):
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def publish(self, event, topics=None):
        for topic in topics or ['default']:
            self.redis.publish(
                topic,
                json.dumps(event.to_dict())
            )
```

**Configure in settings:**

```python
# settings.py
EVENT_BUS_BACKEND = 'myapp.backends.RedisEventBackend'
```

## Integration Examples

### Django Signal Integration

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.events import publish_event

@receiver(post_save, sender=Deal)
def deal_saved(sender, instance, created, **kwargs):
    event_type = 'deal.created' if created else 'deal.updated'
    
    publish_event(
        event_type=event_type,
        data={
            'deal_id': str(instance.id),
            'name': instance.name,
            'amount': str(instance.amount)
        },
        topics=['deals']
    )
```

### View Integration

```python
from rest_framework.decorators import action
from core.events import publish_event

class DealViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=['post'])
    def move(self, request):
        # Move deal logic...
        
        # Publish event
        publish_event(
            event_type='deal.stage_changed',
            data={
                'deal_id': str(deal.id),
                'old_stage': old_stage,
                'new_stage': new_stage
            },
            metadata={
                'user_id': str(request.user.id),
                'company_id': str(request.company.id)
            },
            topics=['deals', 'notifications']
        )
        
        return Response({'message': 'Deal moved'})
```

### Celery Task Integration

```python
from celery import shared_task
from core.events import get_event_bus

@shared_task
def process_deal_events():
    bus = get_event_bus()
    
    def handle_event(event):
        # Process event asynchronously
        if event.event_type == 'deal.won':
            send_congratulations_email(event.data['deal_id'])
    
    bus.subscribe('deals', handle_event)
```

## Testing Events

### Unit Test Example

```python
from core.events import InMemoryEventBackend, EventBus, Event

def test_event_publishing():
    # Setup
    backend = InMemoryEventBackend()
    bus = EventBus(backend)
    
    # Publish event
    event = Event('test.event', {'key': 'value'})
    bus.publish(event, topics=['test'])
    
    # Assert
    events = backend.get_events('test.event')
    assert len(events) == 1
    assert events[0].data['key'] == 'value'
```

### Integration Test Example

```python
def test_deal_move_publishes_event():
    # Setup event capture
    backend = InMemoryEventBackend()
    bus = EventBus(backend)
    
    # Replace global bus
    import core.events.bus
    original_bus = core.events.bus._global_event_bus
    core.events.bus._global_event_bus = bus
    
    try:
        # Trigger action
        response = client.post('/api/deals/move/', {
            'deal_id': deal.id,
            'to_stage_id': stage.id
        })
        
        # Assert event published
        events = backend.get_events('deal.stage_changed')
        assert len(events) == 1
    finally:
        # Restore
        core.events.bus._global_event_bus = original_bus
```

## Performance Considerations

### Asynchronous Processing

For heavy event processing, use async handlers:

```python
import asyncio

async def async_event_handler(event):
    # Heavy processing
    await process_large_dataset(event.data)

bus.subscribe('data_import', async_event_handler)
```

### Event Batching

Batch events for efficiency:

```python
class BatchEventBackend(EventBackend):
    def __init__(self, batch_size=100, flush_interval=5):
        self.batch = []
        self.batch_size = batch_size
        self.flush_interval = flush_interval
    
    def publish(self, event, topics=None):
        self.batch.append((event, topics))
        
        if len(self.batch) >= self.batch_size:
            self.flush()
    
    def flush(self):
        # Process batch
        for event, topics in self.batch:
            # Bulk process
            pass
        self.batch = []
```

## Future Enhancements

### Planned Features

1. **Redis Pub/Sub Backend**: Real-time event streaming
2. **WebSocket Backend**: Live updates to connected clients
3. **Event Replay**: Replay events from history
4. **Event Sourcing**: Full event sourcing support
5. **Dead Letter Queue**: Failed event handling
6. **Event Filtering**: Subscribe with filters
7. **Event Transformation**: Transform events in pipeline
8. **Metrics Collection**: Event flow analytics

### Redis Backend (Preview)

```python
class RedisEventBackend(EventBackend):
    def __init__(self, redis_url):
        self.redis = redis.from_url(redis_url)
    
    def publish(self, event, topics=None):
        for topic in topics or ['default']:
            self.redis.publish(
                f'crm:events:{topic}',
                json.dumps(event.to_dict())
            )
```

### WebSocket Backend (Preview)

```python
class WebSocketEventBackend(EventBackend):
    def __init__(self, websocket_manager):
        self.ws_manager = websocket_manager
    
    def publish(self, event, topics=None):
        message = {
            'type': 'event',
            'event': event.to_dict()
        }
        
        for topic in topics or ['default']:
            self.ws_manager.broadcast(
                topic,
                message
            )
```

## Best Practices

1. **Use Topics**: Organize events by topic for targeted subscriptions
2. **Include Metadata**: Add user, timestamp, and context to all events
3. **Event Naming**: Use consistent naming (entity.action format)
4. **Keep Events Small**: Don't include large payloads
5. **Idempotency**: Design handlers to be idempotent
6. **Error Handling**: Handle subscriber errors gracefully
7. **Testing**: Use InMemoryBackend for testing
8. **Documentation**: Document all event types and data structures

## Troubleshooting

### Events Not Publishing

Check if event bus is initialized:

```python
from core.events import get_event_bus
bus = get_event_bus()
print(f"Backend: {bus.backend.__class__.__name__}")
```

### Subscriber Not Receiving Events

Verify subscription:

```python
bus = get_event_bus()
print(f"Subscribers for 'deals': {len(bus._subscribers.get('deals', []))}")
```

### Performance Issues

Monitor event volume:

```python
# Add logging to backend
class MonitoredBackend(EventBackend):
    def publish(self, event, topics=None):
        logger.info(f"Event published: {event.event_type}")
        # ... existing logic
```

## Security Considerations

1. **Validate Event Data**: Sanitize all event data
2. **Access Control**: Restrict who can publish events
3. **Audit Trail**: Log all event publications
4. **Rate Limiting**: Prevent event flooding
5. **Encryption**: Encrypt sensitive event data
