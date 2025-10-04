# integrations/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IntegrationViewSet, EmailIntegrationViewSet, CalendarIntegrationViewSet,
    WebhookViewSet, WebhookLogViewSet, APICredentialViewSet, DataSyncViewSet,
    EmailServiceViewSet, CalendarServiceViewSet, WebhookTestViewSet,
    IntegrationTestViewSet, IntegrationMetricsViewSet
)

router = DefaultRouter()
router.register(r'integrations', IntegrationViewSet)
router.register(r'email-integrations', EmailIntegrationViewSet)
router.register(r'calendar-integrations', CalendarIntegrationViewSet)
router.register(r'webhooks', WebhookViewSet)
router.register(r'webhook-logs', WebhookLogViewSet)
router.register(r'api-credentials', APICredentialViewSet)
router.register(r'data-syncs', DataSyncViewSet)
router.register(r'email-service', EmailServiceViewSet, basename='email-service')
router.register(r'calendar-service', CalendarServiceViewSet, basename='calendar-service')
router.register(r'webhook-test', WebhookTestViewSet, basename='webhook-test')
router.register(r'integration-test', IntegrationTestViewSet, basename='integration-test')
router.register(r'integration-metrics', IntegrationMetricsViewSet, basename='integration-metrics')

urlpatterns = [
    path('', include(router.urls)),
]
