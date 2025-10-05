# marketing/urls.py
# Marketing URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'campaigns', views.CampaignViewSet)
router.register(r'email-templates', views.EmailTemplateViewSet)
router.register(r'marketing-lists', views.MarketingListViewSet)
router.register(r'marketing-list-contacts', views.MarketingListContactViewSet)
router.register(r'email-campaigns', views.EmailCampaignViewSet)
router.register(r'email-activities', views.EmailActivityViewSet)
router.register(r'lead-scores', views.LeadScoreViewSet)
router.register(r'marketing-automations', views.MarketingAutomationViewSet)
router.register(r'marketing-automation-executions', views.MarketingAutomationExecutionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]