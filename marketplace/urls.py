# marketplace/urls.py
# URL configuration for marketplace module

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PluginViewSet, PluginInstallationViewSet,
    PluginExecutionViewSet, PluginReviewViewSet
)

router = DefaultRouter()
router.register(r'plugins', PluginViewSet, basename='plugin')
router.register(r'installations', PluginInstallationViewSet, basename='plugin-installation')
router.register(r'executions', PluginExecutionViewSet, basename='plugin-execution')
router.register(r'reviews', PluginReviewViewSet, basename='plugin-review')

urlpatterns = [
    path('', include(router.urls)),
]
