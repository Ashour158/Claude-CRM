# compliance/urls.py
# Compliance URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompliancePolicyViewSet, DataRetentionRuleViewSet, AccessReviewViewSet,
    DataSubjectRequestViewSet, ComplianceViolationViewSet
)

router = DefaultRouter()
router.register(r'policies', CompliancePolicyViewSet)
router.register(r'retention-rules', DataRetentionRuleViewSet)
router.register(r'access-reviews', AccessReviewViewSet)
router.register(r'data-subject-requests', DataSubjectRequestViewSet)
router.register(r'violations', ComplianceViolationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
