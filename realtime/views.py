# realtime/views.py
# REST API views for real-time features including long-polling fallback

import json
import logging
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .event_bus import get_event_bus

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def long_polling(request):
    """
    Long-polling fallback endpoint for real-time updates
    
    Query Parameters:
    - topics: Comma-separated list of topics to subscribe to
    - cursor: Last received event cursor for resumption
    - timeout: Maximum wait time in seconds (default: 30, max: 60)
    - company_id: Company ID for multi-tenant isolation
    """
    try:
        # Extract parameters
        topics = request.GET.get('topics', '').split(',')
        topics = [t.strip() for t in topics if t.strip()]
        cursor = request.GET.get('cursor')
        timeout = min(int(request.GET.get('timeout', 30)), 60)
        company_id = request.GET.get('company_id')
        
        # Validate topics
        if not topics:
            return Response(
                {'error': 'No topics specified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate topic patterns
        valid_prefixes = ['deal.', 'timeline.', 'activity.', 'contact.', 'account.']
        for topic in topics:
            if not any(topic.startswith(prefix) for prefix in valid_prefixes):
                return Response(
                    {'error': f'Invalid topic: {topic}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Log polling request
        logger.info(
            "Long polling request",
            extra={
                'user_id': request.user.id,
                'topics': topics,
                'cursor': cursor,
                'timeout': timeout,
                'company_id': company_id
            }
        )
        
        # Track metric
        _track_metric('longpoll.request', {
            'user_id': request.user.id,
            'topics': topics
        })
        
        # Poll for events
        events = _poll_events(
            user_id=request.user.id,
            topics=topics,
            cursor=cursor,
            timeout=timeout,
            company_id=company_id
        )
        
        # Return events
        response_data = {
            'events': events,
            'cursor': _generate_cursor(),
            'timestamp': timezone.now().isoformat(),
            'has_more': False  # Could be enhanced with pagination
        }
        
        # Track metric
        _track_metric('longpoll.response', {
            'user_id': request.user.id,
            'event_count': len(events)
        })
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error in long polling: {e}", exc_info=True)
        _track_metric('longpoll.error', {
            'user_id': request.user.id if request.user else None,
            'error': str(e)
        })
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def publish_event(request):
    """
    Publish an event to the event bus
    
    Request Body:
    - event_type: Event type (e.g., 'deal.stage.updated')
    - data: Event payload
    - region: Optional region identifier
    - gdpr_context: Optional GDPR metadata
    - idempotency_key: Optional idempotency key
    """
    try:
        event_type = request.data.get('event_type')
        data = request.data.get('data', {})
        region = request.data.get('region')
        gdpr_context = request.data.get('gdpr_context')
        idempotency_key = request.data.get('idempotency_key')
        
        if not event_type:
            return Response(
                {'error': 'event_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user context
        data['user_id'] = request.user.id
        data['user_email'] = request.user.email
        
        # Publish event
        event_bus = get_event_bus()
        result = event_bus.publish_event(
            event_type=event_type,
            data=data,
            region=region,
            gdpr_context=gdpr_context,
            idempotency_key=idempotency_key
        )
        
        if result:
            return Response(
                {'success': True, 'event_type': event_type},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'error': 'Failed to publish event'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    except Exception as e:
        logger.error(f"Error publishing event: {e}", exc_info=True)
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """Health check endpoint for real-time infrastructure"""
    try:
        # Check event bus connectivity
        event_bus = get_event_bus()
        event_bus_healthy = True  # Could add actual health check
        
        # Check cache connectivity
        cache_healthy = _check_cache_health()
        
        health_status = {
            'status': 'healthy' if (event_bus_healthy and cache_healthy) else 'unhealthy',
            'components': {
                'event_bus': 'healthy' if event_bus_healthy else 'unhealthy',
                'cache': 'healthy' if cache_healthy else 'unhealthy'
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(health_status, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        return Response(
            {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


def _poll_events(
    user_id: int,
    topics: List[str],
    cursor: str,
    timeout: int,
    company_id: str
) -> List[Dict[str, Any]]:
    """
    Poll for events with timeout
    
    This is a simplified implementation. In production, you would:
    1. Use Redis BLPOP or similar blocking operations
    2. Implement proper cursor-based pagination
    3. Add retry logic and error handling
    """
    poll_key = f"longpoll:events:{user_id}:{company_id}"
    start_time = time.time()
    poll_interval = 0.5  # Poll every 500ms
    
    while time.time() - start_time < timeout:
        # Check for cached events
        cached_events = cache.get(poll_key, [])
        
        if cached_events:
            # Filter events by topics
            filtered_events = []
            for event in cached_events:
                event_type = event.get('event_type', '')
                if _matches_topics(event_type, topics):
                    filtered_events.append(event)
            
            if filtered_events:
                # Clear cached events
                cache.delete(poll_key)
                return filtered_events
        
        # Wait before next poll
        time.sleep(poll_interval)
    
    # Timeout reached, return empty
    return []


def _matches_topics(event_type: str, topics: List[str]) -> bool:
    """Check if event type matches any of the subscribed topics"""
    for topic in topics:
        if topic.endswith('.*'):
            # Wildcard matching
            prefix = topic[:-2]
            if event_type.startswith(prefix):
                return True
        elif topic == event_type:
            return True
    return False


def _generate_cursor() -> str:
    """Generate a cursor for event resumption"""
    import uuid
    return str(uuid.uuid4())


def _check_cache_health() -> bool:
    """Check cache connectivity"""
    try:
        test_key = 'health_check_test'
        cache.set(test_key, 'ok', 10)
        result = cache.get(test_key)
        cache.delete(test_key)
        return result == 'ok'
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return False


def _track_metric(metric_name: str, data: Dict[str, Any]):
    """Track metric"""
    logger.info(f"Metric: {metric_name}", extra=data)
