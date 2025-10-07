# audit/urls.py
# Audit URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuditLogViewSet, AuditPolicyViewSet, AuditReviewViewSet,
    ComplianceReportViewSet, AuditExportViewSet
)

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet)
router.register(r'policies', AuditPolicyViewSet)
router.register(r'reviews', AuditReviewViewSet)
router.register(r'reports', ComplianceReportViewSet)
router.register(r'exports', AuditExportViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
