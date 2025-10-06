# tests/test_workflow_engine.py
# Tests for workflow engine Phase 4+

import pytest
from datetime import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import Company
from workflow.models import (
    Workflow, WorkflowTrigger, WorkflowAction,
    WorkflowRun, WorkflowActionRun
)
from workflow.services import (
    WorkflowConditionEvaluator,
    WorkflowActionExecutor,
    WorkflowExecutionService
)

User = get_user_model()

@pytest.fixture
def company(db):
    return Company.objects.create(
        name="Test Company",
        code="TEST001"
    )

@pytest.fixture
def user(db, company):
    user = User.objects.create_user(
        email="test@example.com",
        password="testpass123"
    )
    return user

@pytest.fixture
def workflow(db, company, user):
    return Workflow.objects.create(
        company=company,
        name="Test Workflow",
        workflow_type="automation",
        status="active",
        is_active=True,
        owner=user
    )

@pytest.fixture
def workflow_trigger(db, workflow):
    return WorkflowTrigger.objects.create(
        workflow=workflow,
        company=workflow.company,
        event_type="lead.created",
        conditions={"field": "status", "operator": "eq", "value": "qualified"},
        is_active=True,
        priority=100
    )

@pytest.fixture
def workflow_action(db, workflow):
    return WorkflowAction.objects.create(
        workflow=workflow,
        company=workflow.company,
        action_type="add_note",
        payload={"note": "Lead qualified automatically"},
        ordering=1,
        is_active=True
    )

class TestWorkflowConditionEvaluator:
    """Test DSL condition evaluation"""
    
    def test_simple_eq_condition_true(self):
        """Test simple equality condition that is true"""
        condition = {"field": "status", "operator": "eq", "value": "qualified"}
        context = {"status": "qualified"}
        
        result = WorkflowConditionEvaluator.evaluate(condition, context)
        assert result is True
    
    def test_simple_eq_condition_false(self):
        """Test simple equality condition that is false"""
        condition = {"field": "status", "operator": "eq", "value": "qualified"}
        context = {"status": "new"}
        
        result = WorkflowConditionEvaluator.evaluate(condition, context)
        assert result is False
    
    def test_gte_operator(self):
        """Test greater than or equal operator"""
        condition = {"field": "amount", "operator": "gte", "value": 1000}
        
        # True case
        context = {"amount": 1500}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is True
        
        # Equal case
        context = {"amount": 1000}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is True
        
        # False case
        context = {"amount": 500}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is False
    
    def test_in_operator(self):
        """Test 'in' operator"""
        condition = {"field": "source", "operator": "in", "value": ["website", "referral"]}
        
        # True case
        context = {"source": "website"}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is True
        
        # False case
        context = {"source": "cold_call"}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is False
    
    def test_contains_operator(self):
        """Test 'contains' operator"""
        condition = {"field": "company_name", "operator": "contains", "value": "Tech"}
        
        # True case
        context = {"company_name": "TechCorp Inc"}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is True
        
        # False case
        context = {"company_name": "Acme Corp"}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is False
    
    def test_and_condition(self):
        """Test logical AND"""
        condition = {
            "and": [
                {"field": "status", "operator": "eq", "value": "qualified"},
                {"field": "amount", "operator": "gte", "value": 1000}
            ]
        }
        
        # Both true
        context = {"status": "qualified", "amount": 1500}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is True
        
        # First false
        context = {"status": "new", "amount": 1500}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is False
        
        # Second false
        context = {"status": "qualified", "amount": 500}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is False
    
    def test_or_condition(self):
        """Test logical OR"""
        condition = {
            "or": [
                {"field": "priority", "operator": "eq", "value": "high"},
                {"field": "amount", "operator": "gte", "value": 50000}
            ]
        }
        
        # First true
        context = {"priority": "high", "amount": 1000}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is True
        
        # Second true
        context = {"priority": "low", "amount": 60000}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is True
        
        # Both false
        context = {"priority": "low", "amount": 1000}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is False
    
    def test_not_condition(self):
        """Test logical NOT"""
        condition = {
            "not": {"field": "status", "operator": "eq", "value": "unqualified"}
        }
        
        # Should be true (status is not unqualified)
        context = {"status": "qualified"}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is True
        
        # Should be false (status is unqualified)
        context = {"status": "unqualified"}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is False
    
    def test_nested_conditions(self):
        """Test nested AND/OR conditions"""
        condition = {
            "and": [
                {"field": "status", "operator": "eq", "value": "qualified"},
                {
                    "or": [
                        {"field": "source", "operator": "eq", "value": "referral"},
                        {"field": "lead_score", "operator": "gte", "value": 80}
                    ]
                }
            ]
        }
        
        # Status qualified + referral source
        context = {"status": "qualified", "source": "referral", "lead_score": 50}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is True
        
        # Status qualified + high score
        context = {"status": "qualified", "source": "website", "lead_score": 85}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is True
        
        # Status not qualified
        context = {"status": "new", "source": "referral", "lead_score": 50}
        assert WorkflowConditionEvaluator.evaluate(condition, context) is False
    
    def test_nested_field_access(self):
        """Test dot notation for nested fields"""
        condition = {"field": "lead.status", "operator": "eq", "value": "qualified"}
        context = {"lead": {"status": "qualified", "name": "John"}}
        
        result = WorkflowConditionEvaluator.evaluate(condition, context)
        assert result is True
    
    def test_empty_conditions_returns_true(self):
        """Test that empty conditions return True"""
        result = WorkflowConditionEvaluator.evaluate({}, {"any": "data"})
        assert result is True

class TestWorkflowActionExecutor:
    """Test workflow action execution"""
    
    def test_send_email_action(self):
        """Test send email action execution"""
        action = WorkflowAction(
            action_type="send_email",
            payload={"to": "test@example.com", "subject": "Test"}
        )
        context = {"lead_id": "123"}
        
        result = WorkflowActionExecutor.execute_action(action, context)
        
        assert result['success'] is True
        assert result['result']['action'] == 'send_email'
        assert result['result']['status'] == 'queued'
    
    def test_add_note_action(self):
        """Test add note action execution"""
        action = WorkflowAction(
            action_type="add_note",
            payload={"note": "Test note", "entity_type": "lead"}
        )
        context = {"entity_id": "lead-123"}
        
        result = WorkflowActionExecutor.execute_action(action, context)
        
        assert result['success'] is True
        assert result['result']['action'] == 'add_note'
        assert result['result']['note'] == "Test note"
    
    def test_update_field_action(self):
        """Test update field action execution"""
        action = WorkflowAction(
            action_type="update_field",
            payload={"field": "status", "value": "contacted", "entity_type": "lead"}
        )
        context = {"entity_id": "lead-123"}
        
        result = WorkflowActionExecutor.execute_action(action, context)
        
        assert result['success'] is True
        assert result['result']['field'] == "status"
        assert result['result']['value'] == "contacted"
    
    def test_unknown_action_type(self):
        """Test unknown action type returns error"""
        action = WorkflowAction(
            action_type="invalid_action",
            payload={}
        )
        context = {}
        
        result = WorkflowActionExecutor.execute_action(action, context)
        
        assert result['success'] is False
        assert 'error' in result

@pytest.mark.django_db
class TestWorkflowExecutionService:
    """Test workflow execution service"""
    
    def test_trigger_matching_workflow(self, workflow, workflow_trigger, workflow_action, company):
        """Test that matching trigger executes workflow"""
        event_data = {"status": "qualified", "lead_id": "123"}
        
        runs = WorkflowExecutionService.trigger_workflow(
            event_type="lead.created",
            event_data=event_data,
            company=company
        )
        
        assert len(runs) == 1
        assert runs[0].workflow == workflow
        assert runs[0].status == 'completed'
    
    def test_non_matching_conditions_skip_workflow(self, workflow, workflow_trigger, company):
        """Test that non-matching conditions skip workflow"""
        event_data = {"status": "new", "lead_id": "123"}  # Not "qualified"
        
        runs = WorkflowExecutionService.trigger_workflow(
            event_type="lead.created",
            event_data=event_data,
            company=company
        )
        
        assert len(runs) == 0
    
    def test_workflow_run_creates_action_runs(self, workflow, workflow_trigger, workflow_action, user):
        """Test that workflow execution creates action run records"""
        run = WorkflowExecutionService.execute_workflow(
            workflow=workflow,
            trigger=workflow_trigger,
            trigger_data={"status": "qualified"},
            user=user
        )
        
        assert run.status == 'completed'
        assert run.action_runs.count() == 1
        
        action_run = run.action_runs.first()
        assert action_run.action == workflow_action
        assert action_run.status == 'completed'
    
    def test_failed_action_with_allow_failure_continues(self, workflow, company):
        """Test that failed actions with allow_failure=True don't stop workflow"""
        # Create two actions: one that will fail (allow_failure=True), one that succeeds
        action1 = WorkflowAction.objects.create(
            workflow=workflow,
            company=company,
            action_type="invalid_type",  # Will fail
            payload={},
            ordering=1,
            allow_failure=True
        )
        action2 = WorkflowAction.objects.create(
            workflow=workflow,
            company=company,
            action_type="add_note",
            payload={"note": "Success"},
            ordering=2,
            is_active=True
        )
        
        run = WorkflowExecutionService.execute_workflow(workflow=workflow)
        
        # Workflow should complete despite first action failing
        assert run.status == 'completed'
        assert run.action_runs.count() == 2
    
    def test_workflow_updates_execution_count(self, workflow):
        """Test that workflow execution increments count"""
        initial_count = workflow.execution_count
        
        WorkflowExecutionService.execute_workflow(workflow=workflow)
        workflow.refresh_from_db()
        
        assert workflow.execution_count == initial_count + 1
        assert workflow.last_executed is not None
    
    def test_workflow_run_tracks_duration(self, workflow):
        """Test that workflow run tracks execution duration"""
        run = WorkflowExecutionService.execute_workflow(workflow=workflow)
        
        assert run.duration_ms is not None
        assert run.duration_ms >= 0
        assert run.started_at is not None
        assert run.completed_at is not None

@pytest.mark.django_db
class TestWorkflowIntegration:
    """Integration tests for complete workflow scenarios"""
    
    def test_lead_qualification_workflow(self, company, user):
        """Test complete lead qualification workflow"""
        # Create workflow
        workflow = Workflow.objects.create(
            company=company,
            name="Auto-Qualify High Value Leads",
            workflow_type="automation",
            status="active",
            is_active=True,
            owner=user
        )
        
        # Create trigger
        trigger = WorkflowTrigger.objects.create(
            workflow=workflow,
            company=company,
            event_type="lead.created",
            conditions={
                "and": [
                    {"field": "annual_revenue", "operator": "gte", "value": 1000000},
                    {"field": "budget", "operator": "gte", "value": 50000}
                ]
            },
            is_active=True
        )
        
        # Create actions
        WorkflowAction.objects.create(
            workflow=workflow,
            company=company,
            action_type="update_field",
            payload={"field": "status", "value": "qualified"},
            ordering=1
        )
        WorkflowAction.objects.create(
            workflow=workflow,
            company=company,
            action_type="send_notification",
            payload={"recipient": "sales@example.com", "message": "New qualified lead"},
            ordering=2
        )
        
        # Trigger workflow with qualifying data
        event_data = {
            "annual_revenue": 2000000,
            "budget": 75000,
            "lead_id": "lead-123"
        }
        
        runs = WorkflowExecutionService.trigger_workflow(
            event_type="lead.created",
            event_data=event_data,
            company=company,
            user=user
        )
        
        # Verify execution
        assert len(runs) == 1
        run = runs[0]
        assert run.status == 'completed'
        assert run.success is True
        assert run.action_runs.count() == 2
        
        # Verify actions executed in order
        action_runs = list(run.action_runs.all())
        assert action_runs[0].action.action_type == "update_field"
        assert action_runs[1].action.action_type == "send_notification"
