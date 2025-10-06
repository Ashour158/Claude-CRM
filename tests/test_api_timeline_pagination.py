# tests/test_api_timeline_pagination.py
"""Tests for timeline API endpoint with pagination."""

import pytest
from rest_framework import status
from activities.models import TimelineEvent
from django.urls import reverse


@pytest.mark.django_db
class TestTimelineAPIPagination:
    """Test timeline endpoint with pagination."""
    
    def test_timeline_list_returns_200(self, authenticated_api_client, company, user):
        """Test that timeline list endpoint returns 200 OK."""
        # Create some timeline events
        for i in range(5):
            TimelineEvent.objects.create(
                company=company,
                event_type='created',
                title=f'Test Event {i}',
                user=user
            )
        
        url = reverse('timeline-list')
        response = authenticated_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_timeline_pagination_response_structure(self, authenticated_api_client, company, user):
        """Test that timeline response has pagination keys."""
        # Create timeline events
        for i in range(60):  # More than page_size (50)
            TimelineEvent.objects.create(
                company=company,
                event_type='created',
                title=f'Test Event {i}',
                user=user
            )
        
        url = reverse('timeline-list')
        response = authenticated_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert len(response.data['results']) == 50  # Default page size
    
    def test_timeline_custom_page_size(self, authenticated_api_client, company, user):
        """Test custom page size parameter."""
        # Create timeline events
        for i in range(30):
            TimelineEvent.objects.create(
                company=company,
                event_type='created',
                title=f'Test Event {i}',
                user=user
            )
        
        url = reverse('timeline-list')
        response = authenticated_api_client.get(url, {'page_size': 10})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 10
    
    def test_timeline_max_page_size(self, authenticated_api_client, company, user):
        """Test that max page size is enforced (100)."""
        # Create many timeline events
        for i in range(150):
            TimelineEvent.objects.create(
                company=company,
                event_type='created',
                title=f'Test Event {i}',
                user=user
            )
        
        url = reverse('timeline-list')
        response = authenticated_api_client.get(url, {'page_size': 200})
        
        assert response.status_code == status.HTTP_200_OK
        # Should be capped at max_page_size (100)
        assert len(response.data['results']) == 100
    
    def test_timeline_serializer_fields(self, authenticated_api_client, company, user):
        """Test that serializer returns expected fields."""
        event = TimelineEvent.objects.create(
            company=company,
            event_type='created',
            title='Test Event',
            description='Test Description',
            user=user,
            data={'key': 'value'}
        )
        
        url = reverse('timeline-list')
        response = authenticated_api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        result = response.data['results'][0]
        
        # Check expected fields
        assert 'id' in result
        assert 'event_type' in result
        assert 'created_at' in result
        assert 'data' in result
        assert result['event_type'] == 'created'
        assert result['data'] == {'key': 'value'}
