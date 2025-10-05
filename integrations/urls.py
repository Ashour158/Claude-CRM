# integrations/urls.py
# Integrations URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api-credentials', views.APICredentialViewSet)
router.register(r'webhooks', views.WebhookViewSet)
router.register(r'webhook-logs', views.WebhookLogViewSet)
router.register(r'data-syncs', views.DataSyncViewSet)
router.register(r'data-sync-logs', views.DataSyncLogViewSet)
router.register(r'email-integrations', views.EmailIntegrationViewSet)
router.register(r'calendar-integrations', views.CalendarIntegrationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]