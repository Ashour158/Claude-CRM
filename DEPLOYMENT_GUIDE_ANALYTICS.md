# Wave 1 Analytics Implementation - Deployment Guide

## Overview
This guide provides instructions for deploying the Wave 1 Analytics Fact Model Foundation.

## What Was Implemented

### 1. Fact Models (analytics/models.py)
Three core fact tables for analytics:
- **FactDealStageTransition** - Tracks deal pipeline movements
- **FactActivity** - Records activity completion and volume
- **FactLeadConversion** - Monitors lead lifecycle events
- **AnalyticsExportJob** - Manages async data exports

All tables include:
- Region tagging for compliance
- GDPR consent flags
- Data retention dates
- Optimized indexes for time-series queries

### 2. ETL Commands
Two management commands for data population and export:

#### Backfill Command
```bash
# Backfill all fact tables for last year
python manage.py backfill_analytics_facts --days=365

# Backfill specific fact type
python manage.py backfill_analytics_facts --fact-type=deals --days=90

# Dry run (no actual changes)
python manage.py backfill_analytics_facts --dry-run
```

#### Export Command
```bash
# Export deal transitions to CSV
python manage.py export_analytics_data \
  --source=deal_transitions \
  --format=csv \
  --days=30 \
  --output=/exports/deals.csv

# Export with region filter
python manage.py export_analytics_data \
  --source=activities \
  --format=json \
  --days=7 \
  --region=NA \
  --output=/exports/activities.json
```

### 3. Analytics APIs
Four API endpoints for KPI analysis:

#### Pipeline Velocity
```http
GET /api/analytics/fact-deal-stage-transitions/pipeline_velocity/?days=30&region=NA
```
Returns:
- Average days in each stage
- Transition counts
- Win rates
- Pipeline value

#### Activity Volume
```http
GET /api/analytics/fact-activities/activity_volume/?days=30&user_id=123
```
Returns:
- Total and completed activities
- Completion rates
- Volume by activity type
- Average duration

#### Conversion Funnel
```http
GET /api/analytics/fact-lead-conversions/conversion_funnel/?days=30&region=EU
```
Returns:
- Conversion rates by stage
- Time-to-conversion metrics
- Lead source attribution

#### Export Jobs
```http
# Create export job
POST /api/analytics/export-jobs/
{
  "name": "Q4 Pipeline Export",
  "export_type": "csv",
  "data_source": "fact_deal_stage_transition",
  "filters": {"days": 90, "region": "NA"}
}

# Check status
GET /api/analytics/export-jobs/{id}/

# Download result
GET /api/analytics/export-jobs/{id}/download/

# Cancel running job
POST /api/analytics/export-jobs/{id}/cancel/
```

## Deployment Steps

### Step 1: Apply Migrations
```bash
# Create migration files
python manage.py makemigrations analytics --skip-checks

# Apply migrations to database
python manage.py migrate analytics
```

### Step 2: Backfill Historical Data
```bash
# Start with a dry run to verify
python manage.py backfill_analytics_facts --days=365 --dry-run

# Run actual backfill
python manage.py backfill_analytics_facts --days=365

# Verify data
python manage.py shell
>>> from analytics.models import FactDealStageTransition, FactActivity, FactLeadConversion
>>> print(f"Deal transitions: {FactDealStageTransition.objects.count()}")
>>> print(f"Activities: {FactActivity.objects.count()}")
>>> print(f"Lead conversions: {FactLeadConversion.objects.count()}")
```

### Step 3: Test API Endpoints
```bash
# Using curl or httpie
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/analytics/fact-deal-stage-transitions/pipeline_velocity/?days=30

# Using Django shell
python manage.py shell
>>> from rest_framework.test import APIClient
>>> client = APIClient()
>>> # ... authenticate ...
>>> response = client.get('/api/analytics/fact-deal-stage-transitions/pipeline_velocity/')
>>> print(response.json())
```

### Step 4: Set Up Scheduled Jobs
Add to your task scheduler (cron, Celery Beat, etc.):

```python
# Example Celery Beat schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'backfill-analytics-daily': {
        'task': 'analytics.tasks.backfill_daily',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'args': ('--days=7',),
    },
    'export-weekly-report': {
        'task': 'analytics.tasks.export_weekly_report',
        'schedule': crontab(day_of_week=1, hour=6, minute=0),  # Monday 6 AM
    },
}
```

Or using cron:
```cron
# Daily backfill at 2 AM
0 2 * * * cd /path/to/project && python manage.py backfill_analytics_facts --days=7

# Weekly export on Monday at 6 AM
0 6 * * 1 cd /path/to/project && python manage.py export_analytics_data --source=deal_transitions --format=csv --days=7
```

### Step 5: Configure Storage for Exports
Update settings.py:
```python
# For local filesystem
MEDIA_ROOT = '/var/www/media'
MEDIA_URL = '/media/'

# For S3 (requires django-storages and boto3)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
AWS_S3_REGION_NAME = 'us-east-1'
```

### Step 6: Run Tests
```bash
# Run all analytics tests
pytest tests/test_analytics_facts.py tests/test_analytics_apis.py -v

# Run with coverage
pytest tests/test_analytics_*.py --cov=analytics --cov-report=html
```

## Monitoring and Maintenance

### Key Metrics to Monitor
1. **Fact Table Growth**
   ```sql
   SELECT 
     'FactDealStageTransition' as table_name,
     COUNT(*) as row_count
   FROM fact_deal_stage_transition
   UNION ALL
   SELECT 'FactActivity', COUNT(*) FROM fact_activity
   UNION ALL
   SELECT 'FactLeadConversion', COUNT(*) FROM fact_lead_conversion;
   ```

2. **ETL Job Success Rate**
   - Monitor management command exit codes
   - Check logs for errors
   - Set up alerts for failures

3. **API Response Times**
   - Monitor p95/p99 latency for KPI endpoints
   - Alert if response time > 2 seconds

4. **Export Job Completion**
   - Track jobs stuck in 'running' state
   - Alert on failed exports

### Data Retention
Implement scheduled cleanup:
```python
# analytics/tasks.py
from django.utils import timezone
from analytics.models import FactDealStageTransition, FactActivity, FactLeadConversion

def cleanup_expired_facts():
    """Delete fact records past retention date"""
    today = timezone.now().date()
    
    for model in [FactDealStageTransition, FactActivity, FactLeadConversion]:
        deleted = model.objects.filter(
            data_retention_date__lt=today
        ).delete()
        print(f"Deleted {deleted[0]} expired {model.__name__} records")
```

Schedule daily:
```cron
0 3 * * * cd /path/to/project && python manage.py run_cleanup_expired_facts
```

## Troubleshooting

### Issue: Slow Backfill
**Solution**: 
- Process in smaller batches: `--days=30` instead of `--days=365`
- Run during off-peak hours
- Consider database indexing: `CREATE INDEX CONCURRENTLY ...`

### Issue: API Timeouts
**Solution**:
- Add caching for frequently-accessed aggregations
- Use database read replicas for analytics queries
- Implement result pagination for large datasets

### Issue: Export Jobs Failing
**Solution**:
- Check disk space: `df -h`
- Verify file permissions on output directory
- Check export job error messages in database

### Issue: Missing Data in Fact Tables
**Solution**:
- Verify source data exists (Deals, Activities, Leads)
- Check backfill command logs for errors
- Re-run backfill for specific date range

## GDPR Compliance

### Data Subject Access Request (DSAR)
To export all analytics data for a user:
```python
from analytics.models import FactDealStageTransition, FactActivity, FactLeadConversion

user_id = 'user-uuid'

deal_facts = FactDealStageTransition.objects.filter(owner_id=user_id)
activity_facts = FactActivity.objects.filter(assigned_to_id=user_id)
lead_facts = FactLeadConversion.objects.filter(owner_id=user_id)

# Export to CSV using export command
```

### Right to be Forgotten
To anonymize/delete user data:
```python
from analytics.models import FactDealStageTransition, FactActivity, FactLeadConversion

user_id = 'user-uuid'

# Option 1: Delete all records
FactDealStageTransition.objects.filter(owner_id=user_id).delete()
FactActivity.objects.filter(assigned_to_id=user_id).delete()
FactLeadConversion.objects.filter(owner_id=user_id).delete()

# Option 2: Anonymize (if required for historical accuracy)
FactActivity.objects.filter(assigned_to_id=user_id).update(
    assigned_to=None,
    subject='[REDACTED]'
)
```

## Performance Tuning

### Database Indexes
All fact tables have optimized indexes, but monitor slow queries:
```sql
-- Find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE query LIKE '%fact_%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Query Optimization Tips
1. Always filter by date range first
2. Use `select_related()` for foreign keys
3. Add `only()` to limit field selection
4. Cache frequent aggregations
5. Use database-level aggregation (`Count`, `Sum`, `Avg`)

## Documentation

See [ANALYTICS_DATA_MODEL.md](./ANALYTICS_DATA_MODEL.md) for:
- Complete fact table schemas
- Data lineage diagrams
- Extension points for custom fact tables
- API usage examples
- Performance considerations

## Support

For issues or questions:
1. Check [ANALYTICS_DATA_MODEL.md](./ANALYTICS_DATA_MODEL.md) documentation
2. Review test files for usage examples
3. Check management command help: `python manage.py backfill_analytics_facts --help`
4. Open a GitHub issue with detailed logs

---

**Version**: 1.0  
**Last Updated**: 2024  
**Status**: Ready for Production
