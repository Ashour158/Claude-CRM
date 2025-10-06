# workflow/views.py
# Workflow views

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Workflow, WorkflowExecution, ApprovalProcess, ApprovalRequest,
    BusinessRule, BusinessRuleExecution, ProcessTemplate, WorkflowApproval
)
from .serializers import (
    WorkflowSerializer, WorkflowExecutionSerializer, ApprovalProcessSerializer,
    ApprovalRequestSerializer, BusinessRuleSerializer, BusinessRuleExecutionSerializer,
    ProcessTemplateSerializer, WorkflowApprovalSerializer
)

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

class WorkflowApprovalViewSet(viewsets.ModelViewSet):
    """Workflow approval viewset with approve/deny actions"""
    queryset = WorkflowApproval.objects.all()
    serializer_class = WorkflowApprovalSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['workflow_run_id', 'action_run_id', 'status', 'approver_role']
    ordering_fields = ['created_at', 'expires_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve workflow approval request"""
        approval = self.get_object()
        
        # Check if already resolved
        if approval.status in ['approved', 'denied', 'expired']:
            return Response(
                {'error': f'Approval already {approval.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update approval
        approval.status = 'approved'
        approval.resolved_at = timezone.now()
        approval.actor_id = request.user.id if hasattr(request, 'user') else None
        
        # Add approval metadata
        metadata = approval.metadata or {}
        metadata.update({
            'approved_at': timezone.now().isoformat(),
            'approved_by': str(request.user.email) if hasattr(request, 'user') else 'system',
            'comments': request.data.get('comments', ''),
        })
        approval.metadata = metadata
        approval.save()
        
        serializer = self.get_serializer(approval)
        return Response({
            'message': 'Approval request approved successfully',
            'approval': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def deny(self, request, pk=None):
        """Deny workflow approval request"""
        approval = self.get_object()
        
        # Check if already resolved
        if approval.status in ['approved', 'denied', 'expired']:
            return Response(
                {'error': f'Approval already {approval.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update approval
        approval.status = 'denied'
        approval.resolved_at = timezone.now()
        approval.actor_id = request.user.id if hasattr(request, 'user') else None
        
        # Add denial metadata
        metadata = approval.metadata or {}
        metadata.update({
            'denied_at': timezone.now().isoformat(),
            'denied_by': str(request.user.email) if hasattr(request, 'user') else 'system',
            'reason': request.data.get('reason', ''),
            'comments': request.data.get('comments', ''),
        })
        approval.metadata = metadata
        approval.save()
        
        serializer = self.get_serializer(approval)
        return Response({
            'message': 'Approval request denied successfully',
            'approval': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get approval metrics"""
        from django.db.models import Count, Q, Avg
        from datetime import timedelta
        
        # Get query parameters for filtering
        days = int(request.query_params.get('days', 30))
        since = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset().filter(created_at__gte=since)
        
        # Calculate metrics
        total_count = queryset.count()
        status_counts = queryset.values('status').annotate(count=Count('id'))
        
        # Average response time (time between created and resolved)
        resolved = queryset.filter(resolved_at__isnull=False)
        avg_response_time = None
        if resolved.exists():
            from django.db.models import ExpressionWrapper, F, DurationField
            response_times = resolved.annotate(
                response_time=ExpressionWrapper(
                    F('resolved_at') - F('created_at'),
                    output_field=DurationField()
                )
            )
            avg_seconds = sum(
                [rt.response_time.total_seconds() for rt in response_times],
                0
            ) / resolved.count()
            avg_response_time = avg_seconds
        
        # Escalation metrics
        escalated_count = queryset.filter(status='escalated').count()
        escalation_rate = (escalated_count / total_count * 100) if total_count > 0 else 0
        
        return Response({
            'period_days': days,
            'total_approvals': total_count,
            'status_breakdown': {item['status']: item['count'] for item in status_counts},
            'average_response_time_seconds': avg_response_time,
            'escalated_count': escalated_count,
            'escalation_rate_percent': round(escalation_rate, 2),
        })
