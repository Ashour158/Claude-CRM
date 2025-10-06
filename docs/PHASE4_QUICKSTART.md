# Phase 4+ Enterprise Enhancements - Quick Start Guide

This guide helps you get started with the Phase 4+ enterprise enhancements added to the Claude CRM system.

## What's New in Phase 4+

### 🔄 Workflow Automation Engine
Automate business processes with flexible, event-driven workflows.

**Key Features:**
- Event-based triggers (lead.created, deal.stage_changed, etc.)
- Powerful condition DSL with nested logic
- Sequential action execution
- Comprehensive execution logging

**Quick Example:**
```python
from workflow.services import WorkflowExecutionService

# Trigger a workflow
runs = WorkflowExecutionService.trigger_workflow(
    event_type="lead.created",
    event_data={"status": "qualified", "amount": 50000},
    company=company,
    user=request.user
)
```

[→ Full Documentation](docs/WORKFLOW_ENGINE_DESIGN.md)

---

### 🔐 Field-Level Permissions & Masking
Control data access at the field level with GDPR-compliant masking.

**Key Features:**
- 4 permission modes: view, mask, hidden, edit
- 5 masking strategies: hash, partial, redact, encrypt, tokenize
- Automatic serializer integration
- Complete audit trail

**Quick Example:**
```python
from core.permissions_service import FieldPermissionService

# Filter data based on role permissions
filtered_data = FieldPermissionService.filter_fields_for_role(
    data=lead_data,
    role=user_role,
    object_type='lead',
    apply_masking=True
)
```

[→ Full Documentation](docs/FIELD_LEVEL_PERMISSIONS.md)

---

### 📊 Lead Scoring v2
Multi-factor lead scoring with transparent explanations.

**Key Features:**
- 6 scoring components (status, activity, age, completeness, engagement, custom)
- Customizable weights per company
- Hot/Warm/Cool/Cold classification
- Detailed score explanations

**Quick Example:**
```python
from crm.lead_scoring_service import LeadScoringV2Service

# Calculate lead score
score_data = LeadScoringV2Service.calculate_lead_score(lead)

# Returns:
# {
#   "total_score": 78,
#   "quality": "WARM",
#   "recommendation": "Schedule follow-up within 24 hours",
#   "components": [...],
#   "explanation": "..."
# }
```

[→ Full Documentation](docs/LEAD_SCORING_V2_DESIGN.md)

---

### 📈 Observability Stack
Structured logging, metrics, and tracing for production monitoring.

**Key Features:**
- JSON structured logging with correlation IDs
- Prometheus-compatible metrics
- OpenTelemetry-style tracing
- Request latency tracking

**Quick Example:**
```python
from core.observability import PrometheusMetrics, TracingInstrumentation

# Track workflow execution
PrometheusMetrics.increment_counter(
    'workflow_runs_total',
    {'workflow': 'Lead Qualification', 'status': 'success'}
)

# Trace an operation
with TracingInstrumentation.create_span('search.query', {'index': 'leads'}) as span:
    results = search_service.search(...)
```

[→ Full Documentation](docs/OBSERVABILITY_STACK.md)

---

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Initial Data

#### Create Roles and Permissions
```python
from core.permissions_models import Role, RoleFieldPermission

# Create sales rep role
sales_role = Role.objects.create(
    company=company,
    name="sales_rep",
    description="Sales Representative"
)

# Set email as masked for sales reps
RoleFieldPermission.objects.create(
    role=sales_role,
    company=company,
    object_type="lead",
    field_name="email",
    mode="mask"
)
```

#### Create a Workflow
```python
from workflow.models import Workflow, WorkflowTrigger, WorkflowAction

# Create workflow
workflow = Workflow.objects.create(
    company=company,
    name="Auto-Qualify High Value Leads",
    workflow_type="automation",
    status="active",
    is_active=True
)

# Add trigger
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

# Add action
action = WorkflowAction.objects.create(
    workflow=workflow,
    company=company,
    action_type="update_field",
    payload={"field": "status", "value": "qualified"},
    ordering=1
)
```

#### Configure GDPR Masking
```python
from core.permissions_models import GDPRRegistry

# Configure email masking
GDPRRegistry.objects.create(
    company=company,
    object_type="lead",
    field_name="email",
    mask_type="partial",
    mask_config={"show_first": 2, "show_last": 0, "mask_char": "*"},
    is_pii=True
)
```

### 4. Enable Structured Logging

Add to `settings.py`:
```python
MIDDLEWARE = [
    # ... other middleware
    'core.observability.StructuredLoggingMiddleware',
    # ... other middleware
]
```

---

## Usage Examples

### Example 1: Workflow Automation

```python
# In your lead creation view/service
from workflow.services import WorkflowExecutionService

def create_lead(request, data):
    # Create the lead
    lead = Lead.objects.create(**data)
    
    # Trigger workflows
    WorkflowExecutionService.trigger_workflow(
        event_type="lead.created",
        event_data={
            "lead_id": str(lead.id),
            "status": lead.status,
            "annual_revenue": lead.annual_revenue,
            "budget": lead.budget
        },
        company=request.active_company,
        user=request.user
    )
    
    return lead
```

### Example 2: Field Permissions in Serializer

```python
from rest_framework import serializers
from core.permissions_service import FieldPermissionMixin
from crm.models import Lead

class LeadSerializer(FieldPermissionMixin, serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'

# The mixin automatically:
# - Filters out hidden fields
# - Masks fields marked as "mask"
# - Based on the requesting user's role
```

### Example 3: Lead Scoring in API

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from crm.lead_scoring_service import LeadScoringV2Service

class LeadViewSet(viewsets.ModelViewSet):
    
    @action(detail=True, methods=['get'])
    def score(self, request, pk=None):
        lead = self.get_object()
        score_data = LeadScoringV2Service.calculate_lead_score(lead)
        
        return Response({
            'lead_id': str(lead.id),
            'score': score_data['total_score'],
            'quality': score_data.get('quality'),
            'recommendation': score_data.get('recommendation'),
            'components': score_data['components'],
            'explanation': score_data['explanation']
        })
```

### Example 4: Bulk Lead Scoring

```python
# In a Celery task or management command
from crm.lead_scoring_service import LeadScoringV2Service

def refresh_lead_scores(company_id):
    company = Company.objects.get(id=company_id)
    
    # Update scores for up to 1000 leads
    updated = LeadScoringV2Service.bulk_update_scores(company, limit=1000)
    
    print(f"Updated {updated} lead scores for {company.name}")
```

---

## Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Suites
```bash
# Workflow engine tests
pytest tests/test_workflow_engine.py

# Field permissions tests
pytest tests/test_field_permissions.py

# Lead scoring tests
pytest tests/test_lead_scoring.py
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

---

## Configuration

### Workflow Engine Settings
```python
# In settings.py or environment variables

# Enable workflow engine
WORKFLOW_ENGINE_ENABLED = True

# Maximum workflow execution time (seconds)
WORKFLOW_MAX_EXECUTION_TIME = 300

# Maximum actions per workflow
WORKFLOW_MAX_ACTIONS = 50
```

### Lead Scoring Configuration
```python
# Default scoring weights (can be overridden per company)
LEAD_SCORING_DEFAULT_WEIGHTS = {
    'status': 25,
    'recent_activity': 20,
    'age': 15,
    'completeness': 20,
    'engagement': 15,
    'custom_fields': 5,
}

# Score refresh interval (hours)
LEAD_SCORE_REFRESH_INTERVAL = 24
```

### Field Permissions Settings
```python
# Cache TTL for permissions (seconds)
FIELD_PERMISSION_CACHE_TTL = 300

# Enable masking audit logging
MASKING_AUDIT_ENABLED = True

# Default permission mode for unconfigured fields
DEFAULT_FIELD_PERMISSION = 'view'
```

---

## Monitoring & Debugging

### View Workflow Execution Logs
```python
from workflow.models import WorkflowRun

# Get recent workflow runs
recent_runs = WorkflowRun.objects.filter(
    company=company,
    created_at__gte=datetime.now() - timedelta(days=7)
).order_by('-created_at')

for run in recent_runs:
    print(f"{run.workflow.name}: {run.status} in {run.duration_ms}ms")
```

### Check Field Permission Audit Logs
```python
from core.permissions_models import MaskingAuditLog

# Get masking events for a user
logs = MaskingAuditLog.objects.filter(
    user=user,
    created_at__gte=datetime.now() - timedelta(days=1)
)

for log in logs:
    print(f"{log.field_name} on {log.object_type}: {log.action}")
```

### View Lead Score History
```python
from analytics.models import LeadScoreCache

# Get lead score cache
cache = LeadScoreCache.objects.get(lead=lead)

print(f"Score: {cache.total_score}")
print(f"Components: {cache.score_components}")
print(f"Last calculated: {cache.calculated_at}")
```

---

## Performance Tips

### 1. Use Caching
Field permissions are cached automatically. For workflows, consider:
```python
# Cache workflow trigger lookups
from django.core.cache import cache

def get_active_triggers(company, event_type):
    cache_key = f"triggers:{company.id}:{event_type}"
    triggers = cache.get(cache_key)
    
    if not triggers:
        triggers = WorkflowTrigger.objects.filter(
            company=company,
            event_type=event_type,
            is_active=True
        ).select_related('workflow')
        cache.set(cache_key, triggers, 300)  # 5 minutes
    
    return triggers
```

### 2. Batch Operations
```python
# Bulk update lead scores
LeadScoringV2Service.bulk_update_scores(company, limit=1000)

# Batch field filtering
filtered_results = [
    FieldPermissionService.filter_fields_for_role(data, role, 'lead')
    for data in lead_data_list
]
```

### 3. Use select_related/prefetch_related
```python
# Efficient workflow run queries
runs = WorkflowRun.objects.filter(
    company=company
).select_related(
    'workflow',
    'trigger',
    'triggered_by'
).prefetch_related(
    'action_runs__action'
)
```

---

## Troubleshooting

### Workflow Not Triggering
1. Check workflow status: `workflow.status == 'active'`
2. Check trigger status: `trigger.is_active == True`
3. Verify conditions match event data
4. Check workflow execution logs

### Field Masking Not Working
1. Verify RoleFieldPermission exists
2. Check GDPRRegistry configuration
3. Ensure FieldPermissionMixin is used in serializer
4. Check masking audit logs

### Low Lead Scores
1. Verify lead data completeness
2. Check scoring weight configuration
3. Review activity counts
4. Validate custom field weights

---

## API Endpoints (Planned)

These endpoints are documented but not yet implemented:

### Workflows
- `POST /api/v1/workflows/` - Create workflow
- `GET /api/v1/workflows/` - List workflows
- `GET /api/v1/workflows/{id}/` - Get workflow details
- `POST /api/v1/workflows/{id}/execute/` - Execute workflow

### Permissions
- `GET /api/v1/roles/{id}/field-permissions/` - List permissions
- `POST /api/v1/roles/{id}/field-permissions/` - Create permission

### Lead Scoring
- `GET /api/v1/leads/{id}/score/` - Get lead score
- `POST /api/v1/leads/score-bulk/` - Bulk scoring

---

## Further Reading

- [Workflow Engine Design](docs/WORKFLOW_ENGINE_DESIGN.md)
- [Field-Level Permissions](docs/FIELD_LEVEL_PERMISSIONS.md)
- [Lead Scoring v2](docs/LEAD_SCORING_V2_DESIGN.md)
- [Observability Stack](docs/OBSERVABILITY_STACK.md)
- [Implementation Summary](docs/PHASE4_IMPLEMENTATION_SUMMARY.md)

---

## Support & Contributing

For issues, questions, or contributions:
1. Check existing documentation
2. Review test cases for examples
3. Open an issue on GitHub
4. Submit a pull request with tests

---

## License

This software is part of the Claude CRM system. Please refer to the main LICENSE file for details.
