# Workflow Approval Escalation - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     WORKFLOW APPROVAL ESCALATION SYSTEM                 │
└─────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│  CLIENT LAYER                                                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  HTTP Requests (JSON)                                                     │
│  ├── POST /api/v1/workflows/approvals/          (Create)                 │
│  ├── GET  /api/v1/workflows/approvals/          (List)                   │
│  ├── GET  /api/v1/workflows/approvals/{id}/     (Retrieve)               │
│  ├── POST /api/v1/workflows/approvals/{id}/approve/                      │
│  ├── POST /api/v1/workflows/approvals/{id}/deny/                         │
│  └── GET  /api/v1/workflows/approvals/metrics/                           │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────┐
│  API LAYER (Django REST Framework)                                       │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  WorkflowApprovalViewSet (workflow/views.py)                             │
│  ├── queryset: WorkflowApproval.objects.all()                            │
│  ├── serializer_class: WorkflowApprovalSerializer                        │
│  ├── filter_backends: [DjangoFilterBackend, OrderingFilter]              │
│  ├── Actions:                                                             │
│  │   ├── list()           → List all approvals with filtering            │
│  │   ├── create()         → Create new approval                          │
│  │   ├── retrieve()       → Get specific approval                        │
│  │   ├── approve()        → Approve & update status                      │
│  │   ├── deny()           → Deny & update status                         │
│  │   └── metrics()        → Calculate and return metrics                 │
│  └── Filtering: workflow_run_id, action_run_id, status, approver_role    │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────┐
│  SERIALIZATION LAYER                                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  WorkflowApprovalSerializer (workflow/serializers.py)                    │
│  ├── Validates: expires_at must be in future                             │
│  ├── Read-only: id, created_at, updated_at, resolved_at                  │
│  └── Serializes: All WorkflowApproval fields to/from JSON                │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────┐
│  MODEL LAYER (Django ORM)                                                 │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  WorkflowApproval (workflow/models.py)                                   │
│  ├── Fields:                                                              │
│  │   ├── workflow_run_id (UUID)                                          │
│  │   ├── action_run_id (UUID)                                            │
│  │   ├── status (CharField: pending/approved/denied/escalated/expired)   │
│  │   ├── approver_role (CharField)                                       │
│  │   ├── escalate_role (CharField)                                       │
│  │   ├── expires_at (DateTimeField)                                      │
│  │   ├── resolved_at (DateTimeField, nullable)                           │
│  │   ├── actor_id (UUIDField, nullable)                                  │
│  │   ├── metadata (JSONField)                                            │
│  │   └── company (ForeignKey to Company - multi-tenancy)                 │
│  ├── Indexes:                                                             │
│  │   ├── workflow_run_id                                                 │
│  │   ├── action_run_id                                                   │
│  │   ├── status                                                           │
│  │   └── expires_at                                                       │
│  └── Meta:                                                                │
│      ├── db_table: 'workflow_approval'                                   │
│      └── ordering: ['-created_at']                                       │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────┐
│  DATABASE LAYER                                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  PostgreSQL Database                                                      │
│  └── workflow_approval table                                             │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────┐
│  BACKGROUND TASK LAYER (Celery)                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Celery App (config/celery.py)                                           │
│  ├── Broker: Redis (default)                                             │
│  ├── Result Backend: Redis (default)                                     │
│  └── Beat Schedule:                                                       │
│      ├── escalate-expired-approvals-every-5-minutes                      │
│      │   ├── Task: workflow.escalate_expired_approvals                   │
│      │   ├── Schedule: crontab(minute='*/5')                             │
│      │   └── Action: Finds pending approvals past expires_at             │
│      │               Updates status to 'escalated'                        │
│      │               Adds escalation metadata                             │
│      └── cleanup-old-approvals-weekly                                    │
│          ├── Task: workflow.cleanup_old_approvals                        │
│          ├── Schedule: crontab(hour=0, minute=0, day_of_week=0)          │
│          └── Action: Deletes resolved approvals older than 90 days       │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────┐
│  TASK LAYER                                                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  escalate_expired_approvals() (workflow/tasks.py)                        │
│  ├── Query: WorkflowApproval.objects.filter(                             │
│  │             status='pending',                                          │
│  │             expires_at__lte=timezone.now()                            │
│  │         )                                                              │
│  ├── For each expired approval:                                          │
│  │   ├── approval.status = 'escalated'                                   │
│  │   ├── approval.metadata['escalated_at'] = now                         │
│  │   ├── approval.metadata['escalation_reason'] = 'timeout'              │
│  │   └── approval.save()                                                 │
│  └── Return: {escalated_count, escalation_details}                       │
│                                                                           │
│  cleanup_old_approvals(days=90) (workflow/tasks.py)                      │
│  ├── Query: WorkflowApproval.objects.filter(                             │
│  │             resolved_at__lt=cutoff_date,                               │
│  │             status__in=['approved', 'denied', 'expired']              │
│  │         )                                                              │
│  ├── Delete old approvals                                                │
│  └── Return: {deleted_count, cutoff_days}                                │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────┐
│  ADMIN INTERFACE LAYER (Django Admin)                                    │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  WorkflowApprovalAdmin (workflow/admin.py)                               │
│  ├── List Display:                                                        │
│  │   ├── id, workflow_run_id, action_run_id, status                      │
│  │   ├── approver_role, escalate_role                                    │
│  │   ├── expires_at, resolved_at, created_at                             │
│  ├── Filters: status, approver_role, company, created_at                 │
│  ├── Search: workflow_run_id, action_run_id, approver_role               │
│  └── Fieldsets:                                                           │
│      ├── Workflow References                                             │
│      ├── Approval Configuration                                          │
│      ├── Status                                                           │
│      ├── Metadata                                                         │
│      └── Timestamps                                                       │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────┐
│  DATA FLOW EXAMPLE                                                        │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  1. Workflow Execution triggers approval_ext action                       │
│     └─> POST /api/v1/workflows/approvals/                                │
│         {workflow_run_id, action_run_id, approver_role,                  │
│          escalate_role, expires_at}                                       │
│                                                                           │
│  2. WorkflowApproval record created with status='pending'                │
│     └─> Stored in database with company isolation                        │
│                                                                           │
│  3. User approves/denies via API                                         │
│     └─> POST /api/v1/workflows/approvals/{id}/approve/                   │
│         - Updates status to 'approved'                                    │
│         - Sets resolved_at to current time                                │
│         - Sets actor_id to requesting user                                │
│         - Adds approval metadata                                          │
│                                                                           │
│  4. OR Celery task escalates if expired                                  │
│     └─> escalate_expired_approvals task runs every 5 minutes             │
│         - Finds approvals with expires_at <= now                          │
│         - Updates status to 'escalated'                                   │
│         - Adds escalation metadata                                        │
│                                                                           │
│  5. Metrics endpoint tracks performance                                  │
│     └─> GET /api/v1/workflows/approvals/metrics/                         │
│         - Total approvals count                                           │
│         - Status breakdown                                                │
│         - Average response time                                           │
│         - Escalation rate                                                 │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────────────┐
│  STATUS STATE MACHINE                                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│                          ┌──────────┐                                    │
│                          │ PENDING  │ ← Initial State                    │
│                          └────┬─────┘                                    │
│                               │                                           │
│                  ┌────────────┼────────────┐                             │
│                  │            │            │                             │
│              User Action  Timeout    User Action                         │
│              (Approve)    (Task)     (Deny)                              │
│                  │            │            │                             │
│                  ↓            ↓            ↓                             │
│            ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│            │ APPROVED │ │ESCALATED │ │  DENIED  │                       │
│            └──────────┘ └────┬─────┘ └──────────┘                       │
│                Final State    │        Final State                       │
│                              │                                           │
│                         User Action                                      │
│                      (Approve/Deny)                                      │
│                              │                                           │
│                   ┌──────────┴──────────┐                                │
│                   │                     │                                │
│                   ↓                     ↓                                │
│             ┌──────────┐          ┌──────────┐                           │
│             │ APPROVED │          │  DENIED  │                           │
│             └──────────┘          └──────────┘                           │
│              Final State           Final State                           │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

## Key Components Summary

| Component | Purpose | Location |
|-----------|---------|----------|
| **WorkflowApproval Model** | Stores approval records | `workflow/models.py` |
| **WorkflowApprovalSerializer** | Serializes/validates data | `workflow/serializers.py` |
| **WorkflowApprovalViewSet** | Handles HTTP requests | `workflow/views.py` |
| **URL Routing** | Maps endpoints to views | `workflow/urls.py` |
| **Celery App** | Background task scheduler | `config/celery.py` |
| **Escalation Task** | Auto-escalates expired approvals | `workflow/tasks.py` |
| **Admin Interface** | Management interface | `workflow/admin.py` |
| **Migration** | Database schema | `workflow/migrations/0001_initial.py` |
| **Tests** | Comprehensive test suite | `tests/test_workflow_approval.py` |

## Integration Points

1. **Workflow Execution** → Creates WorkflowApproval when encountering `approval_ext` action
2. **API Client** → Approves/denies via REST endpoints
3. **Celery Beat** → Runs escalation task every 5 minutes
4. **Metrics Dashboard** → Queries metrics endpoint for reporting
5. **Django Admin** → Manual approval management and monitoring
