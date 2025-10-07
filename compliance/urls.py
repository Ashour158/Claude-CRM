# compliance/urls.py
# URL routing for compliance API

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompliancePolicyViewSet, PolicyAuditLogViewSet, DataResidencyViewSet,
    DataSubjectRequestViewSet, SecretVaultViewSet, SecretAccessLogViewSet,
    AccessReviewViewSet, StaleAccessViewSet, RetentionPolicyViewSet, RetentionLogViewSet
)

router = DefaultRouter()
router.register(r'policies', CompliancePolicyViewSet, basename='compliance-policy')
router.register(r'policy-logs', PolicyAuditLogViewSet, basename='policy-audit-log')
router.register(r'data-residency', DataResidencyViewSet, basename='data-residency')
router.register(r'dsr-requests', DataSubjectRequestViewSet, basename='dsr-request')
router.register(r'secrets', SecretVaultViewSet, basename='secret-vault')
router.register(r'secret-logs', SecretAccessLogViewSet, basename='secret-access-log')
router.register(r'access-reviews', AccessReviewViewSet, basename='access-review')
router.register(r'stale-access', StaleAccessViewSet, basename='stale-access')
router.register(r'retention-policies', RetentionPolicyViewSet, basename='retention-policy')
router.register(r'retention-logs', RetentionLogViewSet, basename='retention-log')

urlpatterns = [
    path('', include(router.urls)),
]
