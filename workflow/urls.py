# workflow/urls.py
# Workflow URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'workflows', views.WorkflowViewSet)
router.register(r'workflow-executions', views.WorkflowExecutionViewSet)
router.register(r'approval-processes', views.ApprovalProcessViewSet)
router.register(r'approval-requests', views.ApprovalRequestViewSet)
router.register(r'business-rules', views.BusinessRuleViewSet)
router.register(r'business-rule-executions', views.BusinessRuleExecutionViewSet)
router.register(r'process-templates', views.ProcessTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
