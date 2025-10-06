# crm/activities/selectors/timeline_selector.py
"""
Timeline selector layer for data retrieval
"""
from django.contrib.contenttypes.models import ContentType
from crm.activities.models import TimelineEvent


class TimelineSelector:
    """Selector for timeline queries"""
    
    @staticmethod
    def fetch_timeline(organization, target=None, event_types=None, limit=50):
        """
        Fetch timeline events for an entity or organization
        
        Args:
            organization: Company instance
            target: Optional specific object to get timeline for
            event_types: Optional list of event types to filter
            limit: Maximum number of events to return
            
        Returns:
            QuerySet of TimelineEvent instances
        """
        queryset = TimelineEvent.objects.for_organization(organization)
        
        if target:
            content_type = ContentType.objects.get_for_model(target)
            queryset = queryset.filter(
                target_content_type=content_type,
                target_object_id=str(target.pk)
            )
        
        if event_types:
            queryset = queryset.filter(event_type__in=event_types)
        
        return queryset.order_by('-event_date')[:limit]
    
    @staticmethod
    def get_recent_activities(organization, days=7, limit=20):
        """
        Get recent activities for an organization
        
        Args:
            organization: Company instance
            days: Number of days to look back
            limit: Maximum number of events
            
        Returns:
            QuerySet of recent TimelineEvent instances
        """
        return TimelineEvent.objects.for_organization(organization).updated_recently(days)[:limit]
    
    @staticmethod
    def get_user_activities(organization, user, limit=20):
        """
        Get activities by a specific user
        
        Args:
            organization: Company instance
            user: User instance
            limit: Maximum number of events
            
        Returns:
            QuerySet of TimelineEvent instances
        """
        return TimelineEvent.objects.for_organization(organization).filter(
            actor=user
        ).order_by('-event_date')[:limit]
