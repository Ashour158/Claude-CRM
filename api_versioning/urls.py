# api_versioning/urls.py
# API Versioning URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    APIVersionViewSet, APIEndpointViewSet, APIClientViewSet,
    APIRequestLogViewSet, APIDeprecationNoticeViewSet
)

router = DefaultRouter()
router.register(r'versions', APIVersionViewSet)
router.register(r'endpoints', APIEndpointViewSet)
router.register(r'clients', APIClientViewSet)
router.register(r'logs', APIRequestLogViewSet)
router.register(r'deprecation-notices', APIDeprecationNoticeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
