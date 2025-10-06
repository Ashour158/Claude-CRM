# Analytics Data Model Documentation

## Overview

This document describes the analytics data model, ETL patterns, compliance approach, and extension points for the CRM analytics system. The analytics system is built on a fact-based data warehouse pattern to enable high-performance reporting and analysis.

## Architecture

### Fact-Based Analytics
The analytics system uses three core fact tables to track key business events:

1. **FactDealStageTransition** - Pipeline velocity and stage transitions
2. **FactActivity** - Activity volume and productivity metrics
3. **FactLeadConversion** - Lead conversion funnel tracking

### Design Principles

- **Immutable Facts**: Fact records are immutable snapshots of events as they occurred
- **Time-Series Optimized**: All fact tables are indexed by date for efficient time-based queries
- **Denormalized**: Key dimensions are denormalized into facts for query performance
- **Regional Compliance**: All facts include region tagging for GDPR and data residency compliance

## Fact Tables

### FactDealStageTransition

Tracks every stage change in the sales pipeline to enable velocity analysis.

**Purpose**: Pipeline velocity, stage duration analysis, conversion rates between stages

**Key Fields**:
- `deal` - Foreign key to Deal
- `from_stage` - Previous stage (empty for new deals)
- `to_stage` - Current stage after transition
- `transition_date` - When the transition occurred
- `days_in_previous_stage` - Time spent in previous stage
- `deal_amount` - Deal value at transition time
- `probability` - Win probability at transition
- `weighted_amount` - Amount × probability
- `owner` - Deal owner at transition time
- `region` - Geographic region for compliance
- `gdpr_consent` - GDPR consent flag
- `data_retention_date` - Compliance deletion date

**Indexes**:
- `(transition_date, to_stage)` - Stage transition timeline queries
- `(deal, transition_date)` - Deal history queries
- `(region, transition_date)` - Regional compliance queries

**Use Cases**:
- Calculate average days in each stage
- Measure pipeline velocity (deals per day/week/month)
- Analyze conversion rates between stages
- Identify bottlenecks in the sales process
- Track changes in deal value over time

### FactActivity

Records completed activities for productivity and engagement analysis.

**Purpose**: Activity volume tracking, team productivity, customer engagement metrics

**Key Fields**:
- `activity_type` - Type (call, email, meeting, demo, etc.)
- `activity_date` - When activity occurred
- `subject` - Activity subject/title
- `duration_minutes` - Activity duration
- `status` - Activity status
- `related_entity_type` - Type of related entity (Account, Contact, Deal, Lead)
- `related_entity_id` - ID of related entity
- `assigned_to` - User who performed the activity
- `is_completed` - Completion flag
- `is_overdue` - Overdue flag
- `completion_date` - When completed
- `region` - Geographic region
- `gdpr_consent` - GDPR consent flag
- `data_retention_date` - Compliance deletion date

**Indexes**:
- `(activity_date, activity_type)` - Activity timeline by type
- `(assigned_to, activity_date)` - User productivity queries
- `(region, activity_date)` - Regional compliance queries
- `(is_completed, activity_date)` - Completion tracking

**Use Cases**:
- Track activity volume by type and user
- Calculate activity completion rates
- Measure average activity duration
- Analyze customer engagement patterns
- Monitor team productivity

### FactLeadConversion

Tracks lead lifecycle events for funnel analysis.

**Purpose**: Conversion funnel tracking, lead velocity, source attribution

**Key Fields**:
- `lead` - Foreign key to Lead
- `event_type` - Type of event (created, qualified, converted, lost)
- `event_date` - When event occurred
- `lead_status` - Lead status at event time
- `lead_source` - Lead source (for attribution)
- `lead_score` - Lead score at event time
- `days_since_creation` - Days since lead was created
- `days_in_previous_status` - Time in previous status
- `converted_to_account` - Resulting account (if converted)
- `converted_to_deal` - Resulting deal (if converted)
- `conversion_value` - Value of resulting opportunity
- `owner` - Lead owner
- `region` - Geographic region
- `gdpr_consent` - GDPR consent flag
- `data_retention_date` - Compliance deletion date

**Indexes**:
- `(event_date, event_type)` - Funnel timeline queries
- `(lead, event_date)` - Lead history queries
- `(region, event_date)` - Regional compliance queries
- `(owner, event_date)` - Owner performance queries

**Use Cases**:
- Calculate conversion rates (created → qualified → converted)
- Measure time-to-conversion
- Analyze lead source effectiveness
- Track lead velocity through funnel
- Measure lead scoring accuracy

## ETL Patterns

### Backfill Pattern

The `backfill_analytics_facts` management command populates fact tables from historical data:

```bash
# Backfill all fact tables for last 365 days
python manage.py backfill_analytics_facts --days=365

# Backfill specific fact table
python manage.py backfill_analytics_facts --fact-type=deals --days=90

# Dry run to preview changes
python manage.py backfill_analytics_facts --dry-run
```

**Strategy**:
- Reads from source tables (Deals, Activities, Leads)
- Creates fact records for significant events
- Uses `get_or_create` to avoid duplicates
- Can be run multiple times safely (idempotent)

### Ongoing ETL Pattern

For ongoing fact creation, implement signal handlers or post-save hooks:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from deals.models import Deal
from analytics.models import FactDealStageTransition

@receiver(post_save, sender=Deal)
def create_deal_stage_transition(sender, instance, created, **kwargs):
    if created or instance.stage != instance._original_stage:
        FactDealStageTransition.objects.create(
            company=instance.company,
            deal=instance,
            from_stage=instance._original_stage if not created else '',
            to_stage=instance.stage,
            transition_date=timezone.now(),
            deal_amount=instance.amount,
            probability=instance.probability,
            weighted_amount=instance.weighted_amount,
            owner=instance.owner,
            region=instance.region,
            gdpr_consent=True
        )
```

### Data Lineage

```
Source Systems          Fact Tables                Analytics APIs
─────────────────      ─────────────              ──────────────

Deals                  FactDealStage              /api/analytics/
  └─> stage changes    Transition                   fact-deal-stage-transitions/
                         └─> pipeline_velocity/
                         
Activities             FactActivity               /api/analytics/
  └─> completed          └─> activity_volume/       fact-activities/
      activities                                    
                         
Leads                  FactLeadConversion         /api/analytics/
  └─> status changes     └─> conversion_funnel/     fact-lead-conversions/
```

## Analytics APIs

### Core KPI Endpoints

#### Pipeline Velocity
**Endpoint**: `GET /api/analytics/fact-deal-stage-transitions/pipeline_velocity/`

**Parameters**:
- `days` - Number of days (default: 30)
- `region` - Filter by region (optional)

**Returns**:
- Average days in each stage
- Transition counts by stage
- Total pipeline value
- Win rate

**Example**:
```json
{
  "period_days": 30,
  "start_date": "2024-01-01",
  "stage_metrics": [
    {
      "to_stage": "qualification",
      "avg_days": 7.5,
      "transition_count": 45,
      "total_value": "450000.00"
    }
  ],
  "total_transitions": 234,
  "won_deals": 23,
  "win_rate": 9.83
}
```

#### Activity Volume
**Endpoint**: `GET /api/analytics/fact-activities/activity_volume/`

**Parameters**:
- `days` - Number of days (default: 30)
- `user_id` - Filter by user (optional)
- `region` - Filter by region (optional)

**Returns**:
- Total and completed activity counts
- Completion rate
- Volume by activity type
- Average duration by type

**Example**:
```json
{
  "period_days": 30,
  "start_date": "2024-01-01",
  "total_activities": 567,
  "completed_activities": 489,
  "completion_rate": 86.25,
  "volume_by_type": [
    {
      "activity_type": "call",
      "total_count": 234,
      "completed_count": 198,
      "avg_duration": 15.5
    }
  ]
}
```

#### Conversion Funnel
**Endpoint**: `GET /api/analytics/fact-lead-conversions/conversion_funnel/`

**Parameters**:
- `days` - Number of days (default: 30)
- `region` - Filter by region (optional)

**Returns**:
- Funnel metrics by event type
- Conversion rates
- Average time-to-conversion
- Total conversion value

**Example**:
```json
{
  "period_days": 30,
  "start_date": "2024-01-01",
  "funnel_metrics": [
    {
      "event_type": "created",
      "event_count": 150,
      "avg_days_since_creation": 0,
      "total_value": null
    },
    {
      "event_type": "converted",
      "event_count": 23,
      "avg_days_since_creation": 45.2,
      "total_value": "345000.00"
    }
  ],
  "conversion_rates": {
    "created_to_qualified": 35.6,
    "qualified_to_converted": 42.9,
    "created_to_converted": 15.3
  }
}
```

## Export Functionality

### Export Job Pattern

Analytics data can be exported asynchronously for large datasets:

1. **Create Export Job**:
```http
POST /api/analytics/export-jobs/
{
  "name": "Q4 Pipeline Analysis",
  "export_type": "csv",
  "data_source": "fact_deal_stage_transition",
  "filters": {
    "start_date": "2024-10-01",
    "end_date": "2024-12-31",
    "region": "NA"
  }
}
```

2. **Check Status**:
```http
GET /api/analytics/export-jobs/{id}/
```

3. **Download Result**:
```http
GET /api/analytics/export-jobs/{id}/download/
```

4. **Cancel Job** (if needed):
```http
POST /api/analytics/export-jobs/{id}/cancel/
```

### Management Command Export

For scheduled or batch exports:

```bash
# Export deal transitions to CSV
python manage.py export_analytics_data \
  --source=deal_transitions \
  --format=csv \
  --days=90 \
  --output=/exports/deals_q4.csv \
  --region=NA

# Export to JSON
python manage.py export_analytics_data \
  --source=activities \
  --format=json \
  --days=30 \
  --output=/exports/activities.json
```

## GDPR and Compliance

### Region Tagging

All fact tables include a `region` field for geographic segmentation:
- Used for data residency requirements
- Enables region-specific queries and exports
- Supports multi-region deployments

### GDPR Consent

All fact tables include:
- `gdpr_consent` - Boolean flag for consent tracking
- `data_retention_date` - When record should be deleted

### Data Retention

Implement a scheduled task to purge expired records:

```python
# Example: Delete records past retention date
from analytics.models import FactDealStageTransition, FactActivity, FactLeadConversion
from django.utils import timezone

for model in [FactDealStageTransition, FactActivity, FactLeadConversion]:
    model.objects.filter(
        data_retention_date__lt=timezone.now().date()
    ).delete()
```

### Right to be Forgotten

When processing GDPR deletion requests:
1. Identify all fact records for the data subject
2. Either delete or anonymize records based on retention policy
3. Log the deletion for audit trail

```python
# Example: Anonymize user data in facts
FactActivity.objects.filter(assigned_to=user).update(
    assigned_to=None,
    subject='[REDACTED]',
    outcome='[REDACTED]'
)
```

## Extension Points

### Adding New Fact Tables

To add a new fact table:

1. **Define Model** in `analytics/models.py`:
```python
class FactCustomerEngagement(CompanyIsolatedModel):
    customer = models.ForeignKey(Account, on_delete=models.CASCADE)
    engagement_date = models.DateTimeField(db_index=True)
    engagement_type = models.CharField(max_length=50)
    score = models.IntegerField()
    region = models.CharField(max_length=100, blank=True, db_index=True)
    gdpr_consent = models.BooleanField(default=False)
    data_retention_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'fact_customer_engagement'
        indexes = [
            models.Index(fields=['engagement_date', 'engagement_type']),
            models.Index(fields=['region', 'engagement_date']),
        ]
```

2. **Create Serializer** in `analytics/serializers.py`:
```python
class FactCustomerEngagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactCustomerEngagement
        fields = '__all__'
```

3. **Create ViewSet** in `analytics/views.py`:
```python
class FactCustomerEngagementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FactCustomerEngagement.objects.all()
    serializer_class = FactCustomerEngagementSerializer
    
    @action(detail=False, methods=['get'])
    def engagement_trends(self, request):
        # Custom analytics endpoint
        pass
```

4. **Register URL** in `analytics/urls.py`:
```python
router.register(r'fact-customer-engagement', views.FactCustomerEngagementViewSet)
```

5. **Add ETL Logic** in management command or signals

### Adding Custom KPI Endpoints

Add custom action methods to fact viewsets:

```python
@action(detail=False, methods=['get'])
def custom_metric(self, request):
    # Custom calculation logic
    result = self.get_queryset().aggregate(
        total=Sum('amount'),
        avg=Avg('score')
    )
    return Response(result)
```

### Aggregation Tables

For frequently-accessed aggregations, create materialized views or summary tables:

```python
class DailySalesMetrics(CompanyIsolatedModel):
    """Pre-aggregated daily metrics for fast dashboard queries"""
    date = models.DateField(db_index=True)
    total_deals = models.IntegerField()
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    won_deals = models.IntegerField()
    lost_deals = models.IntegerField()
    region = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ('company', 'date', 'region')
```

Update via nightly batch job or incremental refresh.

## Performance Considerations

### Indexing Strategy

All fact tables use composite indexes optimized for common query patterns:
- Time-based queries (always include date field first)
- Dimension filtering (region, owner, type)
- Aggregation queries (status, completion flags)

### Query Optimization

- Use `select_related()` for foreign key lookups
- Use `prefetch_related()` for many-to-many relationships
- Add `only()` to limit field selection
- Use database-level aggregations (`Count`, `Sum`, `Avg`)
- Cache frequently-accessed aggregations

### Data Volume Management

- Implement data retention policies (e.g., keep 2 years)
- Archive old data to separate tables/database
- Partition tables by date for large volumes
- Use read replicas for analytics queries

## Testing

### Unit Tests

Test fact creation logic:
```python
def test_fact_deal_transition_creation():
    deal = create_test_deal()
    fact = FactDealStageTransition.objects.create(
        company=deal.company,
        deal=deal,
        to_stage='qualification',
        transition_date=timezone.now()
    )
    assert fact.to_stage == 'qualification'
```

### Integration Tests

Test ETL commands:
```python
def test_backfill_command():
    # Create test data
    create_test_deals(count=10)
    
    # Run backfill
    call_command('backfill_analytics_facts', '--fact-type=deals')
    
    # Verify facts created
    assert FactDealStageTransition.objects.count() >= 10
```

### API Tests

Test analytics endpoints:
```python
def test_pipeline_velocity_api():
    response = client.get('/api/analytics/fact-deal-stage-transitions/pipeline_velocity/')
    assert response.status_code == 200
    assert 'stage_metrics' in response.json()
```

## Monitoring

### Key Metrics to Monitor

- ETL job completion time
- Fact table row counts and growth rate
- API response times for analytics endpoints
- Export job success/failure rates
- Cache hit rates for aggregations

### Alerts

Set up alerts for:
- ETL job failures
- Fact table growth anomalies
- Slow query performance (>2s)
- Export job failures
- Data retention policy violations

## Future Enhancements

### Planned Features

1. **Real-time Streaming**: Use Kafka/event sourcing for real-time fact creation
2. **Machine Learning**: Integrate ML models for predictive analytics
3. **Data Warehouse**: Export to dedicated OLAP database (e.g., Redshift, BigQuery)
4. **Advanced Visualizations**: Add chart/graph rendering APIs
5. **Scheduled Reports**: Automated report generation and distribution
6. **Anomaly Detection**: Alert on unusual patterns in metrics

### Extension Areas

- Custom dimension tables for flexible slicing/dicing
- Slowly Changing Dimensions (SCD) for historical accuracy
- Fact table snapshots for point-in-time analysis
- Cross-company benchmarking (anonymized)
- Natural language query interface

## Support and Maintenance

### Common Operations

**Rebuild fact tables**:
```bash
python manage.py backfill_analytics_facts --fact-type=all --days=730
```

**Export for analysis**:
```bash
python manage.py export_analytics_data --source=deal_transitions --format=csv
```

**Check fact table sizes**:
```sql
SELECT 
  table_name,
  pg_size_pretty(pg_total_relation_size(table_name::regclass)) AS size
FROM information_schema.tables
WHERE table_schema = 'public' AND table_name LIKE 'fact_%';
```

### Troubleshooting

**Slow queries**: Check indexes, add caching, use read replicas

**Data inconsistencies**: Re-run backfill with appropriate date range

**Missing facts**: Check ETL job logs, verify signal handlers are firing

**Export failures**: Check disk space, file permissions, timeout settings

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Maintained By**: Analytics Team
