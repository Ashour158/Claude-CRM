# api_versioning/urls.py
# URL configuration for API versioning module

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    APIVersionViewSet, APIEndpointViewSet,
    APIClientViewSet, APIRequestLogViewSet
)

router = DefaultRouter()
router.register(r'versions', APIVersionViewSet, basename='api-version')
router.register(r'endpoints', APIEndpointViewSet, basename='api-endpoint')
router.register(r'clients', APIClientViewSet, basename='api-client')
router.register(r'logs', APIRequestLogViewSet, basename='api-request-log')

urlpatterns = [
    path('', include(router.urls)),
]
