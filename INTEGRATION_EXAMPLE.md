# INTEGRATION_EXAMPLE.md
# Real-Time Infrastructure - Integration Example

This document shows how to integrate the real-time infrastructure with existing CRM models.

## Example: Real-Time Deal Stage Updates

### Step 1: Enable Signal-Based Events (Optional)

Edit `realtime/apps.py` to auto-publish events:

```python
class RealtimeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'realtime'
    verbose_name = 'Real-time Infrastructure'
    
    def ready(self):
        # Auto-connect signals for automatic event publishing
        from .signals import connect_deal_signals
        connect_deal_signals()
```

Now any Deal model change will automatically publish events!

### Step 2: Manual Event Publishing in Views

Update your Deal view to manually publish events:

**File: `deals/views.py`**

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from realtime.event_bus import get_event_bus
from .models import Deal
from .serializers import DealSerializer

class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    
    @action(detail=True, methods=['post'])
    def change_stage(self, request, pk=None):
        """Change deal stage and publish real-time event"""
        deal = self.get_object()
        old_stage = deal.stage
        new_stage = request.data.get('stage')
        
        if not new_stage:
            return Response(
                {'error': 'stage is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the deal
        deal.stage = new_stage
        deal.save()
        
        # Publish real-time event
        event_bus = get_event_bus()
        event_bus.publish_event(
            event_type='deal.stage.updated',
            data={
                'deal_id': deal.id,
                'deal_name': deal.name,
                'old_stage': old_stage,
                'new_stage': new_stage,
                'amount': str(deal.amount) if hasattr(deal, 'amount') else None,
                'company_id': deal.company_id,
                'user_id': request.user.id,
                'user_email': request.user.email,
            },
            region='us-east-1',  # Or get from settings
            gdpr_context={
                'consent': True,
                'purpose': 'service_delivery',
                'retention_days': 365
            },
            idempotency_key=f'deal-{deal.id}-stage-{deal.updated_at.timestamp()}'
        )
        
        return Response({
            'success': True,
            'deal': DealSerializer(deal).data
        })
```

### Step 3: Frontend Integration

**File: `frontend/src/services/realtime.js`**

```javascript
import { getCookie } from './utils';

class RealtimeService {
    constructor() {
        this.ws = null;
        this.eventHandlers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect(token, companyId) {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws?token=${token}&company_id=${companyId}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('[Realtime] Connected');
            this.reconnectAttempts = 0;
            
            // Subscribe to default topics
            this.subscribe([
                'deal.stage.*',
                'deal.amount.*',
                'timeline.object.*',
                'activity.task.*'
            ]);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('[Realtime] Error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('[Realtime] Disconnected');
            this.reconnect(token, companyId);
        };
    }
    
    subscribe(topics) {
        this.send({
            type: 'subscribe',
            topics: topics
        });
    }
    
    on(eventType, handler) {
        if (!this.eventHandlers.has(eventType)) {
            this.eventHandlers.set(eventType, []);
        }
        this.eventHandlers.get(eventType).push(handler);
    }
    
    handleMessage(data) {
        if (data.type === 'event') {
            const event = data.data;
            const eventType = event.event_type;
            
            // Call registered handlers
            if (this.eventHandlers.has(eventType)) {
                this.eventHandlers.get(eventType).forEach(handler => {
                    try {
                        handler(event);
                    } catch (error) {
                        console.error('[Realtime] Handler error:', error);
                    }
                });
            }
            
            // Call wildcard handlers
            this.eventHandlers.forEach((handlers, pattern) => {
                if (pattern.endsWith('.*')) {
                    const prefix = pattern.slice(0, -2);
                    if (eventType.startsWith(prefix)) {
                        handlers.forEach(handler => handler(event));
                    }
                }
            });
        }
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    reconnect(token, companyId) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            setTimeout(() => this.connect(token, companyId), delay);
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

export const realtimeService = new RealtimeService();
```

### Step 4: Use in React Component

**File: `frontend/src/pages/Deals/DealDetail.jsx`**

```javascript
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { realtimeService } from '../../services/realtime';
import { useAuth } from '../../context/AuthContext';

const DealDetail = () => {
    const { dealId } = useParams();
    const { token, user } = useAuth();
    const [deal, setDeal] = useState(null);
    const [notifications, setNotifications] = useState([]);
    
    useEffect(() => {
        // Load initial deal data
        loadDeal();
        
        // Connect to real-time service
        if (token && user.company_id) {
            realtimeService.connect(token, user.company_id);
            
            // Subscribe to deal stage updates
            realtimeService.on('deal.stage.updated', handleDealStageUpdate);
            
            // Subscribe to all deal events for this deal
            realtimeService.on('deal.*', handleDealEvent);
        }
        
        return () => {
            // Cleanup on unmount
            realtimeService.disconnect();
        };
    }, [dealId, token, user.company_id]);
    
    const handleDealStageUpdate = (event) => {
        const { deal_id, old_stage, new_stage, user_email } = event.data;
        
        // Update UI if this is our deal
        if (deal_id === parseInt(dealId)) {
            setDeal(prev => ({
                ...prev,
                stage: new_stage
            }));
            
            // Show notification
            addNotification(
                `Deal stage changed from ${old_stage} to ${new_stage} by ${user_email}`
            );
        }
    };
    
    const handleDealEvent = (event) => {
        console.log('Deal event received:', event);
        // Handle other deal events
    };
    
    const addNotification = (message) => {
        setNotifications(prev => [
            ...prev,
            { id: Date.now(), message, timestamp: new Date() }
        ]);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            setNotifications(prev => prev.filter(n => n.id !== Date.now()));
        }, 5000);
    };
    
    const loadDeal = async () => {
        // Load deal from API
        const response = await fetch(`/api/deals/${dealId}/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        setDeal(data);
    };
    
    const changeDealStage = async (newStage) => {
        // Update deal stage via API
        const response = await fetch(`/api/deals/${dealId}/change_stage/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ stage: newStage })
        });
        
        if (response.ok) {
            // Event will be received via WebSocket, no need to manually update
            console.log('Stage change requested');
        }
    };
    
    return (
        <div>
            <h1>Deal: {deal?.name}</h1>
            <p>Current Stage: {deal?.stage}</p>
            
            {/* Stage change buttons */}
            <div>
                <button onClick={() => changeDealStage('prospecting')}>
                    Prospecting
                </button>
                <button onClick={() => changeDealStage('qualification')}>
                    Qualification
                </button>
                <button onClick={() => changeDealStage('proposal')}>
                    Proposal
                </button>
            </div>
            
            {/* Real-time notifications */}
            <div className="notifications">
                {notifications.map(notif => (
                    <div key={notif.id} className="notification">
                        {notif.message}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default DealDetail;
```

### Step 5: Dashboard Real-Time Updates

**File: `frontend/src/pages/Dashboard/Dashboard.jsx`**

```javascript
import React, { useEffect, useState } from 'react';
import { realtimeService } from '../../services/realtime';
import { useAuth } from '../../context/AuthContext';

const Dashboard = () => {
    const { token, user } = useAuth();
    const [recentActivities, setRecentActivities] = useState([]);
    
    useEffect(() => {
        // Connect to real-time service
        if (token && user.company_id) {
            realtimeService.connect(token, user.company_id);
            
            // Subscribe to all activity events
            realtimeService.on('activity.*', handleActivity);
            realtimeService.on('deal.stage.*', handleDealStage);
            realtimeService.on('timeline.object.*', handleTimeline);
        }
        
        return () => {
            realtimeService.disconnect();
        };
    }, [token, user.company_id]);
    
    const handleActivity = (event) => {
        addActivity({
            type: 'activity',
            message: `New activity: ${event.data.subject}`,
            timestamp: event.timestamp
        });
    };
    
    const handleDealStage = (event) => {
        addActivity({
            type: 'deal',
            message: `${event.data.deal_name}: ${event.data.old_stage} → ${event.data.new_stage}`,
            timestamp: event.timestamp
        });
    };
    
    const handleTimeline = (event) => {
        addActivity({
            type: 'timeline',
            message: `Timeline: ${event.data.title}`,
            timestamp: event.timestamp
        });
    };
    
    const addActivity = (activity) => {
        setRecentActivities(prev => [activity, ...prev].slice(0, 20));
    };
    
    return (
        <div>
            <h1>Dashboard</h1>
            
            <div className="recent-activities">
                <h2>Recent Activities (Real-time)</h2>
                <ul>
                    {recentActivities.map((activity, index) => (
                        <li key={index}>
                            <span className={`badge ${activity.type}`}>
                                {activity.type}
                            </span>
                            {activity.message}
                            <small>{new Date(activity.timestamp).toLocaleTimeString()}</small>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default Dashboard;
```

## Testing the Integration

### 1. Start Redis (required for event bus)
```bash
docker run -d -p 6379:6379 redis:latest
```

### 2. Start Django with ASGI server
```bash
# Install daphne (ASGI server)
pip install daphne

# Run with daphne
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### 3. Test WebSocket Connection
```bash
# In browser console
const ws = new WebSocket('ws://localhost:8000/ws?token=YOUR_JWT_TOKEN&company_id=1');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({type: 'subscribe', topics: ['deal.stage.*']}));
```

### 4. Trigger an Event
```bash
# Change a deal stage via API
curl -X POST http://localhost:8000/api/deals/123/change_stage/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"stage": "qualification"}'
```

### 5. Verify Event Received
Check browser console - you should see:
```json
{
    "type": "event",
    "data": {
        "event_id": "...",
        "event_type": "deal.stage.updated",
        "data": {
            "deal_id": 123,
            "old_stage": "prospecting",
            "new_stage": "qualification"
        }
    }
}
```

## Production Deployment

### 1. Use Production ASGI Server
```bash
# Install uvicorn with websockets support
pip install uvicorn[standard]

# Run with uvicorn
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Configure Nginx for WebSocket
```nginx
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    # WebSocket upgrade
    location /ws {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
    
    # Regular HTTP
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Environment Variables
```bash
# .env
EVENT_BUS_BACKEND=redis
REDIS_URL=redis://redis:6379/0
DEFAULT_REGION=us-east-1
GDPR_ENABLED=True
GDPR_RETENTION_DAYS=365
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/api/realtime/health/
```

### View Logs
```bash
# Real-time logs
tail -f logs/django.log | grep -E "(websocket|event|realtime)"
```

### Metrics (if using Prometheus)
```python
# Add to settings.py
METRICS_BACKEND = 'prometheus'

# Install prometheus client
pip install prometheus-client
```

## Next Steps

1. ✅ Enable signal-based events in `realtime/apps.py`
2. ✅ Integrate frontend real-time service
3. ✅ Test with multiple clients
4. ✅ Set up monitoring and alerts
5. ✅ Deploy to production with proper ASGI server
6. ✅ Configure load balancer for WebSocket sticky sessions

## Support

For issues or questions:
- Check `REALTIME_ARCHITECTURE.md` for detailed documentation
- Review `realtime/examples.py` for more usage patterns
- Check logs for error messages with context
