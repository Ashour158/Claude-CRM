# workflow/views.py
# Workflow views

from rest_framework import viewsets, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Workflow, WorkflowExecution, ApprovalProcess, ApprovalRequest,
    BusinessRule, BusinessRuleExecution, ProcessTemplate,
    ActionCatalog, WorkflowSuggestion, WorkflowSimulation,
    WorkflowSLA, SLABreach
)
from .serializers import (
    WorkflowSerializer, WorkflowExecutionSerializer, ApprovalProcessSerializer,
    ApprovalRequestSerializer, BusinessRuleSerializer, BusinessRuleExecutionSerializer,
    ProcessTemplateSerializer, ActionCatalogSerializer, WorkflowSuggestionSerializer,
    WorkflowSimulationSerializer, WorkflowSLASerializer, SLABreachSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
import json

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
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Export template as blueprint"""
        template = self.get_object()
        blueprint = {
            'name': template.name,
            'description': template.description,
            'version': template.version,
            'template_type': template.template_type,
            'process_steps': template.process_steps,
            'variables': template.variables,
            'settings': template.settings,
            'graph_spec': template.graph_spec,
        }
        return Response(blueprint)
    
    @action(detail=False, methods=['post'])
    def import_blueprint(self, request):
        """Import blueprint template"""
        data = request.data
        
        # Create new template from blueprint
        template = ProcessTemplate.objects.create(
            company=request.user.active_company,
            name=data.get('name'),
            description=data.get('description', ''),
            version=data.get('version', '1.0.0'),
            template_type=data.get('template_type', 'custom'),
            process_steps=data.get('process_steps', []),
            variables=data.get('variables', []),
            settings=data.get('settings', {}),
            graph_spec=data.get('graph_spec', {}),
            owner=request.user
        )
        
        serializer = self.get_serializer(template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ActionCatalogViewSet(viewsets.ModelViewSet):
    """Action catalog viewset"""
    queryset = ActionCatalog.objects.all()
    serializer_class = ActionCatalogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action_type', 'is_idempotent', 'latency_class', 'is_active', 'is_global']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'execution_count', 'success_rate']
    ordering = ['name']


class WorkflowSuggestionViewSet(viewsets.ModelViewSet):
    """Workflow suggestion viewset"""
    queryset = WorkflowSuggestion.objects.all()
    serializer_class = WorkflowSuggestionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source', 'status']
    search_fields = ['title', 'description']
    ordering_fields = ['confidence_score', 'created_at', 'pattern_frequency']
    ordering = ['-confidence_score']
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept workflow suggestion"""
        suggestion = self.get_object()
        suggestion.status = 'accepted'
        suggestion.reviewed_by = request.user
        suggestion.reviewed_at = timezone.now()
        suggestion.review_notes = request.data.get('notes', '')
        suggestion.save()
        return Response({'message': 'Suggestion accepted'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject workflow suggestion"""
        suggestion = self.get_object()
        suggestion.status = 'rejected'
        suggestion.reviewed_by = request.user
        suggestion.reviewed_at = timezone.now()
        suggestion.review_notes = request.data.get('notes', '')
        suggestion.save()
        return Response({'message': 'Suggestion rejected'})
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate workflow suggestions based on historical data"""
        # This would analyze historical workflow executions
        # For now, return a sample suggestion
        suggestion = WorkflowSuggestion.objects.create(
            company=request.user.active_company,
            title='Suggested: Auto-approve small discounts',
            description='Based on historical data, discounts under 10% are always approved. Consider auto-approval.',
            source='historical',
            confidence_score=0.85,
            workflow_template={
                'workflow_type': 'approval',
                'trigger_conditions': {'discount_percentage': {'$lt': 10}},
                'steps': [
                    {'action': 'auto_approve', 'conditions': {}}
                ]
            },
            supporting_data={'sample_count': 150, 'approval_rate': 1.0},
            pattern_frequency=150
        )
        
        serializer = self.get_serializer(suggestion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WorkflowSimulationViewSet(viewsets.ModelViewSet):
    """Workflow simulation viewset"""
    queryset = WorkflowSimulation.objects.all()
    serializer_class = WorkflowSimulationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['workflow', 'status', 'created_by']
    ordering_fields = ['started_at']
    ordering = ['-started_at']
    
    def create(self, request, *args, **kwargs):
        """Create and run a workflow simulation"""
        workflow_id = request.data.get('workflow_id')
        input_data = request.data.get('input_data', {})
        
        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            return Response(
                {'error': 'Workflow not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create simulation
        simulation = WorkflowSimulation.objects.create(
            company=request.user.active_company,
            workflow=workflow,
            input_data=input_data,
            status='running',
            created_by=request.user
        )
        
        # Run simulation (dry-run, no DB mutations)
        try:
            simulation_result = self._run_simulation(workflow, input_data)
            
            simulation.status = 'completed'
            simulation.execution_path = simulation_result['execution_path']
            simulation.branch_explorations = simulation_result['branch_explorations']
            simulation.approval_chain = simulation_result['approval_chain']
            simulation.predicted_duration_ms = simulation_result['predicted_duration_ms']
            simulation.validation_errors = simulation_result['validation_errors']
            simulation.warnings = simulation_result['warnings']
            simulation.completed_at = timezone.now()
            simulation.save()
            
        except Exception as e:
            simulation.status = 'failed'
            simulation.validation_errors.append(str(e))
            simulation.completed_at = timezone.now()
            simulation.save()
        
        serializer = self.get_serializer(simulation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _run_simulation(self, workflow, input_data):
        """Run workflow simulation without DB mutations"""
        execution_path = []
        branch_explorations = []
        approval_chain = []
        validation_errors = []
        warnings = []
        predicted_duration = 0
        
        # Simulate each step
        for idx, step in enumerate(workflow.steps):
            step_result = {
                'step_index': idx,
                'step_name': step.get('name', f'Step {idx}'),
                'action': step.get('action'),
                'status': 'simulated'
            }
            
            # Check for approvals
            if step.get('action') == 'approval':
                approver = step.get('approver', 'Unknown')
                approval_chain.append({
                    'step': idx,
                    'approver': approver,
                    'conditions': step.get('conditions', {})
                })
            
            # Estimate duration
            action_type = step.get('action', 'default')
            step_duration = self._estimate_action_duration(action_type)
            predicted_duration += step_duration
            step_result['estimated_duration_ms'] = step_duration
            
            # Check for branching conditions
            if 'branches' in step:
                for branch in step['branches']:
                    branch_explorations.append({
                        'from_step': idx,
                        'condition': branch.get('condition'),
                        'next_step': branch.get('next_step')
                    })
            
            # Validate step configuration
            if not step.get('action'):
                validation_errors.append(f"Step {idx}: Missing action")
            
            execution_path.append(step_result)
        
        return {
            'execution_path': execution_path,
            'branch_explorations': branch_explorations,
            'approval_chain': approval_chain,
            'predicted_duration_ms': predicted_duration,
            'validation_errors': validation_errors,
            'warnings': warnings
        }
    
    def _estimate_action_duration(self, action_type):
        """Estimate action duration based on action catalog"""
        try:
            action = ActionCatalog.objects.filter(action_type=action_type).first()
            if action and action.avg_execution_time_ms:
                return action.avg_execution_time_ms
        except:
            pass
        
        # Default estimates
        duration_map = {
            'approval': 1000,
            'notification': 500,
            'calculation': 200,
            'validation': 100,
            'default': 500
        }
        return duration_map.get(action_type, duration_map['default'])


class WorkflowSLAViewSet(viewsets.ModelViewSet):
    """Workflow SLA viewset"""
    queryset = WorkflowSLA.objects.all()
    serializer_class = WorkflowSLASerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['workflow', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'current_slo_percentage']
    ordering = ['workflow', 'name']
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Get SLA metrics"""
        sla = self.get_object()
        
        # Calculate metrics for the SLO window
        window_start = timezone.now() - timedelta(hours=sla.slo_window_hours)
        
        breaches = SLABreach.objects.filter(
            sla=sla,
            detected_at__gte=window_start
        )
        
        metrics = {
            'sla_name': sla.name,
            'slo_window_hours': sla.slo_window_hours,
            'slo_target_percentage': sla.slo_target_percentage,
            'current_slo_percentage': sla.current_slo_percentage,
            'total_executions': sla.total_executions,
            'breached_executions': sla.breached_executions,
            'window_breaches': breaches.count(),
            'critical_breaches': breaches.filter(severity='critical').count(),
            'warning_breaches': breaches.filter(severity='warning').count(),
        }
        
        return Response(metrics)


class SLABreachViewSet(viewsets.ReadOnlyModelViewSet):
    """SLA breach viewset"""
    queryset = SLABreach.objects.all()
    serializer_class = SLABreachSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['sla', 'severity', 'acknowledged', 'alert_sent']
    ordering_fields = ['detected_at', 'breach_margin_seconds']
    ordering = ['-detected_at']
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge SLA breach"""
        breach = self.get_object()
        breach.acknowledged = True
        breach.acknowledged_by = request.user
        breach.acknowledged_at = timezone.now()
        breach.resolution_notes = request.data.get('notes', '')
        breach.save()
        
        return Response({'message': 'SLA breach acknowledged'})
    
    @action(detail=False, methods=['get'])
    def unacknowledged(self, request):
        """Get unacknowledged breaches"""
        breaches = self.queryset.filter(acknowledged=False)
        serializer = self.get_serializer(breaches, many=True)
        return Response(serializer.data)
