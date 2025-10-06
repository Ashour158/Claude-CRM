# Workflow Engine Design

## Overview
The Workflow Engine MVP enables automated business processes through configurable triggers, conditions, and actions. This document describes the workflow system architecture, DSL syntax, trigger matrix, and action schema.

## Architecture

### Components
1. **Workflow** - Container for automation logic
2. **WorkflowTrigger** - Defines when workflow executes
3. **WorkflowAction** - Defines what workflow does
4. **WorkflowRun** - Tracks execution instance
5. **WorkflowActionRun** - Tracks individual action execution

### Data Flow
```
Event → Trigger Matching → Condition Evaluation → Action Execution → Run Logging
```

## Trigger Matrix

### Supported Event Types
| Event Type | Description | Available Context |
|------------|-------------|-------------------|
| `timeline.event` | Timeline/activity events | event_type, entity_type, entity_id |
| `lead.created` | New lead created | lead_id, lead_data |
| `lead.converted` | Lead converted to opportunity | lead_id, deal_id |
| `deal.stage_changed` | Deal moved to new stage | deal_id, old_stage, new_stage |
| `deal.won` | Deal marked as won | deal_id, amount |
| `deal.lost` | Deal marked as lost | deal_id, reason |
| `contact.created` | New contact created | contact_id, contact_data |
| `account.created` | New account created | account_id, account_data |
| `custom` | Custom event type | Varies by implementation |

## Condition DSL

### Simple Condition
```json
{
  "field": "status",
  "operator": "eq",
  "value": "qualified"
}
```

### Logical AND
```json
{
  "and": [
    {"field": "amount", "operator": "gte", "value": 1000},
    {"field": "stage", "operator": "eq", "value": "proposal"}
  ]
}
```

### Logical OR
```json
{
  "or": [
    {"field": "priority", "operator": "eq", "value": "high"},
    {"field": "amount", "operator": "gte", "value": 50000}
  ]
}
```

### Logical NOT
```json
{
  "not": {
    "field": "status",
    "operator": "eq",
    "value": "unqualified"
  }
}
```

### Nested Conditions
```json
{
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
```

### Supported Operators
- `eq` - Equals
- `ne` - Not equals
- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than
- `lte` - Less than or equal
- `in` - Value in list
- `contains` - String contains
- `startswith` - String starts with
- `endswith` - String ends with

### Nested Field Access
Use dot notation for nested fields:
```json
{
  "field": "lead.company_name",
  "operator": "contains",
  "value": "Tech"
}
```

## Action Schema

### Send Email
```json
{
  "to": "{{lead.email}}",
  "subject": "Welcome to our platform",
  "template": "welcome_email",
  "variables": {
    "first_name": "{{lead.first_name}}"
  }
}
```

### Add Note
```json
{
  "entity_type": "lead",
  "entity_id": "{{lead.id}}",
  "note": "Lead automatically qualified based on score",
  "visibility": "internal"
}
```

### Update Field
```json
{
  "entity_type": "lead",
  "entity_id": "{{lead.id}}",
  "field": "status",
  "value": "contacted"
}
```

### Enqueue Export
```json
{
  "export_type": "csv",
  "entity_type": "lead",
  "filters": {
    "status": "qualified",
    "created_at__gte": "{{today-30}}"
  },
  "email_to": "{{user.email}}"
}
```

### Create Task
```json
{
  "title": "Follow up with {{lead.company_name}}",
  "description": "Lead showed high interest",
  "assignee": "{{lead.owner.email}}",
  "due_date": "{{today+2}}",
  "priority": "high"
}
```

### Send Notification
```json
{
  "recipient": "{{lead.owner.email}}",
  "message": "New qualified lead: {{lead.company_name}}",
  "notification_type": "in_app",
  "link": "/leads/{{lead.id}}"
}
```

### Call Webhook
```json
{
  "url": "https://api.example.com/webhooks/lead",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer {{api_key}}",
    "Content-Type": "application/json"
  },
  "body": {
    "lead_id": "{{lead.id}}",
    "event": "lead.qualified"
  }
}
```

## Execution Model

### Sequential Execution
Actions execute in order defined by `ordering` field.

### Rollback Safety
- Actions with `allow_failure=True` don't stop workflow on error
- Failed actions are logged with error details
- Partial execution state preserved in `WorkflowRun`

### Idempotency
- Each workflow run has unique ID
- Actions should be designed for idempotency
- Duplicate trigger detection recommended for production

## Performance Considerations

### Trigger Evaluation
- Triggers cached per company
- Priority-based ordering for efficiency
- Condition evaluation short-circuits on first failure

### Action Execution
- Async execution for long-running actions (future enhancement)
- Batch operations for multiple records
- Rate limiting per workflow

### Monitoring
- All runs logged with duration metrics
- Failed runs tracked separately
- Execution history retained per retention policy

## Security

### Permissions
- Workflow creation: Admin/Manager only
- Workflow execution: System + authorized users
- Action capabilities limited by user role

### Data Access
- Actions respect field-level permissions
- Masked fields remain masked in action context
- Audit log for all workflow executions

## Usage Examples

### Example 1: Auto-qualify High-Value Leads
```python
# Trigger
event_type = "lead.created"
conditions = {
    "and": [
        {"field": "annual_revenue", "operator": "gte", "value": 1000000},
        {"field": "budget", "operator": "gte", "value": 50000}
    ]
}

# Actions
1. Update lead status to "qualified"
2. Assign to senior sales rep
3. Send notification to sales manager
4. Create follow-up task
```

### Example 2: Deal Stage Change Notification
```python
# Trigger
event_type = "deal.stage_changed"
conditions = {
    "field": "new_stage",
    "operator": "eq",
    "value": "negotiation"
}

# Actions
1. Send email to deal owner
2. Create approval request if > $100k
3. Add note to deal timeline
4. Update forecast
```

### Example 3: Lead Nurture Automation
```python
# Trigger
event_type = "lead.created"
conditions = {
    "and": [
        {"field": "status", "operator": "eq", "value": "new"},
        {"field": "lead_score", "operator": "lt", "value": 60}
    ]
}

# Actions
1. Add to nurture email campaign
2. Schedule follow-up task in 7 days
3. Tag as "nurture_track"
```

## Testing Strategy

### Unit Tests
- Condition DSL parsing
- Operator evaluation
- Nested condition logic
- Field access with dot notation

### Integration Tests
- Trigger matching
- Condition evaluation with real data
- Action execution and rollback
- Run logging and status tracking

### Performance Tests
- High-volume trigger evaluation
- Concurrent workflow execution
- Action execution latency
- Database query optimization

## Future Enhancements

### Phase 5+
- Visual workflow designer
- Async action execution with Celery
- Workflow versioning and rollback
- A/B testing for workflows
- AI-suggested workflow optimizations
- Cross-workflow dependencies
- Sub-workflow support
- External system integrations (Zapier-style)

## API Endpoints

### Create Workflow
```
POST /api/v1/workflows/
```

### List Workflows
```
GET /api/v1/workflows/
```

### Get Workflow Details
```
GET /api/v1/workflows/{id}/
```

### Update Workflow
```
PUT /api/v1/workflows/{id}/
```

### Delete Workflow
```
DELETE /api/v1/workflows/{id}/
```

### Execute Workflow Manually
```
POST /api/v1/workflows/{id}/execute/
```

### List Workflow Runs
```
GET /api/v1/workflows/{id}/runs/
```

### Get Run Details
```
GET /api/v1/workflow-runs/{id}/
```

## Conclusion
The Workflow Engine provides a powerful, flexible automation foundation that can be extended to support increasingly complex business processes while maintaining performance and security.
