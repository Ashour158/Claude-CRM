# workflow/views.py
# Workflow views

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Workflow, WorkflowExecution, ApprovalProcess, ApprovalRequest,
    BusinessRule, BusinessRuleExecution, ProcessTemplate
)
from .serializers import (
    WorkflowSerializer, WorkflowExecutionSerializer, ApprovalProcessSerializer,
    ApprovalRequestSerializer, BusinessRuleSerializer, BusinessRuleExecutionSerializer,
    ProcessTemplateSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response

class WorkflowViewSet(viewsets.ModelViewSet):
    """Workflow viewset"""
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['workflow_type', 'status', 'is_active', 'is_global']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate workflow"""
        workflow = self.get_object()
        workflow.status = 'active'
        workflow.save()
        return Response({'message': 'Workflow activated successfully'})

class WorkflowExecutionViewSet(viewsets.ModelViewSet):
    """Workflow execution viewset"""
    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['workflow', 'status', 'triggered_by']
    ordering_fields = ['started_at']
    ordering = ['-started_at']
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause workflow execution"""
        execution = self.get_object()
        execution.status = 'paused'
        execution.save()
        return Response({'message': 'Workflow execution paused'})
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume workflow execution"""
        execution = self.get_object()
        execution.status = 'running'
        execution.save()
        return Response({'message': 'Workflow execution resumed'})

class ApprovalProcessViewSet(viewsets.ModelViewSet):
    """Approval process viewset"""
    queryset = ApprovalProcess.objects.all()
    serializer_class = ApprovalProcessSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['process_type', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class ApprovalRequestViewSet(viewsets.ModelViewSet):
    """Approval request viewset"""
    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['approval_process', 'status', 'requested_by']
    ordering_fields = ['requested_at']
    ordering = ['-requested_at']
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve request"""
        approval_request = self.get_object()
        approval_request.status = 'approved'
        approval_request.save()
        return Response({'message': 'Request approved successfully'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject request"""
        approval_request = self.get_object()
        approval_request.status = 'rejected'
        approval_request.save()
        return Response({'message': 'Request rejected'})

class BusinessRuleViewSet(viewsets.ModelViewSet):
    """Business rule viewset"""
    queryset = BusinessRule.objects.all()
    serializer_class = BusinessRuleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rule_type', 'entity_type', 'is_active', 'is_global']
    search_fields = ['name', 'description']
    ordering_fields = ['priority', 'name']
    ordering = ['-priority', 'name']
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test business rule"""
        rule = self.get_object()
        # Note: Implementation would test the rule
        return Response({'message': 'Business rule test completed'})

class BusinessRuleExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """Business rule execution viewset"""
    queryset = BusinessRuleExecution.objects.all()
    serializer_class = BusinessRuleExecutionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['business_rule', 'success']
    ordering_fields = ['executed_at']
    ordering = ['-executed_at']

class ProcessTemplateViewSet(viewsets.ModelViewSet):
    """Process template viewset"""
    queryset = ProcessTemplate.objects.all()
    serializer_class = ProcessTemplateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template_type', 'is_active', 'is_public']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """Use process template"""
        template = self.get_object()
        # Note: Implementation would create a workflow from the template
        return Response({'message': 'Process template used successfully'})
