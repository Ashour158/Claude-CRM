# Analytics Evolution - Documentation

## Overview

This document describes the enhanced analytics capabilities added to Claude-CRM, including metrics catalog, time series pipelines, anomaly detection, report scheduling, and data quality validation.

## Features

### 1. Metrics Catalog and Introspection

The metrics catalog provides a centralized registry of all metrics with full lineage tracking and introspection capabilities.

#### Models
- **MetricDefinition**: Defines metrics with calculation formulas, dependencies, and versioning
- **MetricLineage**: Tracks relationships between metrics
- **MetricComputationDAG**: Manages computation order for derived metrics

#### Key Features
- Metric versioning with parent-child relationships
- Dependency graph generation
- Lineage tracking (upstream and downstream)
- Support for base, derived, and aggregate metrics

#### API Endpoints
```
GET    /api/analytics/metrics/                    # List all metrics
POST   /api/analytics/metrics/                    # Create new metric
GET    /api/analytics/metrics/{id}/               # Get metric details
PUT    /api/analytics/metrics/{id}/               # Update metric
DELETE /api/analytics/metrics/{id}/               # Delete metric
GET    /api/analytics/metrics/{id}/lineage/       # Get metric lineage
GET    /api/analytics/metrics/{id}/dependency_graph/  # Get dependency graph
GET    /api/analytics/metrics/catalog/            # Get full metrics catalog
```

#### Example Usage
```python
# Create a base metric
metric = MetricDefinition.objects.create(
    name='total_revenue',
    display_name='Total Revenue',
    category='revenue',
    metric_type='base',
    data_source='sales_orders',
    calculation_formula='SUM(amount)',
    aggregation_method='sum',
    unit='USD',
    owner=user,
    company=company
)

# Create a derived metric
derived_metric = MetricDefinition.objects.create(
    name='revenue_growth',
    display_name='Revenue Growth Rate',
    category='revenue',
    metric_type='derived',
    dependencies=['total_revenue'],
    calculation_formula='(current_revenue - previous_revenue) / previous_revenue',
    parent_metric=metric,
    version=2,
    owner=user,
    company=company
)

# Get lineage
lineage = derived_metric.get_lineage()
```

### 2. Derived Metric Computation Graph (DAG)

The DAG system manages computation order for complex metric dependencies.

#### Features
- Automatic cycle detection
- Topological sorting for execution order
- Versioning support
- Validation before execution

#### API Endpoints
```
GET    /api/analytics/metric-dags/                # List all DAGs
POST   /api/analytics/metric-dags/                # Create new DAG
GET    /api/analytics/metric-dags/{id}/           # Get DAG details
POST   /api/analytics/metric-dags/{id}/validate/  # Validate DAG structure
POST   /api/analytics/metric-dags/{id}/compute/   # Execute DAG computation
```

#### Example Usage
```python
# Create a DAG
dag = MetricComputationDAG.objects.create(
    name='Revenue Metrics DAG',
    dag_definition={
        'nodes': ['base_revenue', 'revenue_growth', 'revenue_forecast'],
        'edges': {
            'base_revenue': ['revenue_growth'],
            'revenue_growth': ['revenue_forecast'],
            'revenue_forecast': []
        }
    },
    company=company
)

# Validate DAG
is_valid, message = dag.validate_dag()

# Get execution order
execution_order = dag.topological_sort()

# Execute DAG
# POST /api/analytics/metric-dags/{id}/compute/
```

### 3. Time Series Pipeline with Snapshot Table

The time series system provides daily rollups with automatic change tracking.

#### Models
- **TimeSeriesSnapshot**: Daily snapshots of metric values with change tracking
- **TimeSeriesPipeline**: Automated pipeline for generating snapshots
- **TimeSeriesAggregation**: Pre-aggregated data for different time periods

#### Features
- Automatic change calculation (absolute and percentage)
- Moving averages (7-day and 30-day)
- Multiple period types (daily, weekly, monthly, quarterly, yearly)
- Data quality scoring

#### API Endpoints
```
GET    /api/analytics/time-series-snapshots/      # List snapshots
POST   /api/analytics/time-series-snapshots/      # Create snapshot
GET    /api/analytics/time-series-snapshots/?metric={id}&start_date={date}&end_date={date}

GET    /api/analytics/time-series-pipelines/      # List pipelines
POST   /api/analytics/time-series-pipelines/      # Create pipeline
POST   /api/analytics/time-series-pipelines/{id}/run/  # Execute pipeline
```

#### Example Usage
```python
# Create a time series pipeline
pipeline = TimeSeriesPipeline.objects.create(
    name='Daily Revenue Pipeline',
    schedule_type='daily',
    schedule_time=datetime.time(0, 0),
    is_active=True,
    company=company
)
pipeline.metrics.add(revenue_metric)

# Create a snapshot
snapshot = TimeSeriesSnapshot.objects.create(
    metric=revenue_metric,
    snapshot_date=date.today(),
    period_type='daily',
    value=Decimal('1000.00'),
    company=company
)

# Changes are calculated automatically
print(f"Previous: {snapshot.previous_value}")
print(f"Change: {snapshot.absolute_change}")
print(f"Percent Change: {snapshot.percent_change}%")
```

### 4. Automated Anomaly Detection

The anomaly detection system monitors KPIs and alerts on unusual patterns.

#### Detection Methods
- **Z-Score**: Statistical outlier detection based on standard deviations
- **IQR**: Interquartile range method for outlier detection
- **Moving Average**: Deviation from moving average threshold
- **Threshold**: Fixed upper/lower bounds

#### Models
- **AnomalyDetectionRule**: Configuration for anomaly detection
- **AnomalyDetection**: Detected anomalies
- **AnomalyAlert**: Alert notifications

#### API Endpoints
```
GET    /api/analytics/anomaly-rules/              # List rules
POST   /api/analytics/anomaly-rules/              # Create rule
POST   /api/analytics/anomaly-rules/{id}/detect/  # Run detection

GET    /api/analytics/anomalies/                  # List anomalies
GET    /api/analytics/anomalies/?status=open&severity=critical
POST   /api/analytics/anomalies/{id}/investigate/ # Mark as investigating
POST   /api/analytics/anomalies/{id}/resolve/     # Resolve anomaly
```

#### Example Usage
```python
# Create anomaly detection rule
rule = AnomalyDetectionRule.objects.create(
    name='Revenue Spike Detection',
    metric=revenue_metric,
    detection_method='zscore',
    zscore_threshold=Decimal('3.0'),
    lookback_period=30,
    alert_enabled=True,
    alert_severity='critical',
    company=company
)
rule.alert_recipients.add(user)

# Detect anomalies
service = AnomalyDetectionService()
anomalies = service.batch_detect(rule, start_date, end_date)
```

### 5. Report Scheduling and Snapshot Store

The report scheduling system supports cron-like scheduling with timezone support.

#### Models
- **ReportSchedule**: Schedule configuration
- **ReportSnapshot**: Stored report results
- **ReportSnapshotAccess**: Access tracking

#### Features
- Multiple schedule types: cron, interval, daily, weekly, monthly
- Timezone-aware scheduling
- Multiple delivery methods: email, API, file storage
- Export formats: PDF, Excel, CSV, JSON
- Automatic retry on failure

#### API Endpoints
```
GET    /api/analytics/report-schedules/           # List schedules
POST   /api/analytics/report-schedules/           # Create schedule
POST   /api/analytics/report-schedules/{id}/execute/  # Execute immediately

GET    /api/analytics/report-snapshots/           # List snapshots
GET    /api/analytics/report-snapshots/{id}/download/  # Download report
```

#### Example Usage
```python
# Create daily report schedule
schedule = ReportSchedule.objects.create(
    report=report,
    name='Daily Sales Report',
    schedule_type='daily',
    schedule_time=datetime.time(9, 0),  # 9 AM
    timezone='America/New_York',
    delivery_method='email',
    export_format='pdf',
    is_active=True,
    company=company
)
schedule.recipients.add(user)

# Calculate next run
next_run = schedule.calculate_next_run()

# Execute schedule
success, snapshot = schedule.execute()
```

### 6. Data Quality Validation Engine

The data quality engine provides comprehensive validation with a rule DSL.

#### Models
- **DataQualityRule**: Validation rule definition
- **DataQualityCheck**: Validation results
- **DataQualityAlert**: Quality issue alerts
- **DataQualityDashboard**: Monitoring dashboard

#### Rule Types
- **Built-in Rules**:
  - `not_null`: Field must not be null
  - `unique`: Field values must be unique
  - `range`: Value must be within range
  - `pattern`: Value must match pattern
  - `foreign_key`: Foreign key must be valid
  - `date_range`: Date must be within range
  - `value_in_list`: Value must be in allowed list

- **SQL Rules**: Custom SQL queries
- **Python Rules**: Python expressions (safe evaluation)

#### Features
- Incremental evaluation (only check new/changed records)
- Configurable failure thresholds
- Severity levels: info, warning, error, critical
- Automated alerting
- Failed records sampling

#### API Endpoints
```
GET    /api/analytics/data-quality-rules/         # List rules
POST   /api/analytics/data-quality-rules/         # Create rule
POST   /api/analytics/data-quality-rules/{id}/evaluate/  # Evaluate rule

GET    /api/analytics/data-quality-checks/        # List checks
GET    /api/analytics/data-quality-alerts/        # List alerts
POST   /api/analytics/data-quality-alerts/{id}/acknowledge/
POST   /api/analytics/data-quality-alerts/{id}/resolve/

GET    /api/analytics/data-quality-dashboards/    # List dashboards
GET    /api/analytics/data-quality-dashboards/{id}/summary/  # Get summary
```

#### Example Usage
```python
# Create a data quality rule
rule = DataQualityRule.objects.create(
    name='Email Completeness',
    description='All leads must have an email',
    category='completeness',
    target_model='Lead',
    target_fields=['email'],
    rule_type='builtin',
    builtin_rule='not_null',
    severity='error',
    failure_threshold_percentage=Decimal('5.0'),
    evaluation_frequency='daily',
    is_incremental=True,
    alert_enabled=True,
    owner=user,
    company=company
)
rule.alert_recipients.add(user)

# Evaluate rule
result = rule.evaluate(incremental=True)

# Create dashboard
dashboard = DataQualityDashboard.objects.create(
    name='Lead Data Quality',
    owner=user,
    company=company
)
dashboard.rules.add(rule)

# Get summary
summary = dashboard.get_summary()
```

## Testing

Run the comprehensive test suite:

```bash
# Run all analytics tests
pytest analytics/tests/test_analytics_extended.py -v

# Run specific test classes
pytest analytics/tests/test_analytics_extended.py::TestMetricsCatalog -v
pytest analytics/tests/test_analytics_extended.py::TestAnomalyDetection -v
pytest analytics/tests/test_analytics_extended.py::TestDataQuality -v
```

## Configuration

### Settings

Add to your Django settings:

```python
# Analytics configuration
ANALYTICS_CACHE_TIMEOUT = 3600  # Default cache timeout for metrics
ANALYTICS_SNAPSHOT_RETENTION_DAYS = 365  # How long to keep snapshots
ANALYTICS_ALERT_EMAIL_FROM = 'alerts@example.com'
```

### URL Configuration

Include the analytics URLs in your main urls.py:

```python
from django.urls import path, include

urlpatterns = [
    # ... other patterns
    path('api/analytics/', include('analytics.urls_extended')),
]
```

## Best Practices

1. **Metrics Catalog**:
   - Use clear, descriptive metric names
   - Document calculation formulas
   - Version metrics when changing formulas
   - Keep dependency graphs acyclic

2. **Time Series**:
   - Run pipelines during off-peak hours
   - Monitor data quality scores
   - Set appropriate retention policies

3. **Anomaly Detection**:
   - Start with threshold-based rules
   - Tune z-score thresholds based on data
   - Use appropriate lookback periods
   - Review and mark false positives

4. **Report Scheduling**:
   - Use appropriate timezone settings
   - Test schedules before enabling
   - Monitor execution failures
   - Set reasonable retry limits

5. **Data Quality**:
   - Start with completeness rules
   - Use incremental evaluation for large datasets
   - Set realistic failure thresholds
   - Review failed records regularly

## Future Enhancements

- Real-time streaming metrics
- Machine learning-based anomaly detection
- Advanced metric forecasting
- Natural language query interface
- Custom visualization builders
- Data lineage visualization
- Automated root cause analysis
- Integration with BI tools
