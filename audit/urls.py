# audit/urls.py
# URL configuration for audit module

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuditLogViewSet, AuditLogExportViewSet,
    ComplianceReportViewSet, AuditPolicyViewSet
)

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='audit-log')
router.register(r'exports', AuditLogExportViewSet, basename='audit-export')
router.register(r'compliance-reports', ComplianceReportViewSet, basename='compliance-report')
router.register(r'policies', AuditPolicyViewSet, basename='audit-policy')

urlpatterns = [
    path('', include(router.urls)),
]
