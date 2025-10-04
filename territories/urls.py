# territories/urls.py
# Territories URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from territories.views import TerritoryViewSet, TerritoryRuleViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'territories', TerritoryViewSet, basename='territory')
router.register(r'rules', TerritoryRuleViewSet, basename='territory-rule')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]
