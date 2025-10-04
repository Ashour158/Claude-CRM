# analytics/models.py
from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class Report(CompanyIsolatedModel):
    """
    Custom reports and analytics
    """
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('marketing', 'Marketing Report'),
        ('financial', 'Financial Report'),
        ('inventory', 'Inventory Report'),
        ('customer', 'Customer Report'),
        ('vendor', 'Vendor Report'),
        ('activity', 'Activity Report'),
        ('custom', 'Custom Report'),
    ]
    
    REPORT_FORMATS = [
        ('table', 'Table'),
        ('chart', 'Chart'),
        ('dashboard', 'Dashboard'),
        ('export', 'Export'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Report name")
    description = models.TextField(blank=True, help_text="Report description")
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        help_text="Type of report"
    )
    format_type = models.CharField(
        max_length=20,
        choices=REPORT_FORMATS,
        default='table',
        help_text="Report format"
    )
    
    # Configuration
    query_config = models.JSONField(
        default=dict,
        help_text="Report query configuration"
    )
    filters = models.JSONField(
        default=dict,
        help_text="Report filters"
    )
    columns = models.JSONField(
        default=list,
        help_text="Report columns configuration"
    )
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Chart configuration for chart reports"
    )
    
    # Scheduling
    is_scheduled = models.BooleanField(
        default=False,
        help_text="Is this report scheduled?"
    )
    schedule_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ],
        blank=True,
        help_text="Schedule frequency"
    )
    schedule_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Schedule time"
    )
    last_run = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last run time"
    )
    next_run = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Next scheduled run"
    )
    
    # Access Control
    is_public = models.BooleanField(
        default=False,
        help_text="Is this report public to all users?"
    )
    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='allowed_reports',
        help_text="Users who can access this report"
    )
    
    # Metadata
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='reports')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

class ReportExecution(CompanyIsolatedModel):
    """
    Report execution history
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='executed_reports'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Execution start time"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Execution completion time"
    )
    execution_time = models.DurationField(
        null=True,
        blank=True,
        help_text="Total execution time"
    )
    result_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of results returned"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if execution failed"
    )
    
    # Parameters used for this execution
    parameters = models.JSONField(
        default=dict,
        help_text="Parameters used for this execution"
    )
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.report.name} - {self.status}"

class Dashboard(CompanyIsolatedModel):
    """
    Custom dashboards
    """
    name = models.CharField(max_length=255, help_text="Dashboard name")
    description = models.TextField(blank=True, help_text="Dashboard description")
    
    # Layout configuration
    layout_config = models.JSONField(
        default=dict,
        help_text="Dashboard layout configuration"
    )
    widgets = models.JSONField(
        default=list,
        help_text="Dashboard widgets configuration"
    )
    
    # Access Control
    is_public = models.BooleanField(
        default=False,
        help_text="Is this dashboard public to all users?"
    )
    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='allowed_dashboards',
        help_text="Users who can access this dashboard"
    )
    
    # Metadata
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='dashboards')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return self.name

class KPI(CompanyIsolatedModel):
    """
    Key Performance Indicators
    """
    KPI_TYPES = [
        ('sales', 'Sales KPI'),
        ('marketing', 'Marketing KPI'),
        ('financial', 'Financial KPI'),
        ('operational', 'Operational KPI'),
        ('customer', 'Customer KPI'),
        ('vendor', 'Vendor KPI'),
    ]
    
    KPI_FORMATS = [
        ('number', 'Number'),
        ('percentage', 'Percentage'),
        ('currency', 'Currency'),
        ('duration', 'Duration'),
        ('ratio', 'Ratio'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="KPI name")
    description = models.TextField(blank=True, help_text="KPI description")
    kpi_type = models.CharField(
        max_length=20,
        choices=KPI_TYPES,
        help_text="Type of KPI"
    )
    format_type = models.CharField(
        max_length=20,
        choices=KPI_FORMATS,
        default='number',
        help_text="KPI format"
    )
    
    # Configuration
    calculation_config = models.JSONField(
        default=dict,
        help_text="KPI calculation configuration"
    )
    target_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Target value for this KPI"
    )
    warning_threshold = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Warning threshold"
    )
    critical_threshold = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Critical threshold"
    )
    
    # Current Value
    current_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Current KPI value"
    )
    last_calculated = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last calculation time"
    )
    
    # Metadata
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='kpis')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.get_kpi_type_display()})"
    
    @property
    def status(self):
        """Get KPI status based on thresholds"""
        if not self.current_value:
            return 'unknown'
        
        if self.critical_threshold and self.current_value <= self.critical_threshold:
            return 'critical'
        elif self.warning_threshold and self.current_value <= self.warning_threshold:
            return 'warning'
        elif self.target_value and self.current_value >= self.target_value:
            return 'success'
        else:
            return 'normal'

class DataExport(CompanyIsolatedModel):
    """
    Data export records
    """
    EXPORT_TYPES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('json', 'JSON'),
        ('xml', 'XML'),
    ]
    
    EXPORT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Export name")
    description = models.TextField(blank=True, help_text="Export description")
    export_type = models.CharField(
        max_length=20,
        choices=EXPORT_TYPES,
        help_text="Export format"
    )
    
    # Configuration
    query_config = models.JSONField(
        default=dict,
        help_text="Export query configuration"
    )
    filters = models.JSONField(
        default=dict,
        help_text="Export filters"
    )
    columns = models.JSONField(
        default=list,
        help_text="Export columns"
    )
    
    # Status and Results
    status = models.CharField(
        max_length=20,
        choices=EXPORT_STATUS_CHOICES,
        default='pending'
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Exported file path"
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    record_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of records exported"
    )
    
    # Execution Details
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Export start time"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Export completion time"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Export expiration time"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if export failed"
    )
    
    # Access Control
    is_public = models.BooleanField(
        default=False,
        help_text="Is this export public to all users?"
    )
    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='allowed_exports',
        help_text="Users who can access this export"
    )
    
    # Metadata
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='exports')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_export_type_display()})"
    
    @property
    def is_expired(self):
        """Check if export is expired"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False

class Alert(CompanyIsolatedModel):
    """
    System alerts and notifications
    """
    ALERT_TYPES = [
        ('kpi', 'KPI Alert'),
        ('threshold', 'Threshold Alert'),
        ('anomaly', 'Anomaly Alert'),
        ('system', 'System Alert'),
        ('business', 'Business Alert'),
    ]
    
    ALERT_PRIORITIES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    ALERT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=255, help_text="Alert title")
    message = models.TextField(help_text="Alert message")
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPES,
        help_text="Type of alert"
    )
    priority = models.CharField(
        max_length=20,
        choices=ALERT_PRIORITIES,
        default='medium',
        help_text="Alert priority"
    )
    status = models.CharField(
        max_length=20,
        choices=ALERT_STATUS_CHOICES,
        default='active',
        help_text="Alert status"
    )
    
    # Related Objects
    related_kpi = models.ForeignKey(
        KPI,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts',
        help_text="Related KPI if applicable"
    )
    related_report = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts',
        help_text="Related report if applicable"
    )
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_alerts',
        help_text="User assigned to this alert"
    )
    
    # Timestamps
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When alert was acknowledged"
    )
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts',
        help_text="User who acknowledged the alert"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When alert was resolved"
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
        help_text="User who resolved the alert"
    )
    
    # Additional Information
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"
    
    def acknowledge(self, user):
        """Acknowledge the alert"""
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user
        self.save()
    
    def resolve(self, user):
        """Resolve the alert"""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()
