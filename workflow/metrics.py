# workflow/metrics.py
# Prometheus metrics for workflow intelligence

try:
    from prometheus_client import Counter, Histogram, Gauge
    
    # Workflow execution metrics
    workflow_execution_total = Counter(
        'workflow_execution_total',
        'Total number of workflow executions',
        ['workflow_type', 'status']
    )
    
    workflow_execution_duration_seconds = Histogram(
        'workflow_execution_duration_seconds',
        'Workflow execution duration in seconds',
        ['workflow_type'],
        buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
    )
    
    # Simulation metrics
    workflow_simulation_total = Counter(
        'workflow_simulation_total',
        'Total number of workflow simulations',
        ['status']
    )
    
    workflow_simulation_duration_seconds = Histogram(
        'workflow_simulation_duration_seconds',
        'Workflow simulation duration in seconds',
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
    )
    
    # SLA metrics
    workflow_sla_breach_total = Counter(
        'workflow_sla_breach_total',
        'Total number of SLA breaches',
        ['severity', 'workflow_name']
    )
    
    workflow_sla_target_seconds = Gauge(
        'workflow_sla_target_seconds',
        'SLA target duration in seconds',
        ['workflow_name', 'sla_name']
    )
    
    workflow_sla_percentage = Gauge(
        'workflow_sla_percentage',
        'Current SLA percentage',
        ['workflow_name', 'sla_name']
    )
    
    # Suggestion metrics
    workflow_suggestion_total = Counter(
        'workflow_suggestion_total',
        'Total number of workflow suggestions',
        ['source', 'status']
    )
    
    workflow_suggestion_confidence = Histogram(
        'workflow_suggestion_confidence',
        'Workflow suggestion confidence score',
        ['source'],
        buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    )
    
    # Action catalog metrics
    action_execution_total = Counter(
        'action_execution_total',
        'Total number of action executions',
        ['action_type', 'latency_class']
    )
    
    action_execution_duration_ms = Histogram(
        'action_execution_duration_ms',
        'Action execution duration in milliseconds',
        ['action_type'],
        buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000, 10000]
    )
    
    action_success_rate = Gauge(
        'action_success_rate',
        'Action success rate',
        ['action_type']
    )
    
    METRICS_ENABLED = True
except ImportError:
    # Prometheus client not installed, metrics disabled
    METRICS_ENABLED = False
    workflow_execution_total = None
    workflow_execution_duration_seconds = None
    workflow_simulation_total = None
    workflow_simulation_duration_seconds = None
    workflow_sla_breach_total = None
    workflow_sla_target_seconds = None
    workflow_sla_percentage = None
    workflow_suggestion_total = None
    workflow_suggestion_confidence = None
    action_execution_total = None
    action_execution_duration_ms = None
    action_success_rate = None


def record_workflow_execution(workflow_type, status, duration_seconds):
    """Record workflow execution metrics"""
    if METRICS_ENABLED:
        try:
            workflow_execution_total.labels(
                workflow_type=workflow_type,
                status=status
            ).inc()
            workflow_execution_duration_seconds.labels(
                workflow_type=workflow_type
            ).observe(duration_seconds)
        except Exception:
            pass


def record_workflow_simulation(status, duration_seconds):
    """Record workflow simulation metrics"""
    if METRICS_ENABLED:
        try:
            workflow_simulation_total.labels(status=status).inc()
            workflow_simulation_duration_seconds.observe(duration_seconds)
        except Exception:
            pass


def record_sla_breach(severity, workflow_name):
    """Record SLA breach metrics"""
    if METRICS_ENABLED:
        try:
            workflow_sla_breach_total.labels(
                severity=severity,
                workflow_name=workflow_name
            ).inc()
        except Exception:
            pass


def update_sla_metrics(workflow_name, sla_name, target_seconds, current_percentage):
    """Update SLA metrics"""
    if METRICS_ENABLED:
        try:
            workflow_sla_target_seconds.labels(
                workflow_name=workflow_name,
                sla_name=sla_name
            ).set(target_seconds)
            workflow_sla_percentage.labels(
                workflow_name=workflow_name,
                sla_name=sla_name
            ).set(current_percentage)
        except Exception:
            pass


def record_workflow_suggestion(source, status, confidence_score):
    """Record workflow suggestion metrics"""
    if METRICS_ENABLED:
        try:
            workflow_suggestion_total.labels(
                source=source,
                status=status
            ).inc()
            workflow_suggestion_confidence.labels(source=source).observe(confidence_score)
        except Exception:
            pass


def record_action_execution(action_type, latency_class, duration_ms, success):
    """Record action execution metrics"""
    if METRICS_ENABLED:
        try:
            action_execution_total.labels(
                action_type=action_type,
                latency_class=latency_class
            ).inc()
            action_execution_duration_ms.labels(action_type=action_type).observe(duration_ms)
        except Exception:
            pass


def update_action_success_rate(action_type, success_rate):
    """Update action success rate metric"""
    if METRICS_ENABLED:
        try:
            action_success_rate.labels(action_type=action_type).set(success_rate)
        except Exception:
            pass
