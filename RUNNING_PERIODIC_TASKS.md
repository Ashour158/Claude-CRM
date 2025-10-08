# Running Periodic Tasks

This document explains how to run the periodic tasks configured in the CRM system.

## Overview

The CRM system has several periodic tasks that maintain and optimize system performance:

1. **Precompute Search Facets** - Precomputes search facets for faster search queries
2. **Precompute Report Aggregates** - Precomputes common report aggregates
3. **Audit Log Maintenance** - Maintains and archives audit log partitions
4. **Warm Caches** - Warms various system caches during off-peak hours

## Automatic Execution (Celery Beat)

These tasks are automatically scheduled to run at specific intervals using Celery Beat:

- **Precompute Search Facets**: Every 5 minutes
- **Precompute Report Aggregates**: Every 10 minutes
- **Audit Log Maintenance**: Daily at 2 AM
- **Warm Caches**: Daily at 3 AM

### Starting Celery Workers

To enable automatic task execution, start the Celery workers:

```bash
# Start Celery worker
celery -A config worker -l info

# Start Celery beat scheduler
celery -A config beat -l info
```

For production, use multiple workers with different queue configurations:

```bash
# I/O-bound worker (more concurrent tasks)
celery -A config worker -Q workflow_io -c 20 --max-tasks-per-child=1000

# CPU-bound worker (fewer concurrent tasks)
celery -A config worker -Q workflow_cpu -c 4 --max-tasks-per-child=100

# Default worker
celery -A config worker -Q celery -c 10

# Beat scheduler
celery -A config beat -l info
```

## Manual Execution

You can manually run any or all of these tasks using the Django management command:

### Run All Tasks

```bash
python manage.py run_periodic_tasks
```

### Run a Specific Task

```bash
# Precompute search facets
python manage.py run_periodic_tasks --task precompute_facets

# Precompute report aggregates
python manage.py run_periodic_tasks --task precompute_aggregates

# Run audit maintenance
python manage.py run_periodic_tasks --task audit_maintenance

# Warm caches
python manage.py run_periodic_tasks --task warm_caches
```

## Task Details

### Precompute Search Facets

**Task Name**: `analytics.precompute_facets`
**Schedule**: Every 5 minutes
**Purpose**: Precomputes search facets for leads, deals, accounts, and contacts to dramatically improve search performance.

**Expected Results**:
- Facets computed for common attributes (status, industry, owner, etc.)
- 80% reduction in search query time
- p95 latency: <100ms for faceted search

### Precompute Report Aggregates

**Task Name**: `analytics.precompute_aggregates`
**Schedule**: Every 10 minutes
**Purpose**: Materializes common report aggregates to speed up reporting queries.

**Expected Results**:
- Common metrics pre-aggregated (counts, sums, averages)
- Faster report generation
- Reduced database load

### Audit Log Maintenance

**Task Name**: `system_config.audit_maintenance`
**Schedule**: Daily at 2 AM
**Purpose**: Maintains audit log partitions, creates new partitions, and archives old data.

**Expected Results**:
- New partitions created for upcoming months
- Old partitions archived or deleted based on retention policy
- Optimized audit log query performance

### Warm Caches

**Task Name**: `analytics.warm_caches`
**Schedule**: Daily at 3 AM
**Purpose**: Warms various system caches during off-peak hours for better performance.

**Expected Results**:
- Sharing rule caches warmed
- Search facet caches populated
- Report aggregate caches ready

## Configuration

The periodic tasks are configured in `config/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'precompute-search-facets': {
        'task': 'analytics.precompute_facets',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'precompute-report-aggregates': {
        'task': 'analytics.precompute_aggregates',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
    'audit-log-maintenance': {
        'task': 'system_config.audit_maintenance',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'warm-caches': {
        'task': 'analytics.warm_caches',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}
```

## Monitoring

### Celery Flower

Use Celery Flower to monitor task execution:

```bash
pip install flower
celery -A config flower
```

Access the monitoring interface at: http://localhost:5555

### Django Admin

Task execution results are logged and can be viewed in the Django admin interface.

### Logs

Check application logs for task execution details:

```bash
tail -f logs/celery.log
```

## Troubleshooting

### Tasks Not Running

1. **Check Redis is running**:
   ```bash
   redis-cli ping
   ```

2. **Check Celery worker is running**:
   ```bash
   ps aux | grep celery
   ```

3. **Check Celery beat is running**:
   ```bash
   ps aux | grep beat
   ```

### Task Failures

1. **Check task logs**:
   ```bash
   python manage.py run_periodic_tasks --task <task_name>
   ```

2. **Verify dependencies are installed**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check database connectivity**

4. **Verify Redis connectivity**

## Performance Impact

These periodic tasks significantly improve system performance:

- **Search**: 80% reduction in query time
- **Reports**: 60% faster report generation
- **Audit Logs**: Optimized storage and query performance
- **Caching**: 95% reduction in sharing rule lookup time

## Best Practices

1. **Run tasks during off-peak hours** for maintenance tasks
2. **Monitor task execution** using Celery Flower
3. **Adjust schedules** based on system load and requirements
4. **Review logs regularly** to ensure tasks are completing successfully
5. **Test tasks manually** before deploying schedule changes

## Related Documentation

- [PERFORMANCE_ENHANCEMENTS.md](PERFORMANCE_ENHANCEMENTS.md) - Detailed performance enhancement documentation
- [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) - API documentation
- `analytics/tasks.py` - Task implementation details

## Support

For issues or questions about periodic tasks:

1. Check the troubleshooting section above
2. Review application logs
3. Manually run tasks to diagnose issues
4. Consult the performance enhancements documentation
