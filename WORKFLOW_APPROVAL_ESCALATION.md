# Workflow Approval Escalation Feature

## Overview

The Workflow Approval Escalation feature provides a timed approval mechanism with automatic escalation after timeout to escalation roles. It includes comprehensive API endpoints, Celery background tasks for automatic escalation, and metrics tracking.

## Features

1. **WorkflowApproval Model**: Stores approval requests with expiration and escalation configuration
2. **API Endpoints**: REST API for creating, approving, denying approvals and retrieving metrics
3. **Automatic Escalation**: Celery task that runs periodically to escalate expired approvals
4. **Metrics**: Track approval rates, response times, and escalation statistics

## Database Model

### WorkflowApproval

| Field | Type | Description |
|-------|------|-------------|
| workflow_run_id | UUID | Reference to workflow execution |
| action_run_id | UUID | Reference to specific action run |
| status | CharField | Current status: pending, approved, denied, escalated, expired |
| approver_role | CharField | Role required to approve this action |
| escalate_role | CharField | Role to escalate to after timeout |
| expires_at | DateTimeField | When this approval expires and should escalate |
| resolved_at | DateTimeField | When the approval was resolved (approved/denied) |
| actor_id | UUIDField | User who approved/denied the request |
| metadata | JSONField | Additional approval metadata (comments, reasons, etc.) |
| company | ForeignKey | Company isolation |
| created_at | DateTimeField | When the approval was created |
| updated_at | DateTimeField | When the approval was last updated |

## API Endpoints

### Base URL
```
/api/v1/workflows/approvals/
```

### 1. List Approvals
```http
GET /api/v1/workflows/approvals/
```

**Query Parameters:**
- `workflow_run_id`: Filter by workflow run ID
- `action_run_id`: Filter by action run ID
- `status`: Filter by status (pending, approved, denied, escalated, expired)
- `approver_role`: Filter by approver role

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "workflow_run_id": "uuid",
      "action_run_id": "uuid",
      "status": "pending",
      "approver_role": "manager",
      "escalate_role": "director",
      "expires_at": "2024-01-01T12:00:00Z",
      "resolved_at": null,
      "actor_id": null,
      "metadata": {},
      "company": 1,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

### 2. Create Approval
```http
POST /api/v1/workflows/approvals/
```

**Request Body:**
```json
{
  "workflow_run_id": "uuid",
  "action_run_id": "uuid",
  "approver_role": "manager",
  "escalate_role": "director",
  "expires_at": "2024-01-01T12:00:00Z",
  "metadata": {
    "priority": "high",
    "description": "Approval for expense over $10,000"
  }
}
```

**Response:** (201 Created)
```json
{
  "id": 1,
  "workflow_run_id": "uuid",
  "action_run_id": "uuid",
  "status": "pending",
  "approver_role": "manager",
  "escalate_role": "director",
  "expires_at": "2024-01-01T12:00:00Z",
  "resolved_at": null,
  "actor_id": null,
  "metadata": {
    "priority": "high",
    "description": "Approval for expense over $10,000"
  },
  "company": 1,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

### 3. Approve Request
```http
POST /api/v1/workflows/approvals/{id}/approve/
```

**Request Body:**
```json
{
  "comments": "Approved - meets all requirements"
}
```

**Response:**
```json
{
  "message": "Approval request approved successfully",
  "approval": {
    "id": 1,
    "status": "approved",
    "resolved_at": "2024-01-01T11:30:00Z",
    "actor_id": "user-uuid",
    "metadata": {
      "approved_at": "2024-01-01T11:30:00Z",
      "approved_by": "user@example.com",
      "comments": "Approved - meets all requirements"
    }
  }
}
```

### 4. Deny Request
```http
POST /api/v1/workflows/approvals/{id}/deny/
```

**Request Body:**
```json
{
  "reason": "Insufficient budget",
  "comments": "Please resubmit with lower amount"
}
```

**Response:**
```json
{
  "message": "Approval request denied successfully",
  "approval": {
    "id": 1,
    "status": "denied",
    "resolved_at": "2024-01-01T11:30:00Z",
    "actor_id": "user-uuid",
    "metadata": {
      "denied_at": "2024-01-01T11:30:00Z",
      "denied_by": "user@example.com",
      "reason": "Insufficient budget",
      "comments": "Please resubmit with lower amount"
    }
  }
}
```

### 5. Get Metrics
```http
GET /api/v1/workflows/approvals/metrics/?days=30
```

**Query Parameters:**
- `days`: Number of days to include in metrics (default: 30)

**Response:**
```json
{
  "period_days": 30,
  "total_approvals": 150,
  "status_breakdown": {
    "pending": 20,
    "approved": 100,
    "denied": 15,
    "escalated": 10,
    "expired": 5
  },
  "average_response_time_seconds": 3600,
  "escalated_count": 10,
  "escalation_rate_percent": 6.67
}
```

## Celery Tasks

### 1. escalate_expired_approvals

**Task Name:** `workflow.escalate_expired_approvals`

**Schedule:** Runs every 5 minutes (configurable in `config/celery.py`)

**Description:** 
Finds all pending approvals that have expired (expires_at <= current time) and updates their status to 'escalated'. The task also updates the metadata with escalation information.

**Configuration:**
```python
# config/celery.py
app.conf.beat_schedule = {
    'escalate-expired-approvals-every-5-minutes': {
        'task': 'workflow.escalate_expired_approvals',
        'schedule': crontab(minute='*/5'),  # Run every 5 minutes
    },
}
```

**Manual Execution:**
```python
from workflow.tasks import escalate_expired_approvals
result = escalate_expired_approvals()
```

**Return Value:**
```json
{
  "task": "escalate_expired_approvals",
  "executed_at": "2024-01-01T12:00:00Z",
  "escalated_count": 5,
  "escalation_details": [
    {
      "approval_id": "uuid",
      "workflow_run_id": "uuid",
      "action_run_id": "uuid",
      "escalated_to": "director"
    }
  ]
}
```

### 2. cleanup_old_approvals (Optional)

**Task Name:** `workflow.cleanup_old_approvals`

**Schedule:** Runs weekly (Sunday at midnight)

**Description:** 
Cleans up old resolved approvals (approved, denied, expired) older than 90 days by default.

**Configuration:**
```python
# config/celery.py
app.conf.beat_schedule = {
    'cleanup-old-approvals-weekly': {
        'task': 'workflow.cleanup_old_approvals',
        'schedule': crontab(hour=0, minute=0, day_of_week=0),
        'kwargs': {'days': 90},
    },
}
```

## Usage Example: approval_ext Action

### Workflow Configuration with approval_ext

When defining a workflow with an approval action that uses escalation:

```python
workflow = {
    "name": "Expense Approval Workflow",
    "steps": [
        {
            "action": "approval_ext",
            "config": {
                "approver_role": "manager",
                "escalate_role": "director",
                "timeout_hours": 24,  # Escalate after 24 hours
                "metadata": {
                    "type": "expense_approval",
                    "threshold": 10000
                }
            }
        }
    ]
}
```

### Creating an Approval from Workflow Execution

```python
from workflow.models import WorkflowApproval
from django.utils import timezone
from datetime import timedelta

# When a workflow reaches an approval_ext action
approval = WorkflowApproval.objects.create(
    company=company,
    workflow_run_id=workflow_execution.id,
    action_run_id=action_run.id,
    status='pending',
    approver_role='manager',
    escalate_role='director',
    expires_at=timezone.now() + timedelta(hours=24),
    metadata={
        'expense_amount': 15000,
        'requester': 'john@example.com',
        'description': 'Conference travel expenses'
    }
)
```

## Running Celery

### Start Celery Worker
```bash
celery -A config worker -l info
```

### Start Celery Beat (Scheduler)
```bash
celery -A config beat -l info
```

### Combined Worker and Beat
```bash
celery -A config worker --beat -l info
```

## Testing

Run the test suite:
```bash
pytest tests/test_workflow_approval.py -v
```

Test coverage includes:
- Model creation and validation
- API endpoint functionality (list, create, approve, deny, metrics)
- Celery task execution
- Escalation logic
- Edge cases (already resolved approvals, expired approvals, etc.)

## Database Migration

Apply the migration to create the WorkflowApproval table:
```bash
python manage.py migrate workflow
```

## Monitoring

### View Recent Escalations
```python
from workflow.models import WorkflowApproval

escalated = WorkflowApproval.objects.filter(
    status='escalated'
).order_by('-updated_at')[:10]
```

### Check Pending Approvals
```python
from workflow.models import WorkflowApproval
from django.utils import timezone

pending = WorkflowApproval.objects.filter(
    status='pending',
    expires_at__gt=timezone.now()
).count()
```

### Approval Response Time Report
```python
from workflow.models import WorkflowApproval
from django.db.models import Avg, F, ExpressionWrapper, DurationField

avg_time = WorkflowApproval.objects.filter(
    resolved_at__isnull=False
).annotate(
    response_time=ExpressionWrapper(
        F('resolved_at') - F('created_at'),
        output_field=DurationField()
    )
).aggregate(Avg('response_time'))
```

## Configuration

### Celery Configuration (config/settings.py)
```python
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
```

### Escalation Schedule
Adjust the escalation check frequency in `config/celery.py`:
```python
# Check every 5 minutes (default)
'schedule': crontab(minute='*/5')

# Or check every minute for faster escalation
'schedule': crontab(minute='*')

# Or check every 15 minutes
'schedule': crontab(minute='*/15')
```

## Security Considerations

1. **Authentication**: All API endpoints require authentication
2. **Authorization**: Consider adding role-based access control to ensure only users with appropriate roles can approve/deny
3. **Audit Trail**: All approval actions are logged with actor_id and timestamps in metadata
4. **Company Isolation**: Approvals are isolated by company (multi-tenancy support)

## Future Enhancements

1. **Notifications**: Send email/SMS notifications when approvals are created, escalated, or resolved
2. **Approval Chains**: Support multi-level approval workflows
3. **Conditional Escalation**: Escalate based on custom conditions (not just timeout)
4. **Approval History**: Track complete approval history with all actions
5. **SLA Tracking**: Monitor and report on approval SLA compliance
