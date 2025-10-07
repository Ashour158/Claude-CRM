# marketplace/urls.py
# Marketplace and Extensibility URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MarketplaceAppViewSet, AppInstallationViewSet, AppReviewViewSet,
    AppPermissionViewSet, AppWebhookViewSet, AppExecutionViewSet,
    AppAnalyticsViewSet, AppSubscriptionViewSet
)

router = DefaultRouter()
router.register(r'apps', MarketplaceAppViewSet)
router.register(r'installations', AppInstallationViewSet)
router.register(r'reviews', AppReviewViewSet)
router.register(r'permissions', AppPermissionViewSet)
router.register(r'webhooks', AppWebhookViewSet)
router.register(r'executions', AppExecutionViewSet)
router.register(r'analytics', AppAnalyticsViewSet)
router.register(r'subscriptions', AppSubscriptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
