# tests/test_realtime.py
# Tests for real-time infrastructure

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from realtime.event_bus import EventBus, RedisEventBus, get_event_bus
from realtime.consumers import RealtimeConsumer

User = get_user_model()


@pytest.mark.django_db
class TestEventBus:
    """Test event bus functionality"""
    
    def test_event_bus_singleton(self):
        """Test event bus is a singleton"""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2
    
    @patch('realtime.event_bus.redis')
    def test_redis_backend_publish(self, mock_redis):
        """Test Redis backend publishes events"""
        mock_client = Mock()
        mock_client.publish.return_value = 1
        mock_redis.from_url.return_value = mock_client
        
        backend = RedisEventBus()
        result = backend.publish('test.channel', {'data': 'test'})
        
        assert result is True
        mock_client.publish.assert_called_once()
    
    @patch('realtime.event_bus.redis')
    def test_event_bus_publish_with_metadata(self, mock_redis):
        """Test publishing event with metadata"""
        mock_client = Mock()
        mock_client.publish.return_value = 1
        mock_redis.from_url.return_value = mock_client
        
        # Reset singleton
        EventBus._instance = None
        EventBus._backend = None
        
        event_bus = EventBus()
        result = event_bus.publish_event(
            event_type='deal.stage.updated',
            data={'deal_id': 123},
            region='us-west-2',
            gdpr_context={'consent': True},
            idempotency_key='test-key-123'
        )
        
        assert result is True
    
    def test_event_bus_get_channel_name(self):
        """Test channel name generation"""
        channel = EventBus._get_channel_name('deal.stage.updated')
        assert channel == 'crm.events.deal.stage.updated'


@pytest.mark.django_db
class TestRealtimeConsumer:
    """Test WebSocket consumer"""
    
    @pytest.fixture
    def user(self):
        """Create test user"""
        return User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    @pytest.fixture
    def access_token(self, user):
        """Generate access token"""
        return str(AccessToken.for_user(user))
    
    @pytest.mark.asyncio
    async def test_websocket_connect_with_valid_token(self, user, access_token):
        """Test WebSocket connection with valid token"""
        communicator = WebsocketCommunicator(
            RealtimeConsumer.as_asgi(),
            f"/ws?token={access_token}&company_id=1"
        )
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Should receive welcome message
        response = await communicator.receive_json_from()
        assert response['type'] == 'connection.established'
        assert response['data']['user_id'] == user.id
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_connect_without_token(self):
        """Test WebSocket connection without token"""
        communicator = WebsocketCommunicator(
            RealtimeConsumer.as_asgi(),
            "/ws"
        )
        
        connected, close_code = await communicator.connect()
        assert not connected
        assert close_code == 4001
    
    @pytest.mark.asyncio
    async def test_websocket_subscribe(self, user, access_token):
        """Test subscribing to topics"""
        communicator = WebsocketCommunicator(
            RealtimeConsumer.as_asgi(),
            f"/ws?token={access_token}&company_id=1"
        )
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Receive welcome message
        await communicator.receive_json_from()
        
        # Subscribe to topics
        await communicator.send_json_to({
            'type': 'subscribe',
            'topics': ['deal.stage.*', 'timeline.object.*']
        })
        
        # Should receive confirmation
        response = await communicator.receive_json_from()
        assert response['type'] == 'subscription.confirmed'
        assert 'deal.stage.*' in response['data']['topics']
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_unsubscribe(self, user, access_token):
        """Test unsubscribing from topics"""
        communicator = WebsocketCommunicator(
            RealtimeConsumer.as_asgi(),
            f"/ws?token={access_token}&company_id=1"
        )
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Skip welcome message
        await communicator.receive_json_from()
        
        # Subscribe first
        await communicator.send_json_to({
            'type': 'subscribe',
            'topics': ['deal.stage.*']
        })
        await communicator.receive_json_from()
        
        # Unsubscribe
        await communicator.send_json_to({
            'type': 'unsubscribe',
            'topics': ['deal.stage.*']
        })
        
        # Should receive confirmation
        response = await communicator.receive_json_from()
        assert response['type'] == 'unsubscription.confirmed'
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, user, access_token):
        """Test ping/pong"""
        communicator = WebsocketCommunicator(
            RealtimeConsumer.as_asgi(),
            f"/ws?token={access_token}&company_id=1"
        )
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Skip welcome message
        await communicator.receive_json_from()
        
        # Send ping
        await communicator.send_json_to({'type': 'ping'})
        
        # Should receive pong
        response = await communicator.receive_json_from()
        assert response['type'] == 'pong'
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_invalid_message(self, user, access_token):
        """Test handling invalid message"""
        communicator = WebsocketCommunicator(
            RealtimeConsumer.as_asgi(),
            f"/ws?token={access_token}&company_id=1"
        )
        
        connected, _ = await communicator.connect()
        assert connected
        
        # Skip welcome message
        await communicator.receive_json_from()
        
        # Send invalid JSON
        await communicator.send_to(text_data='invalid json')
        
        # Should receive error
        response = await communicator.receive_json_from()
        assert response['type'] == 'error'
        
        await communicator.disconnect()


@pytest.mark.django_db
class TestLongPolling:
    """Test long-polling API"""
    
    def test_long_polling_without_auth(self):
        """Test long-polling requires authentication"""
        client = APIClient()
        response = client.get('/api/realtime/poll/?topics=deal.stage.*')
        
        assert response.status_code == 401
    
    def test_long_polling_without_topics(self, authenticated_api_client):
        """Test long-polling requires topics"""
        response = authenticated_api_client.get('/api/realtime/poll/')
        
        assert response.status_code == 400
        assert 'error' in response.data
    
    def test_long_polling_with_valid_topics(self, authenticated_api_client):
        """Test long-polling with valid topics"""
        response = authenticated_api_client.get(
            '/api/realtime/poll/?topics=deal.stage.*,timeline.object.*&timeout=1&company_id=1'
        )
        
        assert response.status_code == 200
        assert 'events' in response.data
        assert 'cursor' in response.data
        assert isinstance(response.data['events'], list)
    
    def test_long_polling_with_invalid_topic(self, authenticated_api_client):
        """Test long-polling rejects invalid topics"""
        response = authenticated_api_client.get(
            '/api/realtime/poll/?topics=invalid.topic&timeout=1&company_id=1'
        )
        
        assert response.status_code == 400
        assert 'error' in response.data


@pytest.mark.django_db
class TestPublishEvent:
    """Test event publishing API"""
    
    def test_publish_event_without_auth(self):
        """Test publishing requires authentication"""
        client = APIClient()
        response = client.post('/api/realtime/publish/', {
            'event_type': 'deal.stage.updated',
            'data': {'deal_id': 123}
        })
        
        assert response.status_code == 401
    
    @patch('realtime.views.get_event_bus')
    def test_publish_event_success(self, mock_get_bus, authenticated_api_client):
        """Test successful event publishing"""
        mock_bus = Mock()
        mock_bus.publish_event.return_value = True
        mock_get_bus.return_value = mock_bus
        
        response = authenticated_api_client.post('/api/realtime/publish/', {
            'event_type': 'deal.stage.updated',
            'data': {'deal_id': 123},
            'region': 'us-east-1'
        }, format='json')
        
        assert response.status_code == 201
        assert response.data['success'] is True
        mock_bus.publish_event.assert_called_once()
    
    def test_publish_event_without_type(self, authenticated_api_client):
        """Test publishing requires event_type"""
        response = authenticated_api_client.post('/api/realtime/publish/', {
            'data': {'deal_id': 123}
        }, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data


@pytest.mark.django_db
class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check_accessible_without_auth(self):
        """Test health check is accessible without auth"""
        client = APIClient()
        response = client.get('/api/realtime/health/')
        
        # Should be accessible but might fail if Redis is not available
        assert response.status_code in [200, 503]
    
    @patch('realtime.views.get_event_bus')
    @patch('realtime.views._check_cache_health')
    def test_health_check_healthy(self, mock_cache_health, mock_get_bus):
        """Test health check when all components healthy"""
        mock_cache_health.return_value = True
        
        client = APIClient()
        response = client.get('/api/realtime/health/')
        
        assert response.status_code == 200
        assert response.data['status'] == 'healthy'
        assert 'components' in response.data


@pytest.mark.integration
class TestEventBusIntegration:
    """Integration tests for event bus (requires Redis)"""
    
    @pytest.mark.skipif(
        True,  # Skip by default, enable when Redis is available
        reason="Requires Redis server"
    )
    def test_publish_and_subscribe(self):
        """Test publishing and subscribing to events"""
        event_bus = get_event_bus()
        received_events = []
        
        def callback(message):
            received_events.append(json.loads(message['data']))
        
        # Subscribe
        event_bus.subscribe_to_topics(['test.event.*'], callback)
        
        # Publish
        event_bus.publish_event(
            event_type='test.event.created',
            data={'test': 'data'}
        )
        
        # Wait a bit for message to be received
        import time
        time.sleep(0.5)
        
        assert len(received_events) > 0
        assert received_events[0]['event_type'] == 'test.event.created'


@pytest.mark.unit
class TestTopicMatching:
    """Test topic pattern matching"""
    
    def test_exact_match(self):
        """Test exact topic match"""
        from realtime.consumers import RealtimeConsumer
        consumer = RealtimeConsumer()
        consumer.subscriptions.add('deal.stage.updated')
        
        assert consumer._is_subscribed('deal.stage.updated')
        assert not consumer._is_subscribed('deal.stage.created')
    
    def test_wildcard_match(self):
        """Test wildcard topic match"""
        from realtime.consumers import RealtimeConsumer
        consumer = RealtimeConsumer()
        consumer.subscriptions.add('deal.stage.*')
        
        assert consumer._is_subscribed('deal.stage.updated')
        assert consumer._is_subscribed('deal.stage.created')
        assert not consumer._is_subscribed('deal.amount.changed')


@pytest.mark.unit
class TestTopicValidation:
    """Test topic validation"""
    
    def test_valid_topics(self):
        """Test valid topic patterns"""
        from realtime.consumers import RealtimeConsumer
        consumer = RealtimeConsumer()
        
        assert consumer._is_valid_topic('deal.stage.updated')
        assert consumer._is_valid_topic('timeline.object.created')
        assert consumer._is_valid_topic('activity.task.completed')
        assert consumer._is_valid_topic('contact.email.sent')
        assert consumer._is_valid_topic('account.status.changed')
    
    def test_invalid_topics(self):
        """Test invalid topic patterns"""
        from realtime.consumers import RealtimeConsumer
        consumer = RealtimeConsumer()
        
        assert not consumer._is_valid_topic('invalid.topic')
        assert not consumer._is_valid_topic('random.event')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
