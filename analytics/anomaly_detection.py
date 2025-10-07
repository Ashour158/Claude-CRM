# analytics/anomaly_detection.py
# Automated anomaly detection on key KPIs with z-score and alerting

from django.db import models
from core.models import CompanyIsolatedModel, User
from analytics.metrics_catalog import MetricDefinition
from analytics.time_series import TimeSeriesSnapshot
from django.utils import timezone
import statistics
from decimal import Decimal
import math


class AnomalyDetectionRule(CompanyIsolatedModel):
    """
    Rules for detecting anomalies in metrics
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Target metric
    metric = models.ForeignKey(
        MetricDefinition,
        on_delete=models.CASCADE,
        related_name='anomaly_rules'
    )
    
    # Detection method
    detection_method = models.CharField(
        max_length=20,
        choices=[
            ('zscore', 'Z-Score'),
            ('iqr', 'Interquartile Range'),
            ('moving_avg', 'Moving Average Deviation'),
            ('threshold', 'Fixed Threshold'),
        ],
        default='zscore'
    )
    
    # Z-score configuration
    zscore_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=3.0,
        help_text="Number of standard deviations for z-score method"
    )
    
    # Threshold configuration
    upper_threshold = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    lower_threshold = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    
    # Moving average configuration
    lookback_period = models.IntegerField(
        default=30,
        help_text="Number of days to look back for baseline"
    )
    deviation_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.0,
        help_text="Percentage deviation from moving average"
    )
    
    # Alerting
    alert_enabled = models.BooleanField(default=True)
    alert_recipients = models.ManyToManyField(
        User,
        related_name='anomaly_alerts'
    )
    alert_severity = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('critical', 'Critical'),
        ],
        default='warning'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'anomaly_detection_rule'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.metric.name}"
    
    def detect_anomalies(self, snapshot: TimeSeriesSnapshot) -> tuple[bool, dict]:
        """
        Detect if a snapshot is anomalous based on the rule
        Returns: (is_anomaly, details)
        """
        if self.detection_method == 'zscore':
            return self._detect_zscore(snapshot)
        elif self.detection_method == 'iqr':
            return self._detect_iqr(snapshot)
        elif self.detection_method == 'moving_avg':
            return self._detect_moving_avg(snapshot)
        elif self.detection_method == 'threshold':
            return self._detect_threshold(snapshot)
        
        return False, {}
    
    def _detect_zscore(self, snapshot: TimeSeriesSnapshot) -> tuple[bool, dict]:
        """
        Detect anomalies using z-score method
        """
        # Get historical data
        historical_snapshots = TimeSeriesSnapshot.objects.filter(
            metric=self.metric,
            snapshot_date__lt=snapshot.snapshot_date,
            snapshot_date__gte=snapshot.snapshot_date - timezone.timedelta(days=self.lookback_period),
            company=self.company
        ).order_by('-snapshot_date')
        
        if historical_snapshots.count() < 2:
            return False, {'reason': 'Insufficient historical data'}
        
        # Calculate mean and standard deviation
        values = [float(s.value) for s in historical_snapshots]
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        if std_dev == 0:
            return False, {'reason': 'Zero standard deviation'}
        
        # Calculate z-score
        z_score = (float(snapshot.value) - mean) / std_dev
        
        is_anomaly = abs(z_score) > float(self.zscore_threshold)
        
        return is_anomaly, {
            'method': 'zscore',
            'z_score': z_score,
            'mean': mean,
            'std_dev': std_dev,
            'threshold': float(self.zscore_threshold),
            'direction': 'high' if z_score > 0 else 'low'
        }
    
    def _detect_iqr(self, snapshot: TimeSeriesSnapshot) -> tuple[bool, dict]:
        """
        Detect anomalies using Interquartile Range (IQR) method
        """
        # Get historical data
        historical_snapshots = TimeSeriesSnapshot.objects.filter(
            metric=self.metric,
            snapshot_date__lt=snapshot.snapshot_date,
            snapshot_date__gte=snapshot.snapshot_date - timezone.timedelta(days=self.lookback_period),
            company=self.company
        ).order_by('-snapshot_date')
        
        if historical_snapshots.count() < 4:
            return False, {'reason': 'Insufficient historical data'}
        
        values = sorted([float(s.value) for s in historical_snapshots])
        
        # Calculate quartiles
        q1 = statistics.quantiles(values, n=4)[0]
        q3 = statistics.quantiles(values, n=4)[2]
        iqr = q3 - q1
        
        # Calculate bounds
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        value = float(snapshot.value)
        is_anomaly = value < lower_bound or value > upper_bound
        
        return is_anomaly, {
            'method': 'iqr',
            'value': value,
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'direction': 'high' if value > upper_bound else 'low' if value < lower_bound else 'normal'
        }
    
    def _detect_moving_avg(self, snapshot: TimeSeriesSnapshot) -> tuple[bool, dict]:
        """
        Detect anomalies based on deviation from moving average
        """
        if snapshot.moving_average_30d is None:
            return False, {'reason': 'Moving average not available'}
        
        moving_avg = float(snapshot.moving_average_30d)
        value = float(snapshot.value)
        
        # Calculate percentage deviation
        if moving_avg != 0:
            deviation = abs((value - moving_avg) / moving_avg) * 100
        else:
            deviation = 0
        
        is_anomaly = deviation > float(self.deviation_percentage)
        
        return is_anomaly, {
            'method': 'moving_avg',
            'value': value,
            'moving_average': moving_avg,
            'deviation_percentage': deviation,
            'threshold': float(self.deviation_percentage),
            'direction': 'high' if value > moving_avg else 'low'
        }
    
    def _detect_threshold(self, snapshot: TimeSeriesSnapshot) -> tuple[bool, dict]:
        """
        Detect anomalies based on fixed thresholds
        """
        value = snapshot.value
        is_anomaly = False
        direction = 'normal'
        
        if self.upper_threshold is not None and value > self.upper_threshold:
            is_anomaly = True
            direction = 'high'
        elif self.lower_threshold is not None and value < self.lower_threshold:
            is_anomaly = True
            direction = 'low'
        
        return is_anomaly, {
            'method': 'threshold',
            'value': float(value),
            'upper_threshold': float(self.upper_threshold) if self.upper_threshold else None,
            'lower_threshold': float(self.lower_threshold) if self.lower_threshold else None,
            'direction': direction
        }


class AnomalyDetection(CompanyIsolatedModel):
    """
    Detected anomalies in metrics
    """
    # Rule and snapshot
    rule = models.ForeignKey(
        AnomalyDetectionRule,
        on_delete=models.CASCADE,
        related_name='detections'
    )
    snapshot = models.ForeignKey(
        TimeSeriesSnapshot,
        on_delete=models.CASCADE,
        related_name='anomalies'
    )
    
    # Anomaly details
    detected_at = models.DateTimeField(auto_now_add=True)
    detection_method = models.CharField(max_length=20)
    severity = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('critical', 'Critical'),
        ]
    )
    
    # Anomaly metrics
    expected_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    actual_value = models.DecimalField(
        max_digits=20,
        decimal_places=4
    )
    deviation = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        null=True,
        blank=True
    )
    
    # Details and metadata
    detection_details = models.JSONField(
        help_text="Detailed detection information"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('investigating', 'Investigating'),
            ('resolved', 'Resolved'),
            ('false_positive', 'False Positive'),
        ],
        default='open'
    )
    
    # Investigation
    investigated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investigated_anomalies'
    )
    investigated_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Alerting
    alert_sent = models.BooleanField(default=False)
    alert_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'anomaly_detection'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['rule', 'detected_at']),
            models.Index(fields=['status', 'severity']),
        ]
    
    def __str__(self):
        return f"Anomaly in {self.snapshot.metric.name} on {self.snapshot.snapshot_date}"
    
    def send_alert(self):
        """
        Send alert notification for this anomaly
        """
        if self.alert_sent:
            return
        
        # Get alert recipients from rule
        recipients = self.rule.alert_recipients.all()
        
        # TODO: Implement actual email/notification sending
        # For now, just mark as sent
        self.alert_sent = True
        self.alert_sent_at = timezone.now()
        self.save(update_fields=['alert_sent', 'alert_sent_at'])
        
        return True


class AnomalyAlert(CompanyIsolatedModel):
    """
    Alert notifications for anomalies
    """
    anomaly = models.ForeignKey(
        AnomalyDetection,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    
    # Alert details
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_anomaly_alerts'
    )
    alert_type = models.CharField(
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
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Content
    subject = models.CharField(max_length=255)
    message = models.TextField()
    
    class Meta:
        db_table = 'anomaly_alert'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Alert to {self.recipient.email} for {self.anomaly}"
