# Quick Start Guide - Workflow Approval Escalation

## Prerequisites

- Django project is set up and running
- PostgreSQL database configured
- Redis server running (for Celery)
- Python 3.8+ with required packages installed

## 5-Minute Setup

### Step 1: Apply Database Migration (30 seconds)

```bash
cd /home/runner/work/Claude-CRM/Claude-CRM
python manage.py migrate workflow
```

**Expected Output:**
```
Running migrations:
  Applying workflow.0001_initial... OK
```

### Step 2: Start Celery Worker (30 seconds)

Open a new terminal and run:

```bash
# Option 1: Worker + Beat combined (recommended for development)
celery -A config worker --beat -l info

# Option 2: Separate worker and beat (recommended for production)
# Terminal 1:
celery -A config worker -l info

# Terminal 2:
celery -A config beat -l info
```

**Expected Output:**
```
 -------------- celery@hostname v5.3.4
---- **** ----- 
--- * ***  * -- Linux-5.4.0 2024-01-01 12:00:00
-- * - **** --- 
- ** ---------- [config]
- ** ---------- .> app:         claude_crm:0x7f...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 4
-- ******* ---- .> task events: OFF
--- ***** ----- 

[tasks]
  . workflow.cleanup_old_approvals
  . workflow.escalate_expired_approvals

[2024-01-01 12:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2024-01-01 12:00:00,001: INFO/MainProcess] mingle: searching for neighbors
[2024-01-01 12:00:00,002: INFO/MainProcess] mingle: all alone
[2024-01-01 12:00:00,003: INFO/MainProcess] celery@hostname ready.
```

### Step 3: Test API Endpoints (2 minutes)

#### Create an Approval

```bash
curl -X POST http://localhost:8000/api/v1/workflows/approvals/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "company": 1,
    "workflow_run_id": "550e8400-e29b-41d4-a716-446655440000",
    "action_run_id": "660e8400-e29b-41d4-a716-446655440000",
    "approver_role": "manager",
    "escalate_role": "director",
    "expires_at": "2024-12-31T23:59:59Z",
    "metadata": {
      "description": "Test approval",
      "amount": 1000
    }
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "workflow_run_id": "550e8400-e29b-41d4-a716-446655440000",
  "action_run_id": "660e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "approver_role": "manager",
  "escalate_role": "director",
  "expires_at": "2024-12-31T23:59:59Z",
  "resolved_at": null,
  "actor_id": null,
  "metadata": {
    "description": "Test approval",
    "amount": 1000
  },
  "company": 1,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### List Approvals

```bash
curl -X GET http://localhost:8000/api/v1/workflows/approvals/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Approve an Approval

```bash
curl -X POST http://localhost:8000/api/v1/workflows/approvals/1/approve/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "comments": "Approved - looks good!"
  }'
```

**Expected Response:**
```json
{
  "message": "Approval request approved successfully",
  "approval": {
    "id": 1,
    "status": "approved",
    "resolved_at": "2024-01-01T12:05:00Z",
    "actor_id": "user-uuid",
    "metadata": {
      "description": "Test approval",
      "amount": 1000,
      "approved_at": "2024-01-01T12:05:00Z",
      "approved_by": "user@example.com",
      "comments": "Approved - looks good!"
    }
  }
}
```

### Step 4: View Metrics (30 seconds)

```bash
curl -X GET http://localhost:8000/api/v1/workflows/approvals/metrics/?days=30 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "period_days": 30,
  "total_approvals": 1,
  "status_breakdown": {
    "approved": 1
  },
  "average_response_time_seconds": 300,
  "escalated_count": 0,
  "escalation_rate_percent": 0
}
```

### Step 5: Access Django Admin (1 minute)

1. Navigate to: `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Go to "Workflow" → "Workflow Approvals"
4. View, edit, or create approvals

## Testing Escalation

### Create an Expired Approval

To test the escalation functionality, create an approval that's already expired:

```bash
curl -X POST http://localhost:8000/api/v1/workflows/approvals/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "company": 1,
    "workflow_run_id": "770e8400-e29b-41d4-a716-446655440000",
    "action_run_id": "880e8400-e29b-41d4-a716-446655440000",
    "approver_role": "manager",
    "escalate_role": "director",
    "expires_at": "2024-01-01T00:00:00Z",
    "metadata": {
      "description": "Expired approval for testing"
    }
  }'
```

### Manually Trigger Escalation Task

```bash
# Using Django shell
python manage.py shell

# In the shell:
from workflow.tasks import escalate_expired_approvals
result = escalate_expired_approvals()
print(result)
```

**Expected Output:**
```python
{
    'task': 'escalate_expired_approvals',
    'executed_at': '2024-01-01T12:10:00Z',
    'escalated_count': 1,
    'escalation_details': [
        {
            'approval_id': '2',
            'workflow_run_id': '770e8400-e29b-41d4-a716-446655440000',
            'action_run_id': '880e8400-e29b-41d4-a716-446655440000',
            'escalated_to': 'director'
        }
    ]
}
```

### Verify Escalation

```bash
curl -X GET http://localhost:8000/api/v1/workflows/approvals/2/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "id": 2,
  "status": "escalated",
  "metadata": {
    "description": "Expired approval for testing",
    "escalated_at": "2024-01-01T12:10:00Z",
    "escalation_reason": "timeout",
    "original_approver_role": "manager",
    "escalated_to_role": "director"
  }
}
```

## Troubleshooting

### Issue: Celery not connecting to Redis

**Error:**
```
Error: Connection to redis://localhost:6379/0 failed
```

**Solution:**
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running, start Redis:
sudo systemctl start redis
# OR
redis-server
```

### Issue: Migration fails

**Error:**
```
django.db.utils.ProgrammingError: relation "workflow_approval" already exists
```

**Solution:**
```bash
# Check migration status
python manage.py showmigrations workflow

# If needed, fake the migration
python manage.py migrate workflow --fake
```

### Issue: API returns 403 Forbidden

**Solution:**
Ensure you're passing a valid authentication token in the Authorization header.

### Issue: Celery task not running

**Check:**
```bash
# Verify beat schedule
celery -A config inspect scheduled

# Check worker status
celery -A config inspect active
```

## Production Deployment Checklist

- [ ] Set up production Redis server
- [ ] Configure Celery with production settings
- [ ] Set up Celery worker as a systemd service
- [ ] Set up Celery beat as a systemd service
- [ ] Configure logging for Celery tasks
- [ ] Set up monitoring for escalation task
- [ ] Configure alerts for failed escalations
- [ ] Set up database backups
- [ ] Review and adjust escalation schedule
- [ ] Test escalation in staging environment

## Next Steps

1. **Integrate with Workflow Execution**
   - Update workflow engine to create approvals for `approval_ext` actions
   - Handle approval responses in workflow continuation logic

2. **Add Notifications**
   - Email notifications when approval is created
   - Email notifications when approval is escalated
   - SMS notifications for urgent approvals

3. **Build Frontend UI**
   - Approval dashboard
   - Approve/deny buttons
   - Metrics visualization

4. **Add Role-Based Access Control**
   - Restrict approve/deny to users with appropriate roles
   - Implement permission checks

5. **Enhance Metrics**
   - Add more detailed reports
   - Create approval SLA tracking
   - Build escalation trend analysis

## Support

For more detailed information, see:
- [WORKFLOW_APPROVAL_ESCALATION.md](WORKFLOW_APPROVAL_ESCALATION.md) - Complete user guide
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details
- [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) - System architecture

## Success Criteria

You've successfully set up the Workflow Approval Escalation system when:

✅ Migration applied without errors  
✅ Celery worker running and showing tasks  
✅ API endpoints responding with 200 status  
✅ Can create and approve/deny approvals  
✅ Escalation task runs and escalates expired approvals  
✅ Metrics endpoint returns statistics  

Congratulations! Your workflow approval escalation system is now operational.
