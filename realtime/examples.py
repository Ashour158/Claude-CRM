# realtime/examples.py
# Usage examples for real-time infrastructure

"""
This file contains code examples demonstrating how to use the real-time infrastructure.
These examples are for documentation purposes and are not automatically executed.
"""


# Example 1: Publishing Events Manually
# ======================================

def example_publish_deal_event():
    """Example: Publish a deal stage change event"""
    from realtime.event_bus import get_event_bus
    
    event_bus = get_event_bus()
    
    # Publish event when deal stage changes
    event_bus.publish_event(
        event_type='deal.stage.updated',
        data={
            'deal_id': 123,
            'deal_name': 'Acme Corp - Enterprise License',
            'old_stage': 'prospecting',
            'new_stage': 'qualification',
            'amount': 50000,
            'company_id': 456,
            'user_id': 789
        },
        region='us-east-1',
        gdpr_context={
            'consent': True,
            'purpose': 'service_delivery',
            'retention_days': 365
        },
        idempotency_key='deal-123-stage-update-20240101'
    )


def example_publish_timeline_event():
    """Example: Publish a timeline event"""
    from realtime.event_bus import get_event_bus
    
    event_bus = get_event_bus()
    
    # Publish timeline event
    event_bus.publish_event(
        event_type='timeline.object.created',
        data={
            'object_type': 'note',
            'object_id': 456,
            'title': 'Meeting notes',
            'related_to': {
                'type': 'deal',
                'id': 123
            },
            'company_id': 456
        }
    )


# Example 2: WebSocket Client (JavaScript)
# ========================================

WEBSOCKET_CLIENT_EXAMPLE = """
// Example WebSocket client implementation

class CRMRealtimeClient {
    constructor(jwtToken, companyId) {
        this.token = jwtToken;
        this.companyId = companyId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.eventHandlers = {};
        this.cursor = localStorage.getItem('crm_event_cursor');
    }
    
    connect() {
        const wsUrl = `ws://${window.location.host}/ws?token=${this.token}&company_id=${this.companyId}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('[CRM] Real-time connection established');
            this.reconnectAttempts = 0;
            
            // Update cursor if we have one
            if (this.cursor) {
                this.updateCursor(this.cursor);
            }
            
            // Subscribe to default topics
            this.subscribe([
                'deal.stage.*',
                'timeline.object.*',
                'activity.task.*'
            ]);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('[CRM] WebSocket error:', error);
        };
        
        this.ws.onclose = (event) => {
            console.log('[CRM] WebSocket closed:', event.code);
            this.reconnect();
        };
    }
    
    subscribe(topics) {
        this.send({
            type: 'subscribe',
            topics: topics
        });
    }
    
    unsubscribe(topics) {
        this.send({
            type: 'unsubscribe',
            topics: topics
        });
    }
    
    updateCursor(cursor) {
        this.send({
            type: 'cursor.update',
            cursor: cursor
        });
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('[CRM] WebSocket not open, message not sent');
        }
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'connection.established':
                console.log('[CRM] Connected as user:', data.data.user_id);
                break;
                
            case 'subscription.confirmed':
                console.log('[CRM] Subscribed to:', data.data.topics);
                break;
                
            case 'event':
                this.handleEvent(data.data);
                break;
                
            case 'error':
                console.error('[CRM] Server error:', data.data.message);
                break;
                
            case 'pong':
                // Heartbeat response
                break;
                
            default:
                console.log('[CRM] Received:', data);
        }
    }
    
    handleEvent(event) {
        // Store cursor for resumption
        this.cursor = event.event_id;
        localStorage.setItem('crm_event_cursor', this.cursor);
        
        // Check for duplicate (idempotency)
        const processedKey = `crm_event_processed_${event.metadata.idempotency_key}`;
        if (localStorage.getItem(processedKey)) {
            console.log('[CRM] Skipping duplicate event:', event.event_id);
            return;
        }
        
        // Mark as processed
        localStorage.setItem(processedKey, 'true');
        
        // Call registered handlers
        const eventType = event.event_type;
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].forEach(handler => {
                try {
                    handler(event);
                } catch (error) {
                    console.error('[CRM] Error in event handler:', error);
                }
            });
        }
        
        // Call wildcard handlers
        Object.keys(this.eventHandlers).forEach(pattern => {
            if (pattern.endsWith('.*')) {
                const prefix = pattern.slice(0, -2);
                if (eventType.startsWith(prefix)) {
                    this.eventHandlers[pattern].forEach(handler => {
                        try {
                            handler(event);
                        } catch (error) {
                            console.error('[CRM] Error in wildcard handler:', error);
                        }
                    });
                }
            }
        });
    }
    
    on(eventType, handler) {
        if (!this.eventHandlers[eventType]) {
            this.eventHandlers[eventType] = [];
        }
        this.eventHandlers[eventType].push(handler);
    }
    
    off(eventType, handler) {
        if (this.eventHandlers[eventType]) {
            const index = this.eventHandlers[eventType].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[eventType].splice(index, 1);
            }
        }
    }
    
    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`[CRM] Reconnecting in ${delay}ms...`);
            setTimeout(() => this.connect(), delay);
        } else {
            console.error('[CRM] Max reconnection attempts reached');
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
    
    // Keep connection alive
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            this.send({ type: 'ping' });
        }, 30000); // Ping every 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
    }
}

// Usage Example
const realtimeClient = new CRMRealtimeClient(
    'your-jwt-token',
    '123' // company_id
);

// Register event handlers
realtimeClient.on('deal.stage.updated', (event) => {
    console.log('Deal stage updated:', event.data);
    // Update UI, show notification, etc.
    updateDealCard(event.data.deal_id, event.data.new_stage);
});

realtimeClient.on('timeline.object.*', (event) => {
    console.log('Timeline event:', event.data);
    // Refresh timeline view
    refreshTimeline();
});

// Connect
realtimeClient.connect();
realtimeClient.startHeartbeat();

// Later, disconnect
// realtimeClient.disconnect();
"""


# Example 3: Long-Polling Client (JavaScript)
# ===========================================

LONGPOLLING_CLIENT_EXAMPLE = """
// Example long-polling client for environments without WebSocket support

class CRMLongPollingClient {
    constructor(jwtToken, companyId) {
        this.token = jwtToken;
        this.companyId = companyId;
        this.topics = [];
        this.cursor = localStorage.getItem('crm_poll_cursor');
        this.polling = false;
        this.eventHandlers = {};
    }
    
    subscribe(topics) {
        this.topics = topics;
        if (!this.polling) {
            this.startPolling();
        }
    }
    
    async startPolling() {
        this.polling = true;
        
        while (this.polling) {
            try {
                const params = new URLSearchParams({
                    topics: this.topics.join(','),
                    timeout: 30,
                    company_id: this.companyId
                });
                
                if (this.cursor) {
                    params.append('cursor', this.cursor);
                }
                
                const response = await fetch(
                    `/api/realtime/poll/?${params.toString()}`,
                    {
                        headers: {
                            'Authorization': `Bearer ${this.token}`
                        }
                    }
                );
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                
                // Process events
                if (data.events && data.events.length > 0) {
                    data.events.forEach(event => this.handleEvent(event));
                }
                
                // Update cursor
                this.cursor = data.cursor;
                localStorage.setItem('crm_poll_cursor', this.cursor);
                
            } catch (error) {
                console.error('[CRM] Polling error:', error);
                // Wait before retrying on error
                await this.sleep(5000);
            }
        }
    }
    
    handleEvent(event) {
        const eventType = event.event_type;
        
        // Check for duplicates
        const processedKey = `crm_event_processed_${event.metadata.idempotency_key}`;
        if (localStorage.getItem(processedKey)) {
            return;
        }
        localStorage.setItem(processedKey, 'true');
        
        // Call handlers
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].forEach(handler => handler(event));
        }
    }
    
    on(eventType, handler) {
        if (!this.eventHandlers[eventType]) {
            this.eventHandlers[eventType] = [];
        }
        this.eventHandlers[eventType].push(handler);
    }
    
    stopPolling() {
        this.polling = false;
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Usage
const pollingClient = new CRMLongPollingClient('jwt-token', '123');
pollingClient.on('deal.stage.updated', (event) => {
    console.log('Deal updated:', event.data);
});
pollingClient.subscribe(['deal.stage.*', 'timeline.object.*']);
"""


# Example 4: Django View Integration
# ===================================

def example_django_view():
    """Example: Publishing events from Django views"""
    from django.http import JsonResponse
    from rest_framework.decorators import api_view, permission_classes
    from rest_framework.permissions import IsAuthenticated
    from realtime.event_bus import get_event_bus
    
    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def update_deal_stage(request, deal_id):
        """Update deal stage and publish event"""
        from deals.models import Deal
        
        deal = Deal.objects.get(id=deal_id)
        old_stage = deal.stage
        new_stage = request.data.get('stage')
        
        # Update deal
        deal.stage = new_stage
        deal.save()
        
        # Publish event
        event_bus = get_event_bus()
        event_bus.publish_event(
            event_type='deal.stage.updated',
            data={
                'deal_id': deal.id,
                'deal_name': deal.name,
                'old_stage': old_stage,
                'new_stage': new_stage,
                'user_id': request.user.id,
                'company_id': deal.company_id
            },
            region='us-east-1',
            gdpr_context={
                'consent': True,
                'retention_days': 365
            },
            idempotency_key=f'deal-{deal.id}-stage-{deal.updated_at.timestamp()}'
        )
        
        return JsonResponse({
            'success': True,
            'deal_id': deal.id,
            'new_stage': new_stage
        })


# Example 5: Signal-Based Auto Events
# ====================================

def example_enable_auto_events():
    """Example: Enable automatic event publishing via signals"""
    
    # In realtime/apps.py, uncomment the signal connections:
    """
    def ready(self):
        from .signals import (
            connect_deal_signals,
            connect_activity_signals,
            connect_timeline_signals
        )
        connect_deal_signals()
        connect_activity_signals()
        connect_timeline_signals()
    """
    
    # Now any changes to Deal, Activity, or Timeline models
    # will automatically publish events to the event bus


if __name__ == '__main__':
    print("This file contains usage examples.")
    print("See the function docstrings and code for details.")
