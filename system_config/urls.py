# system_config/urls.py
# System configuration URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'settings', views.SystemSettingViewSet)
router.register(r'custom-fields', views.CustomFieldViewSet)
router.register(r'workflow-rules', views.WorkflowRuleViewSet)
router.register(r'notification-templates', views.NotificationTemplateViewSet)
router.register(r'user-preferences', views.UserPreferenceViewSet)
router.register(r'integrations', views.IntegrationViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]