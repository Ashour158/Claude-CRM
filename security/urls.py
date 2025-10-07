# security/urls.py
# Enterprise Security URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SecurityPolicyViewSet, SSOConfigurationViewSet, SCIMConfigurationViewSet,
    IPAllowlistViewSet, DeviceManagementViewSet, SessionManagementViewSet,
    AuditLogViewSet, SecurityIncidentViewSet, DataRetentionPolicyViewSet
)

router = DefaultRouter()
router.register(r'policies', SecurityPolicyViewSet)
router.register(r'sso', SSOConfigurationViewSet)
router.register(r'scim', SCIMConfigurationViewSet)
router.register(r'ip-allowlist', IPAllowlistViewSet)
router.register(r'devices', DeviceManagementViewSet)
router.register(r'sessions', SessionManagementViewSet)
router.register(r'audit-logs', AuditLogViewSet)
router.register(r'incidents', SecurityIncidentViewSet)
router.register(r'retention-policies', DataRetentionPolicyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
