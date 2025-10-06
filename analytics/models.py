# analytics/models.py
# Analytics and reporting models

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
from crm.models import Account, Contact, Lead
from deals.models import Deal
from sales.models import SalesOrder, Invoice
import uuid

User = get_user_model()

class Dashboard(CompanyIsolatedModel):
    """User dashboards for analytics"""
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    
    # Dashboard configuration
    layout = models.JSONField(default=dict, help_text="Dashboard layout configuration")
    widgets = models.JSONField(default=list, help_text="Dashboard widgets")
    
    # Access control
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_dashboards'
    )
    shared_with = models.ManyToManyField(
        User,
        blank=True,
        related_name='shared_dashboards'
    )
    
    class Meta:
        db_table = 'dashboard'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Report(CompanyIsolatedModel):
    """Custom reports"""
    
    REPORT_TYPES = [
        ('table', 'Table'),
        ('chart', 'Chart'),
        ('pivot', 'Pivot Table'),
        ('summary', 'Summary'),
    ]
    
    CHART_TYPES = [
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        default='table'
    )
    chart_type = models.CharField(
        max_length=20,
        choices=CHART_TYPES,
        blank=True
    )
    
    # Report Configuration
    data_source = models.CharField(
        max_length=100,
        help_text="Data source (e.g., 'accounts', 'deals', 'sales')"
    )
    filters = models.JSONField(
        default=dict,
        help_text="Report filters"
    )
    columns = models.JSONField(
        default=list,
        help_text="Report columns"
    )
    grouping = models.JSONField(
        default=list,
        help_text="Grouping configuration"
    )
    sorting = models.JSONField(
        default=list,
        help_text="Sorting configuration"
    )
    
    # Access Control
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_reports'
    )
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(
        User,
        blank=True,
        related_name='shared_reports'
    )
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ],
        blank=True
    )
    schedule_time = models.TimeField(null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'report'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class KPI(CompanyIsolatedModel):
    """Key Performance Indicators"""
    
    KPI_TYPES = [
        ('revenue', 'Revenue'),
        ('leads', 'Leads'),
        ('conversion', 'Conversion Rate'),
        ('deals', 'Deals'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    kpi_type = models.CharField(
        max_length=20,
        choices=KPI_TYPES,
        default='custom'
    )
    
    # KPI Configuration
    formula = models.TextField(help_text="KPI calculation formula")
    target_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    unit = models.CharField(max_length=50, default='')
    
    # Time Period
    period_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ],
        default='monthly'
    )
    
    # Access Control
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_kpis'
    )
    is_public = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'kpi'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class KPIMeasurement(CompanyIsolatedModel):
    """KPI measurements over time"""
    
    kpi = models.ForeignKey(
        KPI,
        on_delete=models.CASCADE,
        related_name='measurements'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    value = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    target_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    variance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Variance from target"
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'kpi_measurement'
        ordering = ['-period_end']
        unique_together = ('kpi', 'period_start', 'period_end')
    
    def __str__(self):
        return f"{self.kpi.name} - {self.period_start} to {self.period_end}"

class SalesForecast(CompanyIsolatedModel):
    """Sales forecasting data"""
    
    FORECAST_TYPES = [
        ('pipeline', 'Pipeline Forecast'),
        ('revenue', 'Revenue Forecast'),
        ('deals', 'Deals Forecast'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    forecast_type = models.CharField(
        max_length=20,
        choices=FORECAST_TYPES,
        default='pipeline'
    )
    
    # Forecast Period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Forecast Data
    forecasted_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    confidence_level = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50.00,
        help_text="Confidence level percentage (0-100)"
    )
    
    # Methodology
    methodology = models.CharField(
        max_length=100,
        help_text="Forecast methodology used"
    )
    assumptions = models.TextField(blank=True)
    
    # Access Control
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_forecasts'
    )
    
    class Meta:
        db_table = 'sales_forecast'
        ordering = ['-period_end']
    
    def __str__(self):
        return f"{self.name} - {self.period_start} to {self.period_end}"

class ActivityAnalytics(CompanyIsolatedModel):
    """Activity analytics and metrics"""
    
    # Time Period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Activity Metrics
    total_activities = models.IntegerField(default=0)
    completed_activities = models.IntegerField(default=0)
    overdue_activities = models.IntegerField(default=0)
    
    # Activity Types
    calls_count = models.IntegerField(default=0)
    emails_count = models.IntegerField(default=0)
    meetings_count = models.IntegerField(default=0)
    demos_count = models.IntegerField(default=0)
    
    # Performance Metrics
    completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Activity completion rate percentage"
    )
    average_duration = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Average activity duration in minutes"
    )
    
    # User Metrics
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_analytics'
    )
    
    class Meta:
        db_table = 'activity_analytics'
        ordering = ['-period_end']
        unique_together = ('user', 'period_start', 'period_end')
    
    def __str__(self):
        return f"{self.user.email} - {self.period_start} to {self.period_end}"

class SalesAnalytics(CompanyIsolatedModel):
    """Sales analytics and metrics"""
    
    # Time Period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Revenue Metrics
    total_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    recurring_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    new_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Deal Metrics
    total_deals = models.IntegerField(default=0)
    won_deals = models.IntegerField(default=0)
    lost_deals = models.IntegerField(default=0)
    open_deals = models.IntegerField(default=0)
    
    # Conversion Metrics
    win_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Win rate percentage"
    )
    average_deal_size = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    average_sales_cycle = models.IntegerField(
        default=0,
        help_text="Average sales cycle in days"
    )
    
    # Pipeline Metrics
    pipeline_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    weighted_pipeline_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # User Metrics
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sales_analytics'
    )
    
    class Meta:
        db_table = 'sales_analytics'
        ordering = ['-period_end']
        unique_together = ('user', 'period_start', 'period_end')
    
    def __str__(self):
        return f"{self.user.email} - {self.period_start} to {self.period_end}"

class LeadAnalytics(CompanyIsolatedModel):
    """Lead analytics and metrics"""
    
    # Time Period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Lead Metrics
    total_leads = models.IntegerField(default=0)
    new_leads = models.IntegerField(default=0)
    qualified_leads = models.IntegerField(default=0)
    converted_leads = models.IntegerField(default=0)
    
    # Conversion Metrics
    lead_to_opportunity_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Lead to opportunity conversion rate"
    )
    lead_to_customer_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Lead to customer conversion rate"
    )
    
    # Source Metrics
    website_leads = models.IntegerField(default=0)
    referral_leads = models.IntegerField(default=0)
    cold_call_leads = models.IntegerField(default=0)
    trade_show_leads = models.IntegerField(default=0)
    email_campaign_leads = models.IntegerField(default=0)
    social_media_leads = models.IntegerField(default=0)
    
    # User Metrics
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lead_analytics'
    )
    
    class Meta:
        db_table = 'lead_analytics'
        ordering = ['-period_end']
        unique_together = ('user', 'period_start', 'period_end')
    
    def __str__(self):
        return f"{self.user.email} - {self.period_start} to {self.period_end}"
# Phase 4+ Analytics Models

class FactWorkflowRun(CompanyIsolatedModel):
    """Fact table for workflow run analytics"""
    
    workflow_id = models.UUIDField(db_index=True)
    workflow_name = models.CharField(max_length=255)
    run_id = models.UUIDField(db_index=True)
    
    # Execution metrics
    success = models.BooleanField(default=False)
    duration_ms = models.IntegerField(help_text="Execution duration in milliseconds")
    
    # Timing
    executed_date = models.DateField(db_index=True)
    executed_at = models.DateTimeField()
    
    # Context
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    trigger_type = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'fact_workflow_run'
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['company', 'executed_date']),
            models.Index(fields=['workflow_id', '-executed_date']),
            models.Index(fields=['success', '-executed_date']),
        ]
    
    def __str__(self):
        return f"Workflow {self.workflow_name} - {self.executed_at}"

class LeadScoreCache(CompanyIsolatedModel):
    """Cached lead scoring with explanation"""
    
    lead = models.OneToOneField(
        Lead,
        on_delete=models.CASCADE,
        related_name='score_cache'
    )
    
    # Score details
    total_score = models.IntegerField(default=0, help_text="Total lead score (0-100)")
    score_components = models.JSONField(
        default=dict,
        help_text="Score breakdown by component"
    )
    explanation = models.JSONField(
        default=dict,
        help_text="Detailed explanation of score calculation"
    )
    
    # Feature values
    status_weight = models.IntegerField(default=0)
    recent_activity_count = models.IntegerField(default=0)
    days_since_creation = models.IntegerField(default=0)
    custom_field_weights = models.JSONField(
        default=dict,
        help_text="Custom field contribution to score"
    )
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now=True)
    score_version = models.CharField(max_length=20, default='v2')
    
    class Meta:
        db_table = 'lead_score_cache'
        indexes = [
            models.Index(fields=['company', '-total_score']),
            models.Index(fields=['-calculated_at']),
        ]
    
    def __str__(self):
        return f"Lead {self.lead.id} - Score: {self.total_score}"
