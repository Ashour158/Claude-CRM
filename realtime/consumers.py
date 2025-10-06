# realtime/consumers.py
# WebSocket consumers for real-time communication

import json
import logging
from typing import Dict, Any, List
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from .event_bus import get_event_bus

logger = logging.getLogger(__name__)

User = get_user_model()


class RealtimeConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time event delivery
    Supports JWT authentication and topic-based subscriptions
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.company_id = None
        self.subscriptions = set()
        self.cursor = None
        self.metrics = {
            'messages_received': 0,
            'messages_sent': 0,
            'errors': 0
        }
    
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            # Extract JWT token from query string or headers
            token = self._extract_token()
            
            if not token:
                logger.warning("Connection rejected: No token provided")
                await self.close(code=4001, reason="Authentication required")
                return
            
            # Authenticate user
            self.user = await self._authenticate_token(token)
            
            if not self.user:
                logger.warning("Connection rejected: Invalid token")
                await self.close(code=4001, reason="Invalid token")
                return
            
            # Get company context from query params
            self.company_id = self.scope['query_string'].decode().split('company_id=')[-1].split('&')[0] if b'company_id=' in self.scope['query_string'] else None
            
            # Accept connection
            await self.accept()
            
            # Log connection
            logger.info(
                "WebSocket connected",
                extra={
                    'user_id': self.user.id,
                    'user_email': self.user.email,
                    'company_id': self.company_id,
                    'remote_addr': self.scope.get('client', ['unknown'])[0]
                }
            )
            
            # Track connection metric
            self._track_metric('websocket.connected', {
                'user_id': self.user.id,
                'company_id': self.company_id
            })
            
            # Send welcome message
            await self.send(text_data=json.dumps({
                'type': 'connection.established',
                'data': {
                    'user_id': self.user.id,
                    'server_time': self._get_timestamp()
                }
            }))
            
        except Exception as e:
            logger.error(f"Error in connect: {e}", exc_info=True)
            self.metrics['errors'] += 1
            await self.close(code=4000, reason="Connection error")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            # Unsubscribe from all topics
            if self.subscriptions:
                await self._unsubscribe_all()
            
            # Log disconnection
            if self.user:
                logger.info(
                    "WebSocket disconnected",
                    extra={
                        'user_id': self.user.id,
                        'close_code': close_code,
                        'metrics': self.metrics
                    }
                )
                
                # Track disconnection metric
                self._track_metric('websocket.disconnected', {
                    'user_id': self.user.id,
                    'close_code': close_code,
                    'messages_sent': self.metrics['messages_sent'],
                    'messages_received': self.metrics['messages_received'],
                    'errors': self.metrics['errors']
                })
        
        except Exception as e:
            logger.error(f"Error in disconnect: {e}", exc_info=True)
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            self.metrics['messages_received'] += 1
            
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Handle different message types
            if message_type == 'subscribe':
                await self._handle_subscribe(data)
            elif message_type == 'unsubscribe':
                await self._handle_unsubscribe(data)
            elif message_type == 'cursor.update':
                await self._handle_cursor_update(data)
            elif message_type == 'ping':
                await self._handle_ping(data)
            else:
                await self._send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            self.metrics['errors'] += 1
            await self._send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error in receive: {e}", exc_info=True)
            self.metrics['errors'] += 1
            await self._send_error("Internal error")
    
    async def _handle_subscribe(self, data: Dict[str, Any]):
        """Handle subscription request"""
        try:
            topics = data.get('topics', [])
            
            if not topics:
                await self._send_error("No topics specified")
                return
            
            # Validate topics
            valid_topics = []
            for topic in topics:
                if self._is_valid_topic(topic):
                    valid_topics.append(topic)
                else:
                    logger.warning(f"Invalid topic rejected: {topic}")
            
            if not valid_topics:
                await self._send_error("No valid topics")
                return
            
            # Subscribe to topics
            for topic in valid_topics:
                self.subscriptions.add(topic)
            
            # Send confirmation
            await self.send(text_data=json.dumps({
                'type': 'subscription.confirmed',
                'data': {
                    'topics': valid_topics,
                    'timestamp': self._get_timestamp()
                }
            }))
            
            logger.info(f"User {self.user.id} subscribed to: {valid_topics}")
            
            # Track metric
            self._track_metric('subscription.created', {
                'user_id': self.user.id,
                'topics': valid_topics
            })
            
        except Exception as e:
            logger.error(f"Error in subscribe: {e}", exc_info=True)
            await self._send_error("Subscription failed")
    
    async def _handle_unsubscribe(self, data: Dict[str, Any]):
        """Handle unsubscription request"""
        try:
            topics = data.get('topics', [])
            
            if not topics:
                # Unsubscribe from all
                await self._unsubscribe_all()
            else:
                # Unsubscribe from specific topics
                for topic in topics:
                    self.subscriptions.discard(topic)
                
                await self.send(text_data=json.dumps({
                    'type': 'unsubscription.confirmed',
                    'data': {
                        'topics': topics,
                        'timestamp': self._get_timestamp()
                    }
                }))
                
                logger.info(f"User {self.user.id} unsubscribed from: {topics}")
        
        except Exception as e:
            logger.error(f"Error in unsubscribe: {e}", exc_info=True)
            await self._send_error("Unsubscription failed")
    
    async def _handle_cursor_update(self, data: Dict[str, Any]):
        """Handle cursor update for resumption"""
        try:
            self.cursor = data.get('cursor')
            
            await self.send(text_data=json.dumps({
                'type': 'cursor.updated',
                'data': {
                    'cursor': self.cursor,
                    'timestamp': self._get_timestamp()
                }
            }))
            
            logger.debug(f"Cursor updated for user {self.user.id}: {self.cursor}")
        
        except Exception as e:
            logger.error(f"Error updating cursor: {e}", exc_info=True)
    
    async def _handle_ping(self, data: Dict[str, Any]):
        """Handle ping message"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'data': {
                'timestamp': self._get_timestamp()
            }
        }))
    
    async def _unsubscribe_all(self):
        """Unsubscribe from all topics"""
        topics = list(self.subscriptions)
        self.subscriptions.clear()
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscription.confirmed',
            'data': {
                'topics': topics,
                'all': True,
                'timestamp': self._get_timestamp()
            }
        }))
    
    async def _send_error(self, message: str):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'data': {
                'message': message,
                'timestamp': self._get_timestamp()
            }
        }))
        
        self.metrics['errors'] += 1
        
        # Track error metric
        self._track_metric('websocket.error', {
            'user_id': self.user.id if self.user else None,
            'message': message
        })
    
    async def send_event(self, event: Dict[str, Any]):
        """Send event to client"""
        try:
            # Check if client is subscribed to this event type
            event_type = event.get('event_type', '')
            
            if not self._is_subscribed(event_type):
                return
            
            # Check company isolation
            event_company_id = event.get('data', {}).get('company_id')
            if event_company_id and str(event_company_id) != str(self.company_id):
                return
            
            # Send event
            await self.send(text_data=json.dumps({
                'type': 'event',
                'data': event
            }))
            
            self.metrics['messages_sent'] += 1
            
            logger.debug(f"Event sent to user {self.user.id}: {event_type}")
            
        except Exception as e:
            logger.error(f"Error sending event: {e}", exc_info=True)
    
    def _extract_token(self) -> str:
        """Extract JWT token from connection"""
        # Try query string
        query_string = self.scope['query_string'].decode()
        if 'token=' in query_string:
            return query_string.split('token=')[-1].split('&')[0]
        
        # Try headers
        headers = dict(self.scope.get('headers', []))
        auth_header = headers.get(b'authorization', b'').decode()
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        
        return None
    
    @database_sync_to_async
    def _authenticate_token(self, token: str):
        """Authenticate JWT token"""
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id, is_active=True)
            return user
        except (TokenError, User.DoesNotExist) as e:
            logger.warning(f"Authentication failed: {e}")
            return None
    
    def _is_valid_topic(self, topic: str) -> bool:
        """Validate topic pattern"""
        # Implement topic validation logic
        valid_prefixes = ['deal.', 'timeline.', 'activity.', 'contact.', 'account.']
        return any(topic.startswith(prefix) for prefix in valid_prefixes)
    
    def _is_subscribed(self, event_type: str) -> bool:
        """Check if client is subscribed to event type"""
        for subscription in self.subscriptions:
            if subscription.endswith('.*'):
                # Wildcard subscription
                prefix = subscription[:-2]
                if event_type.startswith(prefix):
                    return True
            elif subscription == event_type:
                return True
        
        return False
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    @staticmethod
    def _track_metric(metric_name: str, data: Dict[str, Any]):
        """Track metric"""
        logger.info(f"Metric: {metric_name}", extra=data)
