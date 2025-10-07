# mobile/urls.py
# Mobile Application URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MobileDeviceViewSet, MobileSessionViewSet, OfflineDataViewSet,
    PushNotificationViewSet, MobileAppConfigViewSet, MobileAnalyticsViewSet,
    MobileCrashViewSet
)

router = DefaultRouter()
router.register(r'devices', MobileDeviceViewSet)
router.register(r'sessions', MobileSessionViewSet)
router.register(r'offline-data', OfflineDataViewSet)
router.register(r'notifications', PushNotificationViewSet)
router.register(r'config', MobileAppConfigViewSet)
router.register(r'analytics', MobileAnalyticsViewSet)
router.register(r'crashes', MobileCrashViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
