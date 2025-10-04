# marketing/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CampaignViewSet, EmailTemplateViewSet, EmailCampaignViewSet,
    LeadScoreViewSet, MarketingListViewSet, MarketingListMemberViewSet,
    MarketingEventViewSet, MarketingAnalyticsViewSet
)

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet)
router.register(r'email-templates', EmailTemplateViewSet)
router.register(r'email-campaigns', EmailCampaignViewSet)
router.register(r'lead-scores', LeadScoreViewSet)
router.register(r'marketing-lists', MarketingListViewSet)
router.register(r'list-members', MarketingListMemberViewSet)
router.register(r'events', MarketingEventViewSet)
router.register(r'analytics', MarketingAnalyticsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
