# tests/crm/activities/test_timeline.py
"""
Tests for timeline/activity tracking
"""
import pytest
from crm.activities.models import TimelineEvent
from crm.activities.services.timeline_service import TimelineService
from crm.activities.selectors.timeline_selector import TimelineSelector
from crm.accounts.models import Account
from core.models import Company, User


@pytest.fixture
def organization():
    """Test organization"""
    return Company.objects.create(name='Test Org', code='TEST')


@pytest.fixture
def user():
    """Test user"""
    return User.objects.create_user(
        email='user@example.com',
        password='testpass123'
    )


@pytest.fixture
def account(organization):
    """Test account"""
    return Account.objects.create(
        organization=organization,
        name='Test Account'
    )


@pytest.mark.django_db
class TestTimelineEvent:
    """Test timeline event model"""
    
    def test_create_timeline_event(self, organization, account, user):
        """Test creating a timeline event"""
        event = TimelineService.record_event(
            organization=organization,
            target=account,
            event_type='call',
            title='Follow-up call',
            description='Called to discuss renewal',
            actor=user
        )
        
        assert event.id is not None
        assert event.event_type == 'call'
        assert event.title == 'Follow-up call'
        assert event.actor == user
        assert event.organization == organization
    
    def test_record_creation_event(self, organization, account, user):
        """Test recording a creation event"""
        event = TimelineService.record_creation(
            organization=organization,
            target=account,
            actor=user
        )
        
        assert event.event_type == 'creation'
        assert 'Account created' in event.title
    
    def test_record_status_change(self, organization, account, user):
        """Test recording status change"""
        event = TimelineService.record_status_change(
            organization=organization,
            target=account,
            old_status='prospect',
            new_status='customer',
            actor=user
        )
        
        assert event.event_type == 'status_change'
        assert 'prospect' in event.title
        assert 'customer' in event.title
    
    def test_fetch_timeline_for_entity(self, organization, account, user):
        """Test fetching timeline for specific entity"""
        # Create multiple events
        TimelineService.record_event(
            organization=organization,
            target=account,
            event_type='call',
            title='Call 1',
            actor=user
        )
        TimelineService.record_event(
            organization=organization,
            target=account,
            event_type='email',
            title='Email 1',
            actor=user
        )
        
        # Fetch timeline
        events = TimelineSelector.fetch_timeline(
            organization=organization,
            target=account
        )
        
        assert events.count() == 2
    
    def test_fetch_timeline_with_filter(self, organization, account, user):
        """Test fetching timeline with event type filter"""
        # Create events of different types
        TimelineService.record_event(
            organization=organization,
            target=account,
            event_type='call',
            title='Call 1',
            actor=user
        )
        TimelineService.record_event(
            organization=organization,
            target=account,
            event_type='email',
            title='Email 1',
            actor=user
        )
        
        # Filter by type
        calls = TimelineSelector.fetch_timeline(
            organization=organization,
            target=account,
            event_types=['call']
        )
        
        assert calls.count() == 1
        assert calls.first().event_type == 'call'
