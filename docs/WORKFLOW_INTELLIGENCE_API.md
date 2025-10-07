# Workflow & Automation Intelligence API Documentation

## Overview

The Workflow & Automation Intelligence module provides advanced workflow automation capabilities including:
- Action catalog with metadata (idempotent, latency classification, side effects)
- AI-powered workflow suggestions based on historical data
- Workflow simulation/dry-run with branch exploration
- SLA tracking and breach alerting with Prometheus metrics
- Blueprint template import/export with versioning

## Base URL

All workflow intelligence endpoints are prefixed with `/api/v1/workflow/`

---

## Action Catalog

### List Actions
```
GET /api/v1/workflow/action-catalog/
```

**Query Parameters:**
- `action_type` - Filter by action type
- `is_idempotent` - Filter by idempotent flag (true/false)
- `latency_class` - Filter by latency class (instant, fast, medium, slow, very_slow)
- `is_active` - Filter by active status
- `search` - Search by name or description

**Response:**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "name": "Send Email Notification",
      "description": "Send email to specified recipients",
      "action_type": "notification",
      "is_idempotent": true,
      "latency_class": "fast",
      "side_effects": ["email_sent", "notification_logged"],
      "input_schema": {
        "type": "object",
        "properties": {
          "to": {"type": "string"},
          "subject": {"type": "string"},
          "body": {"type": "string"}
        }
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "sent": {"type": "boolean"},
          "message_id": {"type": "string"}
        }
      },
      "execution_count": 1250,
      "avg_execution_time_ms": 450,
      "success_rate": 0.998,
      "is_active": true,
      "is_global": false,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### Create Action
```
POST /api/v1/workflow/action-catalog/
```

**Request Body:**
```json
{
  "name": "Database Update",
  "description": "Update database records",
  "action_type": "update",
  "is_idempotent": false,
  "latency_class": "medium",
  "side_effects": ["db_write", "cache_invalidation"],
  "input_schema": {
    "type": "object",
    "properties": {
      "table": {"type": "string"},
      "data": {"type": "object"}
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "success": {"type": "boolean"},
      "rows_affected": {"type": "integer"}
    }
  }
}
```

---

## Workflow Suggestions

### List Suggestions
```
GET /api/v1/workflow/workflow-suggestions/
```

**Query Parameters:**
- `source` - Filter by source (historical, llm, pattern, user)
- `status` - Filter by status (pending, accepted, rejected, implemented)
- `ordering` - Order by field (confidence_score, created_at, pattern_frequency)

**Response:**
```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "title": "Auto-approve small discounts",
      "description": "Based on historical data, discounts under 10% are always approved. Consider auto-approval.",
      "source": "historical",
      "workflow_template": {
        "workflow_type": "approval",
        "trigger_conditions": {"discount_percentage": {"$lt": 10}},
        "steps": [
          {"action": "auto_approve", "conditions": {}}
        ]
      },
      "confidence_score": 0.85,
      "supporting_data": {
        "sample_count": 150,
        "approval_rate": 1.0,
        "avg_approval_time": "2 minutes"
      },
      "pattern_frequency": 150,
      "status": "pending",
      "reviewed_by": null,
      "reviewed_at": null,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### Generate Suggestions
```
POST /api/v1/workflow/workflow-suggestions/generate/
```

Analyzes historical workflow execution data to generate suggestions.

**Response:**
```json
{
  "id": 2,
  "title": "Suggested: Parallel approval for multiple approvers",
  "description": "When multiple approvers at same level, run in parallel to save time",
  "source": "pattern",
  "confidence_score": 0.78,
  "pattern_frequency": 85,
  "status": "pending"
}
```

### Accept Suggestion
```
POST /api/v1/workflow/workflow-suggestions/{id}/accept/
```

**Request Body:**
```json
{
  "notes": "Good suggestion, will implement this week"
}
```

### Reject Suggestion
```
POST /api/v1/workflow/workflow-suggestions/{id}/reject/
```

**Request Body:**
```json
{
  "notes": "Not applicable for our use case"
}
```

---

## Workflow Simulation

### Create Simulation (Dry-Run)
```
POST /api/v1/workflow/workflow-simulations/
```

Runs a workflow simulation without making any database mutations. Useful for testing and validation.

**Request Body:**
```json
{
  "workflow_id": 5,
  "input_data": {
    "amount": 15000,
    "discount_percentage": 15,
    "customer_type": "premium"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "workflow": 5,
  "workflow_name": "Discount Approval Workflow",
  "input_data": {
    "amount": 15000,
    "discount_percentage": 15,
    "customer_type": "premium"
  },
  "status": "completed",
  "execution_path": [
    {
      "step_index": 0,
      "step_name": "Validate Request",
      "action": "validation",
      "status": "simulated",
      "estimated_duration_ms": 100
    },
    {
      "step_index": 1,
      "step_name": "Manager Approval",
      "action": "approval",
      "status": "simulated",
      "estimated_duration_ms": 1000
    },
    {
      "step_index": 2,
      "step_name": "Director Approval",
      "action": "approval",
      "status": "simulated",
      "estimated_duration_ms": 1000
    }
  ],
  "branch_explorations": [
    {
      "from_step": 1,
      "condition": "amount > 10000",
      "next_step": 2
    }
  ],
  "approval_chain": [
    {
      "step": 1,
      "approver": "manager",
      "conditions": {}
    },
    {
      "step": 2,
      "approver": "director",
      "conditions": {"amount": {"$gt": 10000}}
    }
  ],
  "predicted_duration_ms": 2100,
  "validation_errors": [],
  "warnings": [],
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:00:02Z"
}
```

### List Simulations
```
GET /api/v1/workflow/workflow-simulations/
```

**Query Parameters:**
- `workflow` - Filter by workflow ID
- `status` - Filter by status
- `created_by` - Filter by user

---

## Workflow SLA

### List SLAs
```
GET /api/v1/workflow/workflow-slas/
```

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "workflow": 5,
      "workflow_name": "Discount Approval Workflow",
      "name": "Response Time SLA",
      "description": "Must complete within 5 minutes",
      "target_duration_seconds": 300,
      "warning_threshold_seconds": 240,
      "critical_threshold_seconds": 300,
      "slo_window_hours": 24,
      "slo_target_percentage": 99.0,
      "is_active": true,
      "total_executions": 1000,
      "breached_executions": 5,
      "current_slo_percentage": 99.5,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Create SLA
```
POST /api/v1/workflow/workflow-slas/
```

**Request Body:**
```json
{
  "workflow": 5,
  "name": "Performance SLA",
  "description": "Performance target for workflow execution",
  "target_duration_seconds": 600,
  "warning_threshold_seconds": 480,
  "critical_threshold_seconds": 600,
  "slo_window_hours": 24,
  "slo_target_percentage": 95.0
}
```

### Get SLA Metrics
```
GET /api/v1/workflow/workflow-slas/{id}/metrics/
```

Returns detailed metrics for the SLA within the configured SLO window.

**Response:**
```json
{
  "sla_name": "Response Time SLA",
  "slo_window_hours": 24,
  "slo_target_percentage": 99.0,
  "current_slo_percentage": 99.5,
  "total_executions": 1000,
  "breached_executions": 5,
  "window_breaches": 2,
  "critical_breaches": 1,
  "warning_breaches": 1
}
```

---

## SLA Breaches

### List Breaches
```
GET /api/v1/workflow/sla-breaches/
```

**Query Parameters:**
- `sla` - Filter by SLA ID
- `severity` - Filter by severity (warning, critical)
- `acknowledged` - Filter by acknowledgment status
- `alert_sent` - Filter by alert sent status

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "sla": 1,
      "sla_name": "Response Time SLA",
      "workflow_name": "Discount Approval Workflow",
      "workflow_execution": 1234,
      "severity": "critical",
      "actual_duration_seconds": 450,
      "target_duration_seconds": 300,
      "breach_margin_seconds": 150,
      "alert_sent": true,
      "alert_sent_at": "2024-01-15T10:05:00Z",
      "alert_recipients": ["ops@company.com", "manager@company.com"],
      "acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null,
      "resolution_notes": "",
      "detected_at": "2024-01-15T10:05:00Z"
    }
  ]
}
```

### Get Unacknowledged Breaches
```
GET /api/v1/workflow/sla-breaches/unacknowledged/
```

Returns all breaches that have not been acknowledged.

### Acknowledge Breach
```
POST /api/v1/workflow/sla-breaches/{id}/acknowledge/
```

**Request Body:**
```json
{
  "notes": "Expected delay due to high load during peak hours. Scaling infrastructure."
}
```

---

## Blueprint Templates

### Export Template
```
GET /api/v1/workflow/process-templates/{id}/export/
```

Exports a template as a blueprint that can be shared or imported.

**Response:**
```json
{
  "name": "Standard Approval Process",
  "description": "Multi-level approval workflow template",
  "version": "1.2.0",
  "template_type": "approval",
  "process_steps": [
    {
      "step": 1,
      "name": "Validate Request",
      "action": "validation",
      "config": {}
    },
    {
      "step": 2,
      "name": "Manager Approval",
      "action": "approval",
      "approver": "manager"
    }
  ],
  "variables": [
    {
      "name": "amount",
      "type": "number",
      "description": "Transaction amount"
    },
    {
      "name": "discount_percentage",
      "type": "number",
      "description": "Discount percentage requested"
    }
  ],
  "settings": {
    "timeout": 300,
    "max_retries": 3
  },
  "graph_spec": {
    "nodes": [
      {"id": "start", "type": "trigger", "x": 100, "y": 100},
      {"id": "step1", "type": "action", "x": 200, "y": 100},
      {"id": "step2", "type": "decision", "x": 300, "y": 100},
      {"id": "end", "type": "terminator", "x": 400, "y": 100}
    ],
    "edges": [
      {"from": "start", "to": "step1"},
      {"from": "step1", "to": "step2"},
      {"from": "step2", "to": "end", "condition": "approved"}
    ]
  }
}
```

### Import Blueprint
```
POST /api/v1/workflow/process-templates/import_blueprint/
```

Imports a blueprint template from JSON.

**Request Body:** (Same format as export response)

**Response:**
```json
{
  "id": 10,
  "name": "Standard Approval Process",
  "version": "1.2.0",
  "template_type": "approval",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

## Prometheus Metrics

The following Prometheus metrics are exposed for workflow intelligence:

### Workflow Execution Metrics
- `workflow_execution_total{workflow_type, status}` - Counter of workflow executions
- `workflow_execution_duration_seconds{workflow_type}` - Histogram of execution duration

### Simulation Metrics
- `workflow_simulation_total{status}` - Counter of simulations
- `workflow_simulation_duration_seconds` - Histogram of simulation duration

### SLA Metrics
- `workflow_sla_breach_total{severity, workflow_name}` - Counter of SLA breaches
- `workflow_sla_target_seconds{workflow_name, sla_name}` - Gauge of SLA target
- `workflow_sla_percentage{workflow_name, sla_name}` - Gauge of current SLA percentage

### Suggestion Metrics
- `workflow_suggestion_total{source, status}` - Counter of suggestions
- `workflow_suggestion_confidence{source}` - Histogram of confidence scores

### Action Metrics
- `action_execution_total{action_type, latency_class}` - Counter of action executions
- `action_execution_duration_ms{action_type}` - Histogram of action duration
- `action_success_rate{action_type}` - Gauge of action success rate

---

## Error Handling

All endpoints follow standard REST API error responses:

**400 Bad Request**
```json
{
  "error": "Invalid input data",
  "details": {
    "workflow_id": ["This field is required"]
  }
}
```

**404 Not Found**
```json
{
  "error": "Workflow not found"
}
```

**500 Internal Server Error**
```json
{
  "error": "Internal server error",
  "message": "Failed to execute simulation"
}
```

---

## Best Practices

### Action Catalog
- Mark actions as `is_idempotent=true` only if they can be safely retried
- Accurately classify `latency_class` for better simulation predictions
- Document all `side_effects` for transparency

### Workflow Simulation
- Always run simulations before deploying new workflows to production
- Review `validation_errors` and `warnings` carefully
- Use simulations to estimate workflow duration and resource needs

### SLA Management
- Set `warning_threshold` to 80% of `target_duration` for early alerts
- Configure `slo_window_hours` based on business needs (24h for daily, 168h for weekly)
- Acknowledge breaches promptly with detailed resolution notes

### Blueprint Templates
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Include comprehensive `graph_spec` for visualization
- Export templates before making major changes (backup)

---

## Examples

### Example: Complete Workflow Simulation Flow

1. **Create a workflow simulation**
```bash
curl -X POST https://api.example.com/api/v1/workflow/workflow-simulations/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": 5,
    "input_data": {"amount": 15000, "discount": 15}
  }'
```

2. **Review simulation results**
- Check `execution_path` for step-by-step execution
- Review `approval_chain` for approval sequence
- Examine `branch_explorations` for conditional paths
- Note `predicted_duration_ms` for performance estimation

3. **Check for issues**
- Review `validation_errors` array
- Check `warnings` array for potential problems

### Example: SLA Monitoring Flow

1. **Create SLA for workflow**
```bash
curl -X POST https://api.example.com/api/v1/workflow/workflow-slas/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": 5,
    "name": "5-minute SLA",
    "target_duration_seconds": 300,
    "warning_threshold_seconds": 240,
    "critical_threshold_seconds": 300,
    "slo_window_hours": 24,
    "slo_target_percentage": 99.0
  }'
```

2. **Monitor breaches**
```bash
curl https://api.example.com/api/v1/workflow/sla-breaches/unacknowledged/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

3. **Acknowledge and resolve**
```bash
curl -X POST https://api.example.com/api/v1/workflow/sla-breaches/1/acknowledge/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Resolved by scaling infrastructure"
  }'
```

---

## Rate Limits

- Standard endpoints: 100 requests/minute
- Simulation endpoints: 20 requests/minute (computationally expensive)
- Suggestion generation: 10 requests/hour

---

## Support

For questions or issues with the Workflow Intelligence API, contact support@example.com
