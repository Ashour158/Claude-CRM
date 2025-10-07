# analytics/data_quality.py
# Data quality validation engine with rule DSL, incremental evaluation, and alerting

from django.db import models
from core.models import CompanyIsolatedModel, User
from django.utils import timezone
from typing import Any, Dict, List
import json


class DataQualityRule(CompanyIsolatedModel):
    """
    Data quality validation rules with DSL support
    """
    # Basic information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('completeness', 'Completeness'),
            ('accuracy', 'Accuracy'),
            ('consistency', 'Consistency'),
            ('timeliness', 'Timeliness'),
            ('validity', 'Validity'),
            ('uniqueness', 'Uniqueness'),
        ]
    )
    
    # Target data
    target_model = models.CharField(
        max_length=100,
        help_text="Model/table to validate (e.g., 'leads', 'deals')"
    )
    target_fields = models.JSONField(
        default=list,
        help_text="List of fields to validate"
    )
    
    # Rule definition (DSL)
    rule_type = models.CharField(
        max_length=20,
        choices=[
            ('sql', 'SQL Query'),
            ('python', 'Python Expression'),
            ('builtin', 'Built-in Rule'),
        ],
        default='builtin'
    )
    
    # Built-in rule types
    builtin_rule = models.CharField(
        max_length=50,
        choices=[
            ('not_null', 'Not Null'),
            ('unique', 'Unique'),
            ('range', 'Value Range'),
            ('pattern', 'Pattern Match'),
            ('foreign_key', 'Foreign Key Valid'),
            ('date_range', 'Date Range'),
            ('value_in_list', 'Value In List'),
        ],
        blank=True
    )
    
    # Rule expression
    rule_expression = models.TextField(
        help_text="SQL query, Python expression, or JSON rule definition"
    )
    
    # Rule parameters
    rule_parameters = models.JSONField(
        default=dict,
        help_text="Parameters for the rule (e.g., min/max values, patterns)"
    )
    
    # Severity
    severity = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('critical', 'Critical'),
        ],
        default='warning'
    )
    
    # Thresholds
    failure_threshold_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Percentage of failures to trigger alert (0-100)"
    )
    
    # Execution
    evaluation_frequency = models.CharField(
        max_length=20,
        choices=[
            ('realtime', 'Real-time'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='daily'
    )
    
    # Incremental evaluation
    is_incremental = models.BooleanField(
        default=True,
        help_text="Only evaluate new/changed records"
    )
    last_evaluated_timestamp = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Alerting
    alert_enabled = models.BooleanField(default=True)
    alert_recipients = models.ManyToManyField(
        User,
        related_name='data_quality_alerts'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_data_quality_rules'
    )
    
    class Meta:
        db_table = 'data_quality_rule'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['target_model', 'is_active']),
            models.Index(fields=['category', 'severity']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.target_model}"
    
    def evaluate(self, incremental=True) -> Dict[str, Any]:
        """
        Evaluate the data quality rule
        Returns: Dictionary with evaluation results
        """
        from analytics.services import DataQualityService
        
        service = DataQualityService()
        
        if self.rule_type == 'builtin':
            return service.evaluate_builtin_rule(self, incremental)
        elif self.rule_type == 'sql':
            return service.evaluate_sql_rule(self, incremental)
        elif self.rule_type == 'python':
            return service.evaluate_python_rule(self, incremental)
        
        return {'success': False, 'error': 'Unknown rule type'}
    
    def get_filter_for_incremental(self) -> Dict[str, Any]:
        """
        Get filter conditions for incremental evaluation
        """
        if not self.is_incremental or not self.last_evaluated_timestamp:
            return {}
        
        return {
            'updated_at__gt': self.last_evaluated_timestamp
        }


class DataQualityCheck(CompanyIsolatedModel):
    """
    Record of data quality rule evaluation
    """
    # Rule reference
    rule = models.ForeignKey(
        DataQualityRule,
        on_delete=models.CASCADE,
        related_name='checks'
    )
    
    # Execution details
    executed_at = models.DateTimeField(auto_now_add=True)
    execution_time_ms = models.IntegerField(
        help_text="Execution time in milliseconds"
    )
    
    # Results
    status = models.CharField(
        max_length=20,
        choices=[
            ('passed', 'Passed'),
            ('failed', 'Failed'),
            ('error', 'Error'),
            ('warning', 'Warning'),
        ]
    )
    
    # Metrics
    total_records = models.IntegerField(default=0)
    records_checked = models.IntegerField(default=0)
    records_passed = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    failure_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0
    )
    
    # Details
    check_details = models.JSONField(
        help_text="Detailed check results"
    )
    error_message = models.TextField(blank=True)
    
    # Failed records sample
    failed_records_sample = models.JSONField(
        default=list,
        help_text="Sample of failed records (max 100)"
    )
    
    class Meta:
        db_table = 'data_quality_check'
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['rule', 'executed_at']),
            models.Index(fields=['status', 'executed_at']),
        ]
    
    def __str__(self):
        return f"{self.rule.name} - {self.executed_at} - {self.status}"
    
    def should_alert(self) -> bool:
        """
        Determine if this check should trigger an alert
        """
        if self.status == 'passed':
            return False
        
        if self.status == 'error':
            return True
        
        return self.failure_percentage >= self.rule.failure_threshold_percentage
    
    def create_alert(self):
        """
        Create alert for this failed check
        """
        if not self.should_alert() or not self.rule.alert_enabled:
            return None
        
        alert = DataQualityAlert.objects.create(
            check=self,
            rule=self.rule,
            severity=self.rule.severity,
            title=f"Data Quality Issue: {self.rule.name}",
            message=self._generate_alert_message(),
            company=self.company
        )
        
        # Send notifications to recipients
        for recipient in self.rule.alert_recipients.all():
            DataQualityAlertNotification.objects.create(
                alert=alert,
                recipient=recipient,
                company=self.company
            )
        
        return alert
    
    def _generate_alert_message(self) -> str:
        """
        Generate alert message based on check results
        """
        msg = f"Data quality check '{self.rule.name}' "
        
        if self.status == 'error':
            msg += f"encountered an error: {self.error_message}"
        else:
            msg += f"failed with {self.failure_percentage:.2f}% failure rate.\n\n"
            msg += f"Records checked: {self.records_checked}\n"
            msg += f"Records failed: {self.records_failed}\n"
            msg += f"Threshold: {self.rule.failure_threshold_percentage}%"
        
        return msg


class DataQualityAlert(CompanyIsolatedModel):
    """
    Alerts for data quality issues
    """
    # Check and rule
    check = models.ForeignKey(
        DataQualityCheck,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    rule = models.ForeignKey(
        DataQualityRule,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    
    # Alert details
    severity = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('critical', 'Critical'),
        ]
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('acknowledged', 'Acknowledged'),
            ('resolved', 'Resolved'),
            ('ignored', 'Ignored'),
        ],
        default='open'
    )
    
    # Resolution
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_dq_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_dq_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'data_quality_alert'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rule', 'status']),
            models.Index(fields=['severity', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.status}"
    
    def acknowledge(self, user: User):
        """
        Acknowledge this alert
        """
        self.status = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save(update_fields=['status', 'acknowledged_by', 'acknowledged_at'])
    
    def resolve(self, user: User, notes: str = ''):
        """
        Resolve this alert
        """
        self.status = 'resolved'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save(update_fields=['status', 'resolved_by', 'resolved_at', 'resolution_notes'])


class DataQualityAlertNotification(CompanyIsolatedModel):
    """
    Notification records for data quality alerts
    """
    alert = models.ForeignKey(
        DataQualityAlert,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dq_alert_notifications'
    )
    
    # Notification details
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('slack', 'Slack'),
            ('webhook', 'Webhook'),
        ],
        default='email'
    )
    
    # Status
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'data_quality_alert_notification'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification to {self.recipient.email} for {self.alert}"
    
    def send(self):
        """
        Send the notification
        """
        # TODO: Implement actual notification sending
        self.sent = True
        self.sent_at = timezone.now()
        self.save(update_fields=['sent', 'sent_at'])


class DataQualityDashboard(CompanyIsolatedModel):
    """
    Dashboard for data quality metrics
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Dashboard configuration
    rules = models.ManyToManyField(
        DataQualityRule,
        related_name='dashboards'
    )
    
    # Access control
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_dq_dashboards'
    )
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(
        User,
        blank=True,
        related_name='shared_dq_dashboards'
    )
    
    class Meta:
        db_table = 'data_quality_dashboard'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for dashboard
        """
        rules = self.rules.filter(is_active=True)
        
        # Get latest check for each rule
        latest_checks = []
        for rule in rules:
            latest_check = rule.checks.order_by('-executed_at').first()
            if latest_check:
                latest_checks.append(latest_check)
        
        total_rules = len(latest_checks)
        passed_rules = sum(1 for check in latest_checks if check.status == 'passed')
        failed_rules = sum(1 for check in latest_checks if check.status == 'failed')
        error_rules = sum(1 for check in latest_checks if check.status == 'error')
        
        return {
            'total_rules': total_rules,
            'passed_rules': passed_rules,
            'failed_rules': failed_rules,
            'error_rules': error_rules,
            'health_score': (passed_rules / total_rules * 100) if total_rules > 0 else 0,
            'latest_checks': latest_checks
        }
