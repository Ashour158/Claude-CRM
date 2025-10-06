# Real-Time Architecture Documentation

## Overview

This document describes the real-time infrastructure for the Claude CRM system, providing WebSocket-based event delivery with long-polling fallback for external-facing clients. The architecture supports multi-region deployments, GDPR compliance, and future extensibility.

## Architecture Components

### 1. Event Bus Abstraction

The event bus provides a pluggable backend system for publish/subscribe messaging patterns.

#### Supported Backends

- **Redis Pub/Sub** (default): Lightweight, low-latency messaging for real-time events
- **NATS** (planned): High-performance, cloud-native messaging
- **Kafka** (planned): Distributed streaming for high-volume event processing

#### Configuration

```python
# settings.py
EVENT_BUS_BACKEND = 'redis'  # Options: 'redis', 'nats', 'kafka'
EVENT_BUS_CHANNEL_PREFIX = 'crm.events'
```

To switch backends, simply change the `EVENT_BUS_BACKEND` setting. No code changes required.

#### Backend Implementation

All backends implement the `EventBusBackend` abstract base class:

```python
class EventBusBackend(ABC):
    def publish(self, channel: str, message: Dict[str, Any]) -> bool
    def subscribe(self, channels: List[str], callback: Callable) -> None
    def unsubscribe(self, channels: List[str]) -> None
    def close(self) -> None
```

### 2. WebSocket Gateway

The WebSocket gateway provides real-time event delivery to connected clients.

#### Endpoint

- **URL**: `ws://your-domain/ws`
- **Protocol**: WebSocket
- **Authentication**: JWT Bearer Token

#### Connection

```javascript
// Connect with JWT token
const token = 'your-jwt-token';
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}&company_id=123`);

ws.onopen = () => {
    console.log('Connected to real-time gateway');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

#### Authentication

Clients must provide a valid JWT token via:
- Query parameter: `?token=<jwt-token>`
- Authorization header: `Authorization: Bearer <jwt-token>`

Invalid or missing tokens result in connection rejection with code 4001.

#### Message Types

##### Client → Server

**Subscribe to Topics**
```json
{
    "type": "subscribe",
    "topics": ["deal.stage.*", "timeline.object.created"]
}
```

**Unsubscribe from Topics**
```json
{
    "type": "unsubscribe",
    "topics": ["deal.stage.*"]
}
```

**Update Cursor (for resumption)**
```json
{
    "type": "cursor.update",
    "cursor": "cursor-id-123"
}
```

**Ping**
```json
{
    "type": "ping"
}
```

##### Server → Client

**Connection Established**
```json
{
    "type": "connection.established",
    "data": {
        "user_id": 123,
        "server_time": "2024-01-01T00:00:00Z"
    }
}
```

**Subscription Confirmed**
```json
{
    "type": "subscription.confirmed",
    "data": {
        "topics": ["deal.stage.*"],
        "timestamp": "2024-01-01T00:00:00Z"
    }
}
```

**Event Delivery**
```json
{
    "type": "event",
    "data": {
        "event_id": "uuid",
        "event_type": "deal.stage.updated",
        "timestamp": "2024-01-01T00:00:00Z",
        "data": {
            "deal_id": 456,
            "old_stage": "prospecting",
            "new_stage": "qualification",
            "user_id": 123
        },
        "metadata": {
            "region": "us-east-1",
            "idempotency_key": "uuid",
            "gdpr_context": {
                "consent": true,
                "retention_days": 365
            }
        }
    }
}
```

**Error**
```json
{
    "type": "error",
    "data": {
        "message": "Invalid topic",
        "timestamp": "2024-01-01T00:00:00Z"
    }
}
```

### 3. Topic Subscription Model

#### Channel Taxonomy

Events follow a hierarchical naming convention:

```
<domain>.<entity>.<action>
```

Examples:
- `deal.stage.updated`
- `deal.stage.created`
- `timeline.object.created`
- `timeline.object.updated`
- `activity.task.completed`
- `contact.email.sent`
- `account.status.changed`

#### Wildcard Subscriptions

Use `*` for wildcard matching:
- `deal.stage.*` - All deal stage events
- `timeline.object.*` - All timeline object events
- `activity.*` - All activity events

### 4. Long-Polling Fallback

For environments without WebSocket support, a long-polling endpoint provides similar functionality.

#### Endpoint

- **URL**: `/api/realtime/poll/`
- **Method**: `GET`
- **Authentication**: JWT Bearer Token (header)

#### Request Parameters

- `topics` (required): Comma-separated list of topics
- `cursor` (optional): Last received event cursor for resumption
- `timeout` (optional): Maximum wait time in seconds (default: 30, max: 60)
- `company_id` (optional): Company ID for multi-tenant isolation

#### Example Request

```bash
curl -X GET "http://localhost:8000/api/realtime/poll/?topics=deal.stage.*,timeline.object.*&timeout=30&company_id=123" \
  -H "Authorization: Bearer <jwt-token>"
```

#### Response

```json
{
    "events": [
        {
            "event_id": "uuid",
            "event_type": "deal.stage.updated",
            "timestamp": "2024-01-01T00:00:00Z",
            "data": {...},
            "metadata": {...}
        }
    ],
    "cursor": "cursor-id-456",
    "timestamp": "2024-01-01T00:00:00Z",
    "has_more": false
}
```

### 5. Delivery Guarantees

#### At-Least-Once Delivery

The system ensures at-least-once delivery through:
- **Idempotency Keys**: Each event has a unique idempotency key
- **Event Deduplication**: Clients should track received event IDs
- **Cursor-Based Resumption**: Clients can resume from last processed event

#### Idempotency

```python
# Publishing with idempotency key
event_bus.publish_event(
    event_type='deal.stage.updated',
    data={...},
    idempotency_key='unique-operation-id'
)
```

Clients should check `metadata.idempotency_key` and skip duplicate events.

#### Cursor Resumption

```javascript
// Store cursor on client
let lastCursor = localStorage.getItem('event_cursor');

// Send cursor update
ws.send(JSON.stringify({
    type: 'cursor.update',
    cursor: lastCursor
}));

// Update cursor when receiving events
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'event') {
        localStorage.setItem('event_cursor', data.data.event_id);
    }
};
```

### 6. Multi-Region Support

#### Region Tagging

All events are tagged with region metadata:

```json
{
    "metadata": {
        "region": "us-east-1",
        ...
    }
}
```

#### Configuration

```python
# settings.py
DEFAULT_REGION = 'us-east-1'
```

Clients can filter events by region if needed for compliance or performance.

### 7. GDPR Compliance

#### Event Metadata

All events include GDPR context:

```json
{
    "metadata": {
        "gdpr_context": {
            "consent": true,
            "purpose": "service_delivery",
            "retention_days": 365,
            "data_subject_id": "user-123"
        }
    }
}
```

#### Retention Policies

```python
# settings.py
GDPR_ENABLED = True
GDPR_RETENTION_DAYS = 365
```

Events older than the retention period are automatically purged (implementation pending).

#### Right to be Forgotten

When a user exercises their right to be forgotten:
1. Stop emitting events for that user
2. Purge historical events from event store
3. Notify subscribers of user data removal

### 8. Structured Logging

All real-time operations are logged with structured metadata:

```python
logger.info(
    "Event emitted",
    extra={
        'event_id': event_id,
        'event_type': event_type,
        'region': region,
        'timestamp': timestamp
    }
)
```

#### Log Categories

- **Connection Events**: `websocket.connected`, `websocket.disconnected`
- **Subscription Events**: `subscription.created`, `subscription.deleted`
- **Delivery Events**: `event.published`, `event.delivered`
- **Error Events**: `websocket.error`, `longpoll.error`

### 9. Metrics

The system exposes metrics for monitoring:

#### Connection Metrics

- `websocket.connected`: WebSocket connections established
- `websocket.disconnected`: WebSocket connections closed
- `websocket.active`: Currently active WebSocket connections

#### Delivery Metrics

- `event.published`: Events published to event bus
- `event.delivered`: Events delivered to clients
- `event.dropped`: Events dropped (no subscribers)

#### Error Metrics

- `websocket.error`: WebSocket errors
- `longpoll.error`: Long-polling errors
- `subscription.error`: Subscription errors

### 10. Security

#### Authentication

- JWT-based authentication for both WebSocket and long-polling
- Token validation on every connection
- Automatic disconnection on token expiry

#### Authorization

- Company isolation: Users only receive events for their company
- Topic validation: Only whitelisted topic patterns allowed
- Rate limiting: Configurable per-user/per-IP limits

#### Data Protection

- TLS/SSL encryption for all connections (production)
- No sensitive data in logs
- GDPR-compliant metadata tagging

## Usage Examples

### Publishing Events

```python
from realtime.event_bus import get_event_bus

event_bus = get_event_bus()

# Publish a deal stage change event
event_bus.publish_event(
    event_type='deal.stage.updated',
    data={
        'deal_id': 123,
        'old_stage': 'prospecting',
        'new_stage': 'qualification',
        'company_id': 456
    },
    region='us-east-1',
    gdpr_context={
        'consent': True,
        'retention_days': 365
    },
    idempotency_key='deal-123-stage-update-1'
)
```

### WebSocket Client (JavaScript)

```javascript
class RealtimeClient {
    constructor(token, companyId) {
        this.token = token;
        this.companyId = companyId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect() {
        this.ws = new WebSocket(
            `ws://localhost:8000/ws?token=${this.token}&company_id=${this.companyId}`
        );
        
        this.ws.onopen = () => {
            console.log('Connected');
            this.reconnectAttempts = 0;
            
            // Subscribe to topics
            this.subscribe(['deal.stage.*', 'timeline.object.*']);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('Disconnected');
            this.reconnect();
        };
    }
    
    subscribe(topics) {
        this.send({
            type: 'subscribe',
            topics: topics
        });
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'event':
                this.onEvent(data.data);
                break;
            case 'error':
                console.error('Server error:', data.data.message);
                break;
            default:
                console.log('Received:', data);
        }
    }
    
    onEvent(event) {
        console.log('Event received:', event);
        // Handle event based on event_type
    }
    
    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            setTimeout(() => this.connect(), delay);
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage
const client = new RealtimeClient('jwt-token', '123');
client.connect();
```

### Long-Polling Client (JavaScript)

```javascript
class LongPollingClient {
    constructor(token, companyId) {
        this.token = token;
        this.companyId = companyId;
        this.topics = [];
        this.cursor = null;
        this.polling = false;
    }
    
    subscribe(topics) {
        this.topics = topics;
        this.startPolling();
    }
    
    async startPolling() {
        this.polling = true;
        
        while (this.polling) {
            try {
                const response = await fetch(
                    `/api/realtime/poll/?topics=${this.topics.join(',')}&timeout=30&company_id=${this.companyId}${this.cursor ? `&cursor=${this.cursor}` : ''}`,
                    {
                        headers: {
                            'Authorization': `Bearer ${this.token}`
                        }
                    }
                );
                
                const data = await response.json();
                
                if (data.events && data.events.length > 0) {
                    data.events.forEach(event => this.onEvent(event));
                    this.cursor = data.cursor;
                }
            } catch (error) {
                console.error('Polling error:', error);
                await this.sleep(5000); // Wait 5s on error
            }
        }
    }
    
    onEvent(event) {
        console.log('Event received:', event);
    }
    
    stopPolling() {
        this.polling = false;
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Usage
const client = new LongPollingClient('jwt-token', '123');
client.subscribe(['deal.stage.*', 'timeline.object.*']);
```

## Performance Considerations

### WebSocket Connections

- Maximum concurrent connections: 10,000 per server (configurable)
- Connection timeout: 60 seconds idle
- Ping/pong interval: 30 seconds

### Long-Polling

- Default timeout: 30 seconds
- Maximum timeout: 60 seconds
- Recommended poll interval: Immediately after receiving events

### Event Bus

- Redis: ~100K messages/second
- Message size limit: 1MB
- Retention: Events are not persisted (fire-and-forget)

## Monitoring and Troubleshooting

### Health Check

```bash
curl http://localhost:8000/api/realtime/health/
```

Response:
```json
{
    "status": "healthy",
    "components": {
        "event_bus": "healthy",
        "cache": "healthy"
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### Logs

Structured logs are available for:
- Connection events
- Subscription management
- Event delivery
- Errors

Example log entry:
```
INFO: Event emitted
{
    "event_id": "uuid",
    "event_type": "deal.stage.updated",
    "region": "us-east-1",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common Issues

#### WebSocket Connection Refused

- Check JWT token validity
- Verify `ALLOWED_HOSTS` in settings
- Check firewall rules

#### Events Not Received

- Verify subscription topics
- Check company_id filtering
- Verify event bus connectivity

#### High Latency

- Check Redis connectivity
- Monitor event bus throughput
- Consider scaling horizontally

## Future Enhancements

### Planned Features

1. **NATS Integration**: High-performance alternative to Redis
2. **Kafka Integration**: For high-volume event streaming
3. **Event Replay**: Replay historical events from event store
4. **Event Filtering**: Server-side event filtering
5. **Binary Protocol**: More efficient than JSON for high-volume
6. **Compression**: Event compression for bandwidth optimization
7. **Metrics Dashboard**: Real-time monitoring dashboard
8. **Load Balancing**: Automatic WebSocket load balancing

### Scalability

The architecture supports horizontal scaling:
- Multiple WebSocket servers behind load balancer
- Redis cluster for event bus
- Shared session store for authentication

## References

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Redis Pub/Sub](https://redis.io/topics/pubsub)
- [WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [JWT Authentication](https://jwt.io/)
- [GDPR Compliance](https://gdpr.eu/)
