# analytics/report_scheduling.py
# Report scheduling and snapshot store with cron-like scheduling

from django.db import models
from core.models import CompanyIsolatedModel, User
from analytics.models import Report
from django.utils import timezone
import pytz
from datetime import datetime, timedelta


class ReportSchedule(CompanyIsolatedModel):
    """
    Scheduled report execution configuration
    """
    # Report reference
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    
    # Schedule configuration
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Cron-like schedule
    schedule_type = models.CharField(
        max_length=20,
        choices=[
            ('cron', 'Cron Expression'),
            ('interval', 'Interval'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='daily'
    )
    
    # For cron type
    cron_expression = models.CharField(
        max_length=100,
        blank=True,
        help_text="Cron expression (e.g., '0 9 * * 1' for 9 AM every Monday)"
    )
    
    # For interval type
    interval_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Interval in minutes for interval-based schedules"
    )
    
    # For daily/weekly/monthly types
    schedule_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time of day to run"
    )
    schedule_day_of_week = models.IntegerField(
        null=True,
        blank=True,
        help_text="Day of week (0=Monday, 6=Sunday) for weekly schedules"
    )
    schedule_day_of_month = models.IntegerField(
        null=True,
        blank=True,
        help_text="Day of month (1-31) for monthly schedules"
    )
    
    # Timezone
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="Timezone for schedule (e.g., 'America/New_York')"
    )
    
    # Recipients
    recipients = models.ManyToManyField(
        User,
        related_name='scheduled_reports'
    )
    
    # Delivery options
    delivery_method = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('api', 'API'),
            ('storage', 'File Storage'),
        ],
        default='email'
    )
    
    # Export format
    export_format = models.CharField(
        max_length=20,
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
            ('json', 'JSON'),
        ],
        default='pdf'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    retry_on_failure = models.BooleanField(default=True)
    max_retries = models.IntegerField(default=3)
    
    class Meta:
        db_table = 'report_schedule'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.report.name}"
    
    def calculate_next_run(self, from_time=None):
        """
        Calculate next run time based on schedule configuration
        """
        if from_time is None:
            from_time = timezone.now()
        
        # Get timezone
        tz = pytz.timezone(self.timezone)
        local_time = from_time.astimezone(tz)
        
        if self.schedule_type == 'daily':
            # Daily at specified time
            next_run = local_time.replace(
                hour=self.schedule_time.hour,
                minute=self.schedule_time.minute,
                second=0,
                microsecond=0
            )
            if next_run <= local_time:
                next_run += timedelta(days=1)
        
        elif self.schedule_type == 'weekly':
            # Weekly on specified day and time
            days_ahead = self.schedule_day_of_week - local_time.weekday()
            if days_ahead <= 0:  # Target day already passed this week
                days_ahead += 7
            
            next_run = local_time + timedelta(days=days_ahead)
            next_run = next_run.replace(
                hour=self.schedule_time.hour,
                minute=self.schedule_time.minute,
                second=0,
                microsecond=0
            )
        
        elif self.schedule_type == 'monthly':
            # Monthly on specified day
            next_run = local_time.replace(
                day=self.schedule_day_of_month,
                hour=self.schedule_time.hour,
                minute=self.schedule_time.minute,
                second=0,
                microsecond=0
            )
            if next_run <= local_time:
                # Move to next month
                if next_run.month == 12:
                    next_run = next_run.replace(year=next_run.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=next_run.month + 1)
        
        elif self.schedule_type == 'interval':
            # Interval-based
            next_run = local_time + timedelta(minutes=self.interval_minutes)
        
        elif self.schedule_type == 'cron':
            # Parse cron expression
            from croniter import croniter
            cron = croniter(self.cron_expression, local_time)
            next_run = cron.get_next(datetime)
        
        else:
            return None
        
        # Convert back to UTC
        return next_run.astimezone(pytz.UTC)
    
    def should_run(self):
        """
        Check if the schedule should run now
        """
        if not self.is_active:
            return False
        
        if self.next_run is None:
            self.next_run = self.calculate_next_run()
            self.save(update_fields=['next_run'])
            return False
        
        return timezone.now() >= self.next_run
    
    def execute(self):
        """
        Execute the scheduled report
        """
        from analytics.services import ReportService
        
        service = ReportService()
        
        try:
            # Generate report
            result = service.generate_report(
                report=self.report,
                export_format=self.export_format
            )
            
            # Create snapshot
            snapshot = ReportSnapshot.objects.create(
                schedule=self,
                report=self.report,
                generated_at=timezone.now(),
                export_format=self.export_format,
                result_data=result.get('data', {}),
                file_path=result.get('file_path', ''),
                status='success',
                company=self.company
            )
            
            # Deliver report
            if self.delivery_method == 'email':
                snapshot.send_email(self.recipients.all())
            
            # Update schedule
            self.last_run = timezone.now()
            self.next_run = self.calculate_next_run()
            self.save(update_fields=['last_run', 'next_run'])
            
            return True, snapshot
        
        except Exception as e:
            # Log error
            snapshot = ReportSnapshot.objects.create(
                schedule=self,
                report=self.report,
                generated_at=timezone.now(),
                export_format=self.export_format,
                status='failed',
                error_message=str(e),
                company=self.company
            )
            
            return False, snapshot


class ReportSnapshot(CompanyIsolatedModel):
    """
    Stored snapshots of executed reports
    """
    # Schedule and report
    schedule = models.ForeignKey(
        ReportSchedule,
        on_delete=models.CASCADE,
        related_name='snapshots',
        null=True,
        blank=True
    )
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='snapshots'
    )
    
    # Generation details
    generated_at = models.DateTimeField()
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_report_snapshots'
    )
    
    # Export details
    export_format = models.CharField(
        max_length=20,
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
            ('json', 'JSON'),
        ]
    )
    
    # Result data
    result_data = models.JSONField(
        help_text="Report result data"
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to generated file"
    )
    file_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('partial', 'Partial'),
        ],
        default='success'
    )
    error_message = models.TextField(blank=True)
    
    # Metadata
    execution_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Execution time in milliseconds"
    )
    row_count = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of rows in result"
    )
    
    # Retention
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to delete this snapshot"
    )
    
    class Meta:
        db_table = 'report_snapshot'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report', 'generated_at']),
            models.Index(fields=['schedule', 'status']),
        ]
    
    def __str__(self):
        return f"{self.report.name} - {self.generated_at}"
    
    def send_email(self, recipients):
        """
        Send report snapshot via email to recipients
        """
        # TODO: Implement actual email sending
        pass
    
    def get_download_url(self):
        """
        Get URL to download the report file
        """
        if self.file_path:
            return f"/api/analytics/report-snapshots/{self.id}/download/"
        return None


class ReportSnapshotAccess(CompanyIsolatedModel):
    """
    Track access to report snapshots
    """
    snapshot = models.ForeignKey(
        ReportSnapshot,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='report_snapshot_accesses'
    )
    
    # Access details
    accessed_at = models.DateTimeField(auto_now_add=True)
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('view', 'View'),
            ('download', 'Download'),
            ('email', 'Email'),
        ]
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'report_snapshot_access'
        ordering = ['-accessed_at']
    
    def __str__(self):
        return f"{self.user.email} accessed {self.snapshot} at {self.accessed_at}"
