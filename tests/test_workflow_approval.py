# tests/test_workflow_approval.py
# Tests for WorkflowApproval feature

import pytest
from django.utils import timezone
from datetime import timedelta
from workflow.models import WorkflowApproval
from workflow.tasks import escalate_expired_approvals
from rest_framework.test import APIClient
from core.models import Company, User
import uuid


@pytest.fixture
def company(db):
    """Create a test company"""
    return Company.objects.create(
        name='Test Company',
        code='TEST001'
    )


@pytest.fixture
def user(db):
    """Create a test user"""
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def workflow_approval(db, company):
    """Create a test workflow approval"""
    return WorkflowApproval.objects.create(
        company=company,
        workflow_run_id=uuid.uuid4(),
        action_run_id=uuid.uuid4(),
        status='pending',
        approver_role='manager',
        escalate_role='director',
        expires_at=timezone.now() + timedelta(hours=1),
        metadata={}
    )


@pytest.mark.django_db
class TestWorkflowApprovalModel:
    """Test WorkflowApproval model"""
    
    def test_create_workflow_approval(self, company):
        """Test creating a workflow approval"""
        approval = WorkflowApproval.objects.create(
            company=company,
            workflow_run_id=uuid.uuid4(),
            action_run_id=uuid.uuid4(),
            status='pending',
            approver_role='manager',
            escalate_role='director',
            expires_at=timezone.now() + timedelta(hours=2),
            metadata={'test': 'data'}
        )
        
        assert approval.id is not None
        assert approval.status == 'pending'
        assert approval.approver_role == 'manager'
        assert approval.escalate_role == 'director'
        assert approval.resolved_at is None
        assert approval.actor_id is None
    
    def test_approval_string_representation(self, workflow_approval):
        """Test string representation of approval"""
        str_repr = str(workflow_approval)
        assert 'Approval' in str_repr
        assert 'pending' in str_repr
        assert str(workflow_approval.workflow_run_id) in str_repr
    
    def test_approval_metadata(self, workflow_approval):
        """Test approval metadata field"""
        workflow_approval.metadata = {
            'comments': 'Test comment',
            'priority': 'high'
        }
        workflow_approval.save()
        
        refreshed = WorkflowApproval.objects.get(id=workflow_approval.id)
        assert refreshed.metadata['comments'] == 'Test comment'
        assert refreshed.metadata['priority'] == 'high'


@pytest.mark.django_db
class TestWorkflowApprovalAPI:
    """Test WorkflowApproval API endpoints"""
    
    def test_list_approvals(self, workflow_approval, user):
        """Test listing workflow approvals"""
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/v1/workflows/approvals/')
        assert response.status_code == 200
        assert len(response.data['results']) > 0
    
    def test_create_approval(self, company, user):
        """Test creating a workflow approval via API"""
        client = APIClient()
        client.force_authenticate(user=user)
        
        data = {
            'company': company.id,
            'workflow_run_id': str(uuid.uuid4()),
            'action_run_id': str(uuid.uuid4()),
            'status': 'pending',
            'approver_role': 'manager',
            'escalate_role': 'director',
            'expires_at': (timezone.now() + timedelta(hours=1)).isoformat(),
            'metadata': {}
        }
        
        response = client.post('/api/v1/workflows/approvals/', data, format='json')
        assert response.status_code == 201
        assert response.data['status'] == 'pending'
        assert response.data['approver_role'] == 'manager'
    
    def test_approve_approval(self, workflow_approval, user):
        """Test approving a workflow approval"""
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.post(
            f'/api/v1/workflows/approvals/{workflow_approval.id}/approve/',
            {'comments': 'Approved by test user'}
        )
        
        assert response.status_code == 200
        assert 'approved successfully' in response.data['message'].lower()
        
        # Refresh from database
        workflow_approval.refresh_from_db()
        assert workflow_approval.status == 'approved'
        assert workflow_approval.resolved_at is not None
        assert workflow_approval.actor_id == user.id
    
    def test_deny_approval(self, workflow_approval, user):
        """Test denying a workflow approval"""
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.post(
            f'/api/v1/workflows/approvals/{workflow_approval.id}/deny/',
            {
                'reason': 'Invalid request',
                'comments': 'Denied by test user'
            }
        )
        
        assert response.status_code == 200
        assert 'denied successfully' in response.data['message'].lower()
        
        # Refresh from database
        workflow_approval.refresh_from_db()
        assert workflow_approval.status == 'denied'
        assert workflow_approval.resolved_at is not None
        assert workflow_approval.actor_id == user.id
    
    def test_cannot_approve_already_resolved(self, workflow_approval, user):
        """Test that resolved approvals cannot be approved again"""
        workflow_approval.status = 'approved'
        workflow_approval.resolved_at = timezone.now()
        workflow_approval.save()
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.post(
            f'/api/v1/workflows/approvals/{workflow_approval.id}/approve/'
        )
        
        assert response.status_code == 400
        assert 'already' in response.data['error'].lower()
    
    def test_get_approval_metrics(self, workflow_approval, user):
        """Test getting approval metrics"""
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/v1/workflows/approvals/metrics/')
        
        assert response.status_code == 200
        assert 'total_approvals' in response.data
        assert 'status_breakdown' in response.data
        assert 'escalation_rate_percent' in response.data


@pytest.mark.django_db
class TestEscalationTask:
    """Test escalation Celery task"""
    
    def test_escalate_expired_approvals(self, company):
        """Test escalating expired approvals"""
        # Create an expired approval
        expired_approval = WorkflowApproval.objects.create(
            company=company,
            workflow_run_id=uuid.uuid4(),
            action_run_id=uuid.uuid4(),
            status='pending',
            approver_role='manager',
            escalate_role='director',
            expires_at=timezone.now() - timedelta(hours=1),  # Expired
            metadata={}
        )
        
        # Create a non-expired approval
        active_approval = WorkflowApproval.objects.create(
            company=company,
            workflow_run_id=uuid.uuid4(),
            action_run_id=uuid.uuid4(),
            status='pending',
            approver_role='manager',
            escalate_role='director',
            expires_at=timezone.now() + timedelta(hours=1),  # Not expired
            metadata={}
        )
        
        # Run the escalation task
        result = escalate_expired_approvals()
        
        assert result['escalated_count'] == 1
        assert len(result['escalation_details']) == 1
        
        # Check that the expired approval was escalated
        expired_approval.refresh_from_db()
        assert expired_approval.status == 'escalated'
        assert 'escalated_at' in expired_approval.metadata
        assert expired_approval.metadata['escalation_reason'] == 'timeout'
        
        # Check that the active approval was not escalated
        active_approval.refresh_from_db()
        assert active_approval.status == 'pending'
    
    def test_escalate_no_expired_approvals(self, company):
        """Test escalation when no approvals are expired"""
        # Create a non-expired approval
        WorkflowApproval.objects.create(
            company=company,
            workflow_run_id=uuid.uuid4(),
            action_run_id=uuid.uuid4(),
            status='pending',
            approver_role='manager',
            escalate_role='director',
            expires_at=timezone.now() + timedelta(hours=1),
            metadata={}
        )
        
        # Run the escalation task
        result = escalate_expired_approvals()
        
        assert result['escalated_count'] == 0
        assert len(result['escalation_details']) == 0
