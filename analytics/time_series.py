# analytics/time_series.py
# Time series pipeline with daily rollups and change tracking

from django.db import models
from core.models import CompanyIsolatedModel
from analytics.metrics_catalog import MetricDefinition
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal


class TimeSeriesSnapshot(CompanyIsolatedModel):
    """
    Daily rollup snapshots for metrics with change tracking
    """
    # Metric reference
    metric = models.ForeignKey(
        MetricDefinition,
        on_delete=models.CASCADE,
        related_name='time_series_snapshots'
    )
    
    # Time period
    snapshot_date = models.DateField()
    period_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ],
        default='daily'
    )
    
    # Metric values
    value = models.DecimalField(
        max_digits=20,
        decimal_places=4
    )
    previous_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    
    # Change tracking
    absolute_change = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    percent_change = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    
    # Statistical measures
    moving_average_7d = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    moving_average_30d = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    
    # Metadata
    computation_timestamp = models.DateTimeField(auto_now_add=True)
    data_quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        help_text="Data quality score (0-100)"
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'time_series_snapshot'
        ordering = ['-snapshot_date']
        unique_together = ('metric', 'snapshot_date', 'period_type')
        indexes = [
            models.Index(fields=['metric', 'snapshot_date']),
            models.Index(fields=['snapshot_date', 'period_type']),
        ]
    
    def __str__(self):
        return f"{self.metric.name} - {self.snapshot_date}"
    
    def calculate_changes(self):
        """
        Calculate absolute and percent changes from previous value
        """
        if self.previous_value is not None:
            self.absolute_change = self.value - self.previous_value
            
            if self.previous_value != 0:
                self.percent_change = (
                    (self.value - self.previous_value) / self.previous_value
                ) * Decimal('100')
    
    def calculate_moving_averages(self):
        """
        Calculate moving averages
        """
        # Get previous snapshots
        snapshots_7d = TimeSeriesSnapshot.objects.filter(
            metric=self.metric,
            snapshot_date__gte=self.snapshot_date - timedelta(days=7),
            snapshot_date__lte=self.snapshot_date,
            period_type=self.period_type,
            company=self.company
        ).order_by('-snapshot_date')[:7]
        
        snapshots_30d = TimeSeriesSnapshot.objects.filter(
            metric=self.metric,
            snapshot_date__gte=self.snapshot_date - timedelta(days=30),
            snapshot_date__lte=self.snapshot_date,
            period_type=self.period_type,
            company=self.company
        ).order_by('-snapshot_date')[:30]
        
        # Calculate 7-day moving average
        if snapshots_7d.exists():
            values_7d = [s.value for s in snapshots_7d]
            self.moving_average_7d = sum(values_7d) / len(values_7d)
        
        # Calculate 30-day moving average
        if snapshots_30d.exists():
            values_30d = [s.value for s in snapshots_30d]
            self.moving_average_30d = sum(values_30d) / len(values_30d)
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically calculate changes and moving averages
        """
        # Get previous snapshot
        try:
            previous_snapshot = TimeSeriesSnapshot.objects.filter(
                metric=self.metric,
                snapshot_date__lt=self.snapshot_date,
                period_type=self.period_type,
                company=self.company
            ).order_by('-snapshot_date').first()
            
            if previous_snapshot:
                self.previous_value = previous_snapshot.value
        except TimeSeriesSnapshot.DoesNotExist:
            pass
        
        # Calculate changes
        self.calculate_changes()
        
        super().save(*args, **kwargs)
        
        # Calculate moving averages after save
        self.calculate_moving_averages()
        super().save(update_fields=['moving_average_7d', 'moving_average_30d'])


class TimeSeriesPipeline(CompanyIsolatedModel):
    """
    Configuration for time series data pipeline
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Pipeline configuration
    metrics = models.ManyToManyField(
        MetricDefinition,
        related_name='pipelines'
    )
    
    # Schedule
    schedule_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('hourly', 'Hourly'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='daily'
    )
    schedule_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time of day to run (for daily schedules)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    retry_on_failure = models.BooleanField(default=True)
    max_retries = models.IntegerField(default=3)
    
    class Meta:
        db_table = 'time_series_pipeline'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def run_pipeline(self):
        """
        Execute the pipeline to generate snapshots
        """
        from analytics.services import TimeSeriesService
        
        service = TimeSeriesService()
        results = []
        
        for metric in self.metrics.all():
            try:
                snapshot = service.create_snapshot(
                    metric=metric,
                    snapshot_date=timezone.now().date()
                )
                results.append({
                    'metric': metric.name,
                    'success': True,
                    'snapshot_id': snapshot.id
                })
            except Exception as e:
                results.append({
                    'metric': metric.name,
                    'success': False,
                    'error': str(e)
                })
        
        self.last_run = timezone.now()
        self.save(update_fields=['last_run'])
        
        return results


class TimeSeriesAggregation(CompanyIsolatedModel):
    """
    Pre-aggregated time series data for different time periods
    """
    metric = models.ForeignKey(
        MetricDefinition,
        on_delete=models.CASCADE,
        related_name='aggregations'
    )
    
    # Time period
    period_start = models.DateField()
    period_end = models.DateField()
    period_type = models.CharField(
        max_length=20,
        choices=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ]
    )
    
    # Aggregated values
    sum_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    avg_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    min_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    max_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    count = models.IntegerField(default=0)
    
    # Statistical measures
    std_dev = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    variance = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'time_series_aggregation'
        ordering = ['-period_end']
        unique_together = ('metric', 'period_start', 'period_end', 'period_type')
    
    def __str__(self):
        return f"{self.metric.name} - {self.period_start} to {self.period_end}"
