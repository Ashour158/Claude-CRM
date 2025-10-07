# Workflow & Automation Intelligence

Advanced workflow automation and intelligence features for the Claude CRM system.

## Overview

The Workflow Intelligence module enhances the CRM's workflow capabilities with:

1. **Action Catalog** - Metadata-driven action library with idempotent flags, latency classification, and side effect tracking
2. **Workflow Suggestions** - AI-powered suggestions based on historical pattern mining and LLM analysis
3. **Simulation/Dry-Run** - Test workflows without database mutations, with branch exploration and approval chain visualization
4. **SLA Tracking & Alerting** - Monitor workflow performance with Prometheus metrics and breach alerting
5. **Blueprint Templates** - Import/export workflow templates with versioning and graph specifications

## Features

### 1. Action Catalog

The action catalog provides a metadata-rich registry of workflow actions:

```python
from workflow.models import ActionCatalog

# Create an action
action = ActionCatalog.objects.create(
    company=company,
    name='Send Email Notification',
    action_type='notification',
    is_idempotent=True,  # Can be safely retried
    latency_class='fast',  # < 1 second
    side_effects=['email_sent', 'notification_logged'],
    input_schema={'type': 'object', 'properties': {...}},
    output_schema={'type': 'object', 'properties': {...}}
)
```

**Metadata Fields:**
- `is_idempotent` - Whether the action can be safely retried without side effects
- `latency_class` - Expected execution time (instant, fast, medium, slow, very_slow)
- `side_effects` - List of side effects produced by this action
- `input_schema` / `output_schema` - JSON schema for validation
- `execution_count` / `avg_execution_time_ms` / `success_rate` - Runtime statistics

### 2. Workflow Suggestions

Generate intelligent workflow suggestions based on historical data:

```bash
# Run the suggestion generator
python manage.py generate_workflow_suggestions --days 30 --min-occurrences 10

# Or via API
POST /api/v1/workflow/workflow-suggestions/generate/
```

**Suggestion Types:**
- **Auto-Approvals** - Identifies approval patterns with >95% approval rate
- **Parallel Approvals** - Suggests running sequential approvals in parallel
- **Performance Optimizations** - Identifies slow workflows that could be optimized
- **Error Handling** - Suggests improvements for workflows with high failure rates

**Example Suggestion:**
```json
{
  "title": "Auto-approve small discounts",
  "description": "Based on 150 requests, discounts under 10% are always approved",
  "source": "historical",
  "confidence_score": 0.85,
  "pattern_frequency": 150,
  "status": "pending"
}
```

### 3. Workflow Simulation

Test workflows without making database changes:

```python
from workflow.models import WorkflowSimulation

# Create simulation
simulation = WorkflowSimulation.objects.create(
    company=company,
    workflow=workflow,
    input_data={'amount': 15000, 'discount': 15},
    created_by=user
)

# Results include:
# - execution_path: Step-by-step execution trace
# - branch_explorations: All conditional branches explored
# - approval_chain: Predicted approval sequence
# - predicted_duration_ms: Estimated completion time
# - validation_errors: Configuration issues found
# - warnings: Potential problems detected
```

**API Usage:**
```bash
curl -X POST /api/v1/workflow/workflow-simulations/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "workflow_id": 5,
    "input_data": {"amount": 15000, "discount": 15}
  }'
```

**Benefits:**
- Test workflows before deployment
- Validate configuration without side effects
- Understand approval chains and branching logic
- Estimate execution time
- Identify configuration errors early

### 4. SLA Tracking & Alerting

Monitor workflow performance and get alerted on breaches:

```python
from workflow.models import WorkflowSLA

# Create SLA
sla = WorkflowSLA.objects.create(
    workflow=workflow,
    name='Response Time SLA',
    target_duration_seconds=300,  # 5 minutes
    warning_threshold_seconds=240,  # 4 minutes
    critical_threshold_seconds=300,
    slo_window_hours=24,  # Evaluate over 24 hours
    slo_target_percentage=99.0  # 99% should meet SLA
)
```

**Automatic Monitoring:**
```python
from workflow.sla_monitor import SLAMonitor

# Check workflow execution
monitor = SLAMonitor()
monitor.check_execution(execution)

# Automatically:
# - Detects breaches (warning/critical)
# - Records breach in database
# - Sends email alerts
# - Updates Prometheus metrics
# - Calculates SLO percentage
```

**Breach Alerting:**
- Email alerts to workflow owner and admins
- Configurable severity levels (warning/critical)
- Alert includes execution details and breach margin
- Acknowledgment workflow for resolution tracking

**API Endpoints:**
```bash
# Get SLA metrics
GET /api/v1/workflow/workflow-slas/{id}/metrics/

# Get unacknowledged breaches
GET /api/v1/workflow/sla-breaches/unacknowledged/

# Acknowledge breach
POST /api/v1/workflow/sla-breaches/{id}/acknowledge/
```

### 5. Blueprint Templates

Share and reuse workflows with versioned blueprints:

```python
from workflow.models import ProcessTemplate

# Create template with blueprint
template = ProcessTemplate.objects.create(
    name='Standard Approval Process',
    version='1.2.0',  # Semantic versioning
    template_type='approval',
    process_steps=[...],
    variables=[...],
    settings={...},
    graph_spec={
        'nodes': [
            {'id': 'start', 'type': 'trigger', 'x': 100, 'y': 100},
            {'id': 'step1', 'type': 'action', 'x': 200, 'y': 100},
            ...
        ],
        'edges': [
            {'from': 'start', 'to': 'step1'},
            ...
        ]
    }
)
```

**Export Blueprint:**
```bash
GET /api/v1/workflow/process-templates/{id}/export/

# Returns JSON with:
# - Template configuration
# - Version information
# - Graph specification for visualization
# - Variables and settings
```

**Import Blueprint:**
```bash
POST /api/v1/workflow/process-templates/import_blueprint/
Content-Type: application/json

{
  "name": "Imported Template",
  "version": "1.0.0",
  "template_type": "approval",
  ...
}
```

**Use Cases:**
- Share workflows across teams
- Version control for workflow definitions
- Backup critical workflows
- Template marketplace
- Workflow visualization

## Prometheus Metrics

All workflow intelligence features expose Prometheus metrics:

### Workflow Execution
```
workflow_execution_total{workflow_type, status}
workflow_execution_duration_seconds{workflow_type}
```

### Simulations
```
workflow_simulation_total{status}
workflow_simulation_duration_seconds
```

### SLA Monitoring
```
workflow_sla_breach_total{severity, workflow_name}
workflow_sla_target_seconds{workflow_name, sla_name}
workflow_sla_percentage{workflow_name, sla_name}
```

### Suggestions
```
workflow_suggestion_total{source, status}
workflow_suggestion_confidence{source}
```

### Actions
```
action_execution_total{action_type, latency_class}
action_execution_duration_ms{action_type}
action_success_rate{action_type}
```

## Installation

1. **Run Migrations:**
```bash
python manage.py migrate workflow
```

2. **Install Dependencies:**
```bash
pip install prometheus-client psutil
```

3. **Configure Settings:**
```python
# settings.py

# SLA Alerting
SLA_ALERTS_ENABLED = True
SLA_ALERT_RECIPIENTS = ['ops@company.com']
DEFAULT_FROM_EMAIL = 'noreply@company.com'

# Optional: Prometheus metrics endpoint
PROMETHEUS_METRICS_ENABLED = True
```

4. **Add to URLs:**
```python
# config/urls.py
urlpatterns = [
    path('api/v1/workflow/', include('workflow.urls')),
    ...
]
```

## Usage Examples

### Example 1: Multi-Level Approval with Simulation

```python
# 1. Create workflow
workflow = Workflow.objects.create(
    company=company,
    name='Discount Approval',
    workflow_type='approval',
    steps=[
        {'name': 'Validate', 'action': 'validation'},
        {'name': 'Manager Approval', 'action': 'approval', 'approver': 'manager'},
        {'name': 'Director Approval', 'action': 'approval', 'approver': 'director',
         'conditions': {'amount': {'$gt': 10000}}},
        {'name': 'CFO Approval', 'action': 'approval', 'approver': 'cfo',
         'conditions': {'amount': {'$gt': 50000}}}
    ]
)

# 2. Run simulation with different amounts
simulation_small = WorkflowSimulation.objects.create(
    workflow=workflow,
    input_data={'amount': 5000},
    created_by=user
)
# Result: Only manager approval required

simulation_large = WorkflowSimulation.objects.create(
    workflow=workflow,
    input_data={'amount': 75000},
    created_by=user
)
# Result: Manager -> Director -> CFO approval chain

# 3. Review results
print(f"Small amount approval chain: {simulation_small.approval_chain}")
print(f"Large amount approval chain: {simulation_large.approval_chain}")
```

### Example 2: SLA Monitoring with Alerting

```python
# 1. Create SLA
sla = WorkflowSLA.objects.create(
    workflow=workflow,
    name='5-Minute SLA',
    target_duration_seconds=300,
    warning_threshold_seconds=240,
    critical_threshold_seconds=300,
    slo_window_hours=24,
    slo_target_percentage=99.0
)

# 2. Set up automatic monitoring
from workflow.sla_monitor import SLAMonitor
monitor = SLAMonitor()

# 3. When workflow completes
execution = WorkflowExecution.objects.get(id=123)
monitor.check_execution(execution)
# Automatically detects breaches and sends alerts

# 4. Review breaches
breaches = SLABreach.objects.filter(
    sla=sla,
    acknowledged=False
)
for breach in breaches:
    print(f"Breach: {breach.severity}, margin: {breach.breach_margin_seconds}s")
```

### Example 3: Historical Suggestion Mining

```bash
# Generate suggestions from last 30 days
python manage.py generate_workflow_suggestions --days 30

# Review suggestions
curl /api/v1/workflow/workflow-suggestions/ \
  -H "Authorization: Bearer TOKEN"

# Accept a suggestion
curl -X POST /api/v1/workflow/workflow-suggestions/5/accept/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{"notes": "Will implement this week"}'
```

## Testing

Run the comprehensive test suite:

```bash
# Run all workflow intelligence tests
pytest tests/test_workflow_intelligence.py -v

# Run specific test classes
pytest tests/test_workflow_intelligence.py::TestActionCatalog -v
pytest tests/test_workflow_intelligence.py::TestWorkflowSimulation -v
pytest tests/test_workflow_intelligence.py::TestWorkflowSLA -v

# Run with coverage
pytest tests/test_workflow_intelligence.py --cov=workflow
```

## Best Practices

### Action Catalog
- ✅ Mark actions as idempotent only if truly safe to retry
- ✅ Accurately classify latency for better simulation predictions
- ✅ Document all side effects comprehensively
- ✅ Update execution statistics regularly

### Workflow Simulation
- ✅ Always simulate before deploying to production
- ✅ Test with edge case inputs
- ✅ Review validation errors and warnings
- ✅ Use predicted duration for capacity planning

### SLA Management
- ✅ Set warning threshold to 80% of target
- ✅ Choose appropriate SLO window (24h daily, 168h weekly)
- ✅ Acknowledge breaches with detailed notes
- ✅ Monitor SLO percentage regularly
- ✅ Adjust thresholds based on actual performance

### Suggestions
- ✅ Review suggestions weekly
- ✅ Validate high-confidence suggestions first
- ✅ Document acceptance/rejection reasons
- ✅ Monitor pattern frequency trends

### Blueprint Templates
- ✅ Use semantic versioning (MAJOR.MINOR.PATCH)
- ✅ Include comprehensive graph specifications
- ✅ Export templates before major changes
- ✅ Document variable requirements
- ✅ Test imported templates in simulation

## Troubleshooting

### SLA Alerts Not Sending
```python
# Check settings
SLA_ALERTS_ENABLED = True
DEFAULT_FROM_EMAIL = 'valid@email.com'

# Check email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
```

### Simulation Errors
```python
# Check workflow configuration
workflow = Workflow.objects.get(id=5)
print(workflow.steps)  # Ensure valid JSON

# Check for missing actions
for step in workflow.steps:
    action_type = step.get('action')
    if not ActionCatalog.objects.filter(action_type=action_type).exists():
        print(f"Warning: Action {action_type} not in catalog")
```

### Prometheus Metrics Not Appearing
```python
# Check if prometheus_client is installed
import prometheus_client

# Check metrics module
from workflow.metrics import METRICS_ENABLED
print(f"Metrics enabled: {METRICS_ENABLED}")

# Expose metrics endpoint
from django.urls import path
from prometheus_client import make_wsgi_app

urlpatterns = [
    path('metrics/', make_wsgi_app()),
]
```

## API Documentation

Complete API documentation is available at:
- [Workflow Intelligence API Documentation](./docs/WORKFLOW_INTELLIGENCE_API.md)

## Support

For issues or questions:
- Check the [API Documentation](./docs/WORKFLOW_INTELLIGENCE_API.md)
- Review test cases in `tests/test_workflow_intelligence.py`
- Open an issue in the repository

## Contributing

When adding new workflow intelligence features:
1. Add models to `workflow/models.py`
2. Create serializers in `workflow/serializers.py`
3. Add views in `workflow/views.py`
4. Register routes in `workflow/urls.py`
5. Add admin interfaces in `workflow/admin.py`
6. Add Prometheus metrics in `workflow/metrics.py`
7. Write comprehensive tests
8. Update documentation

## License

Part of the Claude CRM system.
