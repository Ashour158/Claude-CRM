# Observability Stack

## Overview
The observability stack provides comprehensive monitoring, logging, and tracing capabilities for the CRM system. This document describes the metrics, logging fields, tracing instrumentation, and integration patterns.

## Components

### 1. Structured Logging
- **Format**: JSON
- **Transport**: File + Stdout
- **Aggregation**: Can integrate with ELK, Datadog, Splunk
- **Retention**: 30 days default

### 2. Metrics (Prometheus-Compatible)
- **Collection**: In-process collection
- **Export**: `/metrics` endpoint
- **Storage**: Prometheus/Grafana
- **Retention**: 90 days

### 3. Tracing (OpenTelemetry-Style)
- **Protocol**: OpenTelemetry semantic conventions
- **Backend**: Jaeger, Zipkin, or Datadog APM
- **Sampling**: 10% in production, 100% in dev

## Structured Logging

### Log Fields

#### Standard Fields
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "correlation_id": "uuid-v4",
  "service": "crm-backend",
  "environment": "production"
}
```

#### Request Context
```json
{
  "user_id": "uuid",
  "org_id": "uuid",
  "method": "POST",
  "path": "/api/v1/leads/",
  "status_code": 201,
  "latency_ms": 45,
  "remote_addr": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

#### Error Context
```json
{
  "exception_type": "ValidationError",
  "exception_message": "Email is required",
  "stack_trace": "...",
  "error_code": "VALIDATION_001"
}
```

### Log Levels

| Level | Use Case | Example |
|-------|----------|---------|
| DEBUG | Development details | "Query took 15ms" |
| INFO | Normal operations | "User logged in", "Lead created" |
| WARNING | Recoverable issues | "Rate limit approaching", "Cache miss" |
| ERROR | Application errors | "Database connection failed", "API call failed" |
| CRITICAL | System failures | "Service crashed", "Data corruption detected" |

### Example Log Entries

#### Successful Request
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "correlation_id": "abc-123",
  "user_id": "user-uuid",
  "org_id": "org-uuid",
  "method": "GET",
  "path": "/api/v1/leads/",
  "status_code": 200,
  "latency_ms": 42
}
```

#### Failed Request
```json
{
  "timestamp": "2024-01-15T10:30:05.456Z",
  "level": "ERROR",
  "correlation_id": "abc-124",
  "user_id": "user-uuid",
  "org_id": "org-uuid",
  "method": "POST",
  "path": "/api/v1/workflows/{id}/execute/",
  "status_code": 500,
  "latency_ms": 2340,
  "exception_type": "DatabaseError",
  "exception_message": "Connection timeout after 2s"
}
```

#### Workflow Execution
```json
{
  "timestamp": "2024-01-15T10:31:00.789Z",
  "level": "INFO",
  "correlation_id": "abc-125",
  "org_id": "org-uuid",
  "event_type": "workflow.executed",
  "workflow_id": "workflow-uuid",
  "workflow_name": "Qualify High-Value Leads",
  "duration_ms": 156,
  "success": true,
  "actions_executed": 4
}
```

## Metrics

### Metric Types

#### Counters
- Monotonically increasing values
- Reset on service restart
- Examples: requests_total, errors_total

#### Gauges
- Point-in-time values
- Can increase or decrease
- Examples: active_users, memory_usage_bytes

#### Histograms
- Distribution of values
- Percentiles (p50, p95, p99)
- Examples: request_duration_ms, query_latency_ms

### Key Metrics

#### Application Metrics

##### Request Metrics
```
http_requests_total{method="GET", path="/api/v1/leads/", status="200"}
http_request_duration_ms{method="GET", path="/api/v1/leads/", quantile="0.95"}
http_errors_total{method="POST", path="/api/v1/leads/", status="500"}
```

##### Workflow Metrics
```
workflow_runs_total{workflow="Qualify Leads", status="completed"}
workflow_runs_total{workflow="Qualify Leads", status="failed"}
workflow_duration_ms{workflow="Qualify Leads", quantile="0.95"}
workflow_action_failures_total{action_type="send_email"}
```

##### Search Metrics
```
search_query_latency_ms{type="lead", quantile="0.95"}
search_results_total{type="lead"}
search_cache_hit_rate{type="lead"}
```

##### WebSocket Metrics
```
websocket_active_connections_gauge
websocket_messages_sent_total
websocket_connection_duration_seconds
```

##### Lead Scoring Metrics
```
lead_score_calculation_duration_ms{quantile="0.95"}
lead_score_cache_hit_rate
lead_score_recalculations_total
```

#### System Metrics

##### Database
```
db_connections_active_gauge
db_query_duration_ms{query_type="select", quantile="0.95"}
db_errors_total{error_type="timeout"}
db_pool_exhausted_total
```

##### Cache (Redis)
```
cache_hit_rate_gauge
cache_operations_total{operation="get", status="hit"}
cache_operations_total{operation="get", status="miss"}
cache_evictions_total
```

##### Celery (Background Tasks)
```
celery_tasks_total{task="refresh_lead_scores", status="success"}
celery_task_duration_seconds{task="refresh_lead_scores", quantile="0.95"}
celery_queue_length_gauge{queue="default"}
```

### Dashboard Examples

#### Request Dashboard
- Requests per second (by endpoint)
- p95 latency (by endpoint)
- Error rate (by endpoint)
- Status code distribution

#### Workflow Dashboard
- Workflow executions per hour
- Success vs failure rate
- Average execution time
- Most common failure reasons

#### System Health Dashboard
- Database connection pool usage
- Cache hit rate
- Memory usage
- CPU usage
- Disk I/O

## Tracing

### Span Structure

```python
{
  "trace_id": "uuid",
  "span_id": "uuid",
  "parent_span_id": "uuid",
  "operation_name": "workflow.execute",
  "start_time": "2024-01-15T10:30:00.000Z",
  "duration_ms": 156,
  "status": "success",
  "attributes": {
    "workflow.id": "uuid",
    "workflow.name": "Qualify Leads",
    "workflow.action_count": 4
  },
  "events": [
    {
      "name": "action.start",
      "timestamp": "2024-01-15T10:30:00.050Z",
      "attributes": {"action.type": "send_email"}
    },
    {
      "name": "action.complete",
      "timestamp": "2024-01-15T10:30:00.120Z",
      "attributes": {"action.type": "send_email", "status": "success"}
    }
  ]
}
```

### Instrumented Operations

#### Database Queries
```python
with TracingInstrumentation.create_span("db.query", {"query": "SELECT * FROM leads"}) as span:
    results = execute_query(...)
```

#### External API Calls
```python
with TracingInstrumentation.create_span("http.client", {"url": "https://api.example.com"}) as span:
    response = requests.get(...)
```

#### Workflow Execution
```python
with TracingInstrumentation.create_span("workflow.execute", {"workflow_id": workflow_id}) as span:
    workflow_result = execute_workflow(...)
```

#### Search Operations
```python
with TracingInstrumentation.create_span("search.query", {"index": "leads"}) as span:
    search_results = search_service.search(...)
```

### Trace Sampling

#### Production
- Sample 10% of successful requests
- Sample 100% of error requests
- Sample 100% of slow requests (>2s)

#### Development
- Sample 100% of all requests

## Integration

### Logging Configuration

#### Django Settings
```python
LOGGING = {
    'version': 1,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(timestamp)s %(level)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'json'
        }
    },
    'loggers': {
        'django': {'handlers': ['console', 'file'], 'level': 'INFO'},
        'workflow': {'handlers': ['console', 'file'], 'level': 'INFO'},
        'crm': {'handlers': ['console', 'file'], 'level': 'INFO'}
    }
}
```

### Middleware Setup

```python
MIDDLEWARE = [
    # ... other middleware
    'core.observability.StructuredLoggingMiddleware',
    # ... other middleware
]
```

### Metrics Endpoint

```python
# urls.py
path('metrics/', views.metrics_view, name='metrics'),
```

```python
# views.py
from core.observability import PrometheusMetrics

def metrics_view(request):
    metrics = PrometheusMetrics.get_metrics()
    # Format as Prometheus text format
    return HttpResponse(format_prometheus(metrics), content_type='text/plain')
```

## Alerting

### Critical Alerts

#### Service Down
```
alert: ServiceDown
expr: up{job="crm-backend"} == 0
for: 1m
severity: critical
```

#### High Error Rate
```
alert: HighErrorRate
expr: rate(http_errors_total[5m]) > 0.05
for: 5m
severity: critical
```

#### Database Connection Pool Exhausted
```
alert: DatabasePoolExhausted
expr: db_pool_exhausted_total > 0
for: 1m
severity: critical
```

### Warning Alerts

#### High Latency
```
alert: HighLatency
expr: histogram_quantile(0.95, http_request_duration_ms) > 1000
for: 10m
severity: warning
```

#### Cache Hit Rate Low
```
alert: LowCacheHitRate
expr: cache_hit_rate_gauge < 0.8
for: 15m
severity: warning
```

#### Workflow Failures
```
alert: HighWorkflowFailureRate
expr: rate(workflow_runs_total{status="failed"}[10m]) > 0.1
for: 5m
severity: warning
```

## Performance Benchmarks

### Baseline Performance

| Operation | Target p50 | Target p95 | Target p99 |
|-----------|------------|------------|------------|
| GET /api/v1/leads/ | <50ms | <100ms | <200ms |
| POST /api/v1/leads/ | <100ms | <200ms | <500ms |
| Workflow Execution | <200ms | <500ms | <1s |
| Search Query | <100ms | <300ms | <1s |
| Lead Score Calculation | <20ms | <50ms | <100ms |

### Load Testing

#### Sustained Load
- 1000 req/s for 10 minutes
- <1% error rate
- p95 latency within targets

#### Spike Load
- 5000 req/s for 1 minute
- <5% error rate
- Graceful degradation

## Best Practices

### Logging
1. Always include correlation_id
2. Log at appropriate levels
3. Include context (user_id, org_id)
4. Don't log sensitive data (passwords, tokens)
5. Use structured logging (JSON)

### Metrics
1. Use consistent naming (verb_noun_unit)
2. Include relevant labels
3. Don't create high-cardinality metrics
4. Document metric meanings
5. Set up alerts for SLOs

### Tracing
1. Trace cross-service calls
2. Include relevant attributes
3. Sample appropriately
4. Don't trace too granularly
5. Link traces to logs via correlation_id

## Troubleshooting

### High Latency
1. Check metrics dashboard for p95/p99
2. Identify slow endpoint in traces
3. Review database query times
4. Check cache hit rates
5. Review external API call durations

### High Error Rate
1. Check error logs for patterns
2. Review exception types in metrics
3. Trace failed requests
4. Check database connectivity
5. Review resource exhaustion

### Memory Leaks
1. Monitor memory_usage_bytes gauge
2. Check for unbounded caches
3. Review connection pooling
4. Profile with memory profiler
5. Check for circular references

## Future Enhancements

- Real-time anomaly detection
- Predictive alerting
- Distributed tracing across microservices
- APM integration (DataDog, New Relic)
- Custom business metrics dashboard
- SLO tracking and reporting
- Cost attribution by tenant

## Conclusion
A comprehensive observability stack is essential for maintaining system reliability, debugging issues quickly, and understanding system behavior in production.
