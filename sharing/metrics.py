# sharing/metrics.py
# Optional Prometheus metrics for sharing enforcement

try:
    from prometheus_client import Counter
    
    # Counter for tracking sharing filter applications
    sharing_filter_applied_total = Counter(
        'sharing_filter_applied_total',
        'Total number of times sharing filter was applied',
        ['object_type']
    )
    
    METRICS_ENABLED = True
except ImportError:
    # Prometheus client not installed, metrics disabled
    METRICS_ENABLED = False
    sharing_filter_applied_total = None


def increment_sharing_filter_metric(object_type: str):
    """
    Increment the sharing filter counter for the given object type.
    
    Args:
        object_type: The type of object being filtered (lead, deal, etc.)
    """
    if METRICS_ENABLED and sharing_filter_applied_total:
        try:
            sharing_filter_applied_total.labels(object_type=object_type).inc()
        except Exception:
            # Silently fail if metrics collection fails
            pass
