# system_config/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomFieldViewSet, CustomFieldValueViewSet, SystemPreferenceViewSet,
    WorkflowConfigurationViewSet, UserPreferenceViewSet, SystemLogViewSet,
    SystemHealthViewSet, DataBackupViewSet, SystemConfigurationViewSet,
    UserConfigurationViewSet, SystemMetricsViewSet, SystemDiagnosticsViewSet
)

router = DefaultRouter()
router.register(r'custom-fields', CustomFieldViewSet)
router.register(r'custom-field-values', CustomFieldValueViewSet)
router.register(r'system-preferences', SystemPreferenceViewSet)
router.register(r'workflow-configurations', WorkflowConfigurationViewSet)
router.register(r'user-preferences', UserPreferenceViewSet)
router.register(r'system-logs', SystemLogViewSet)
router.register(r'system-health', SystemHealthViewSet)
router.register(r'data-backups', DataBackupViewSet)
router.register(r'system-configuration', SystemConfigurationViewSet, basename='system-config')
router.register(r'user-configuration', UserConfigurationViewSet, basename='user-config')
router.register(r'system-metrics', SystemMetricsViewSet, basename='system-metrics')
router.register(r'system-diagnostics', SystemDiagnosticsViewSet, basename='system-diagnostics')

urlpatterns = [
    path('', include(router.urls)),
]
