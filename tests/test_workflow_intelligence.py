# tests/test_workflow_intelligence.py
# Tests for workflow intelligence features

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from workflow.models import (
    Workflow, WorkflowExecution, ActionCatalog, WorkflowSuggestion,
    WorkflowSimulation, WorkflowSLA, SLABreach, ProcessTemplate
)
from core.models import Company

User = get_user_model()


@pytest.fixture
def company(db):
    """Create test company"""
    return Company.objects.create(
        name='Test Company',
        domain='test.com',
        is_active=True
    )


@pytest.fixture
def user(db, company):
    """Create test user"""
    user = User.objects.create_user(
        email='test@test.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    user.active_company = company
    user.save()
    return user


@pytest.fixture
def workflow(db, company, user):
    """Create test workflow"""
    return Workflow.objects.create(
        company=company,
        name='Test Workflow',
        description='Test workflow for testing',
        workflow_type='approval',
        steps=[
            {'name': 'Step 1', 'action': 'validation'},
            {'name': 'Step 2', 'action': 'approval', 'approver': 'manager'},
            {'name': 'Step 3', 'action': 'notification'}
        ],
        owner=user
    )


@pytest.mark.django_db
class TestActionCatalog:
    """Test action catalog functionality"""
    
    def test_create_action_catalog(self, company):
        """Test creating an action catalog entry"""
        action = ActionCatalog.objects.create(
            company=company,
            name='Email Notification',
            description='Send email notification',
            action_type='notification',
            is_idempotent=True,
            latency_class='fast',
            side_effects=['email_sent'],
            input_schema={'type': 'object', 'properties': {'to': {'type': 'string'}}},
            output_schema={'type': 'object', 'properties': {'sent': {'type': 'boolean'}}}
        )
        
        assert action.name == 'Email Notification'
        assert action.is_idempotent is True
        assert action.latency_class == 'fast'
        assert 'email_sent' in action.side_effects
    
    def test_action_catalog_metadata(self, company):
        """Test action catalog metadata fields"""
        action = ActionCatalog.objects.create(
            company=company,
            name='Database Update',
            action_type='update',
            is_idempotent=False,
            latency_class='medium',
            side_effects=['db_write', 'cache_invalidation'],
            execution_count=100,
            avg_execution_time_ms=250,
            success_rate=0.98
        )
        
        assert action.is_idempotent is False
        assert len(action.side_effects) == 2
        assert action.avg_execution_time_ms == 250
        assert action.success_rate == 0.98


@pytest.mark.django_db
class TestWorkflowSuggestion:
    """Test workflow suggestion engine"""
    
    def test_create_workflow_suggestion(self, company):
        """Test creating a workflow suggestion"""
        suggestion = WorkflowSuggestion.objects.create(
            company=company,
            title='Auto-approve small discounts',
            description='Based on historical data, auto-approve discounts under 10%',
            source='historical',
            workflow_template={
                'workflow_type': 'approval',
                'trigger_conditions': {'discount': {'$lt': 10}},
                'steps': [{'action': 'auto_approve'}]
            },
            confidence_score=0.85,
            supporting_data={'sample_count': 150, 'approval_rate': 1.0},
            pattern_frequency=150
        )
        
        assert suggestion.title == 'Auto-approve small discounts'
        assert suggestion.source == 'historical'
        assert suggestion.confidence_score == 0.85
        assert suggestion.status == 'pending'
    
    def test_accept_workflow_suggestion(self, company, user):
        """Test accepting a workflow suggestion"""
        suggestion = WorkflowSuggestion.objects.create(
            company=company,
            title='Test Suggestion',
            description='Test',
            source='llm'
        )
        
        suggestion.status = 'accepted'
        suggestion.reviewed_by = user
        suggestion.reviewed_at = timezone.now()
        suggestion.review_notes = 'Looks good'
        suggestion.save()
        
        assert suggestion.status == 'accepted'
        assert suggestion.reviewed_by == user
        assert suggestion.review_notes == 'Looks good'
    
    def test_suggestion_ordering(self, company):
        """Test suggestions are ordered by confidence score"""
        WorkflowSuggestion.objects.create(
            company=company,
            title='Low confidence',
            description='Test',
            confidence_score=0.3
        )
        WorkflowSuggestion.objects.create(
            company=company,
            title='High confidence',
            description='Test',
            confidence_score=0.9
        )
        
        suggestions = list(WorkflowSuggestion.objects.all())
        assert suggestions[0].confidence_score == 0.9
        assert suggestions[1].confidence_score == 0.3


@pytest.mark.django_db
class TestWorkflowSimulation:
    """Test workflow simulation/dry-run"""
    
    def test_create_workflow_simulation(self, workflow, user):
        """Test creating a workflow simulation"""
        simulation = WorkflowSimulation.objects.create(
            company=workflow.company,
            workflow=workflow,
            input_data={'amount': 1000, 'discount': 15},
            status='running',
            created_by=user
        )
        
        assert simulation.workflow == workflow
        assert simulation.status == 'running'
        assert simulation.input_data['amount'] == 1000
    
    def test_simulation_execution_path(self, workflow, user):
        """Test simulation captures execution path"""
        simulation = WorkflowSimulation.objects.create(
            company=workflow.company,
            workflow=workflow,
            input_data={},
            status='completed',
            created_by=user,
            execution_path=[
                {'step': 0, 'action': 'validation', 'status': 'simulated'},
                {'step': 1, 'action': 'approval', 'status': 'simulated'},
                {'step': 2, 'action': 'notification', 'status': 'simulated'}
            ]
        )
        
        assert len(simulation.execution_path) == 3
        assert simulation.execution_path[0]['action'] == 'validation'
        assert simulation.execution_path[1]['action'] == 'approval'
    
    def test_simulation_branch_exploration(self, workflow, user):
        """Test simulation explores branches"""
        simulation = WorkflowSimulation.objects.create(
            company=workflow.company,
            workflow=workflow,
            input_data={},
            status='completed',
            created_by=user,
            branch_explorations=[
                {'from_step': 1, 'condition': 'amount > 1000', 'next_step': 3},
                {'from_step': 1, 'condition': 'amount <= 1000', 'next_step': 2}
            ]
        )
        
        assert len(simulation.branch_explorations) == 2
        assert 'condition' in simulation.branch_explorations[0]
    
    def test_simulation_approval_chain(self, workflow, user):
        """Test simulation captures approval chain"""
        simulation = WorkflowSimulation.objects.create(
            company=workflow.company,
            workflow=workflow,
            input_data={},
            status='completed',
            created_by=user,
            approval_chain=[
                {'step': 1, 'approver': 'manager', 'conditions': {}},
                {'step': 3, 'approver': 'director', 'conditions': {'amount': {'$gt': 5000}}}
            ]
        )
        
        assert len(simulation.approval_chain) == 2
        assert simulation.approval_chain[0]['approver'] == 'manager'
    
    def test_simulation_validation_errors(self, workflow, user):
        """Test simulation captures validation errors"""
        simulation = WorkflowSimulation.objects.create(
            company=workflow.company,
            workflow=workflow,
            input_data={},
            status='completed',
            created_by=user,
            validation_errors=['Step 2: Missing approver configuration']
        )
        
        assert len(simulation.validation_errors) == 1
        assert 'Missing approver' in simulation.validation_errors[0]


@pytest.mark.django_db
class TestWorkflowSLA:
    """Test SLA tracking and breach alerting"""
    
    def test_create_workflow_sla(self, workflow):
        """Test creating a workflow SLA"""
        sla = WorkflowSLA.objects.create(
            company=workflow.company,
            workflow=workflow,
            name='Response Time SLA',
            description='Must complete within 5 minutes',
            target_duration_seconds=300,
            warning_threshold_seconds=240,
            critical_threshold_seconds=300,
            slo_window_hours=24,
            slo_target_percentage=99.0
        )
        
        assert sla.name == 'Response Time SLA'
        assert sla.target_duration_seconds == 300
        assert sla.slo_target_percentage == 99.0
        assert sla.current_slo_percentage == 100.0
    
    def test_sla_breach_creation(self, workflow, user):
        """Test creating an SLA breach"""
        sla = WorkflowSLA.objects.create(
            company=workflow.company,
            workflow=workflow,
            name='Test SLA',
            target_duration_seconds=300,
            warning_threshold_seconds=240,
            critical_threshold_seconds=300
        )
        
        execution = WorkflowExecution.objects.create(
            company=workflow.company,
            workflow=workflow,
            triggered_by=user,
            status='completed'
        )
        
        breach = SLABreach.objects.create(
            company=workflow.company,
            sla=sla,
            workflow_execution=execution,
            severity='critical',
            actual_duration_seconds=450,
            target_duration_seconds=300,
            breach_margin_seconds=150
        )
        
        assert breach.severity == 'critical'
        assert breach.actual_duration_seconds == 450
        assert breach.breach_margin_seconds == 150
        assert breach.acknowledged is False
    
    def test_sla_breach_acknowledgment(self, workflow, user):
        """Test acknowledging an SLA breach"""
        sla = WorkflowSLA.objects.create(
            company=workflow.company,
            workflow=workflow,
            name='Test SLA',
            target_duration_seconds=300,
            warning_threshold_seconds=240,
            critical_threshold_seconds=300
        )
        
        execution = WorkflowExecution.objects.create(
            company=workflow.company,
            workflow=workflow,
            triggered_by=user,
            status='completed'
        )
        
        breach = SLABreach.objects.create(
            company=workflow.company,
            sla=sla,
            workflow_execution=execution,
            severity='warning',
            actual_duration_seconds=360,
            target_duration_seconds=300,
            breach_margin_seconds=60
        )
        
        breach.acknowledged = True
        breach.acknowledged_by = user
        breach.acknowledged_at = timezone.now()
        breach.resolution_notes = 'Expected delay due to high load'
        breach.save()
        
        assert breach.acknowledged is True
        assert breach.acknowledged_by == user
        assert breach.resolution_notes != ''
    
    def test_sla_breach_alerting(self, workflow, user):
        """Test SLA breach alert sending"""
        sla = WorkflowSLA.objects.create(
            company=workflow.company,
            workflow=workflow,
            name='Test SLA',
            target_duration_seconds=300,
            warning_threshold_seconds=240,
            critical_threshold_seconds=300
        )
        
        execution = WorkflowExecution.objects.create(
            company=workflow.company,
            workflow=workflow,
            triggered_by=user,
            status='completed'
        )
        
        breach = SLABreach.objects.create(
            company=workflow.company,
            sla=sla,
            workflow_execution=execution,
            severity='critical',
            actual_duration_seconds=450,
            target_duration_seconds=300,
            breach_margin_seconds=150,
            alert_sent=True,
            alert_sent_at=timezone.now(),
            alert_recipients=['admin@test.com', 'ops@test.com']
        )
        
        assert breach.alert_sent is True
        assert len(breach.alert_recipients) == 2


@pytest.mark.django_db
class TestBlueprintTemplates:
    """Test blueprint template import/export"""
    
    def test_template_versioning(self, company, user):
        """Test template version tracking"""
        template = ProcessTemplate.objects.create(
            company=company,
            name='Approval Template',
            description='Standard approval process',
            template_type='approval',
            version='1.2.3',
            owner=user
        )
        
        assert template.version == '1.2.3'
    
    def test_template_graph_spec(self, company, user):
        """Test template graph specification"""
        template = ProcessTemplate.objects.create(
            company=company,
            name='Complex Workflow',
            description='Multi-branch workflow',
            template_type='custom',
            version='2.0.0',
            graph_spec={
                'nodes': [
                    {'id': 'start', 'type': 'trigger'},
                    {'id': 'step1', 'type': 'action'},
                    {'id': 'step2', 'type': 'decision'},
                    {'id': 'end', 'type': 'terminator'}
                ],
                'edges': [
                    {'from': 'start', 'to': 'step1'},
                    {'from': 'step1', 'to': 'step2'},
                    {'from': 'step2', 'to': 'end', 'condition': 'approved'},
                ]
            },
            owner=user
        )
        
        assert 'nodes' in template.graph_spec
        assert 'edges' in template.graph_spec
        assert len(template.graph_spec['nodes']) == 4
    
    def test_template_export_format(self, company, user):
        """Test template export includes all necessary fields"""
        template = ProcessTemplate.objects.create(
            company=company,
            name='Export Test',
            description='Template for export testing',
            template_type='approval',
            version='1.0.0',
            process_steps=[{'step': 1, 'action': 'validate'}],
            variables=[{'name': 'amount', 'type': 'number'}],
            settings={'timeout': 300},
            graph_spec={'nodes': [], 'edges': []},
            owner=user
        )
        
        # Simulate export
        export_data = {
            'name': template.name,
            'description': template.description,
            'version': template.version,
            'template_type': template.template_type,
            'process_steps': template.process_steps,
            'variables': template.variables,
            'settings': template.settings,
            'graph_spec': template.graph_spec,
        }
        
        assert 'version' in export_data
        assert 'graph_spec' in export_data
        assert export_data['name'] == 'Export Test'


@pytest.mark.django_db
class TestIntegration:
    """Integration tests for workflow intelligence"""
    
    def test_multi_approval_workflow(self, company, user):
        """Test multi-level approval workflow simulation"""
        workflow = Workflow.objects.create(
            company=company,
            name='Multi-Approval Workflow',
            workflow_type='approval',
            steps=[
                {'name': 'Manager Approval', 'action': 'approval', 'approver': 'manager'},
                {'name': 'Director Approval', 'action': 'approval', 'approver': 'director', 
                 'conditions': {'amount': {'$gt': 10000}}},
                {'name': 'CFO Approval', 'action': 'approval', 'approver': 'cfo',
                 'conditions': {'amount': {'$gt': 50000}}}
            ],
            owner=user
        )
        
        # Simulate with different amounts
        simulation_small = WorkflowSimulation.objects.create(
            company=company,
            workflow=workflow,
            input_data={'amount': 5000},
            status='completed',
            created_by=user,
            approval_chain=[
                {'step': 0, 'approver': 'manager'}
            ]
        )
        
        simulation_large = WorkflowSimulation.objects.create(
            company=company,
            workflow=workflow,
            input_data={'amount': 75000},
            status='completed',
            created_by=user,
            approval_chain=[
                {'step': 0, 'approver': 'manager'},
                {'step': 1, 'approver': 'director'},
                {'step': 2, 'approver': 'cfo'}
            ]
        )
        
        assert len(simulation_small.approval_chain) == 1
        assert len(simulation_large.approval_chain) == 3
    
    def test_branching_workflow_simulation(self, company, user):
        """Test branching workflow with multiple paths"""
        workflow = Workflow.objects.create(
            company=company,
            name='Branching Workflow',
            workflow_type='custom',
            steps=[
                {'name': 'Validate', 'action': 'validation'},
                {'name': 'Branch', 'action': 'decision', 'branches': [
                    {'condition': 'priority == "high"', 'next_step': 2},
                    {'condition': 'priority == "low"', 'next_step': 3}
                ]},
                {'name': 'High Priority Path', 'action': 'escalation'},
                {'name': 'Normal Path', 'action': 'notification'}
            ],
            owner=user
        )
        
        simulation = WorkflowSimulation.objects.create(
            company=company,
            workflow=workflow,
            input_data={'priority': 'high'},
            status='completed',
            created_by=user,
            branch_explorations=[
                {'from_step': 1, 'condition': 'priority == "high"', 'next_step': 2},
                {'from_step': 1, 'condition': 'priority == "low"', 'next_step': 3}
            ]
        )
        
        assert len(simulation.branch_explorations) == 2
    
    def test_sla_breach_with_metrics(self, workflow, user):
        """Test SLA tracking with breach metrics"""
        sla = WorkflowSLA.objects.create(
            company=workflow.company,
            workflow=workflow,
            name='Performance SLA',
            target_duration_seconds=600,
            warning_threshold_seconds=480,
            critical_threshold_seconds=600,
            slo_window_hours=24,
            slo_target_percentage=95.0,
            total_executions=100,
            breached_executions=3
        )
        
        # Calculate SLO percentage
        sla.current_slo_percentage = ((sla.total_executions - sla.breached_executions) / 
                                      sla.total_executions) * 100
        sla.save()
        
        assert sla.current_slo_percentage == 97.0
        assert sla.current_slo_percentage > sla.slo_target_percentage
