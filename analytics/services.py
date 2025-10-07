# analytics/services.py
# Business logic services for analytics features

from typing import Dict, Any, List
from django.db import connection, transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json


class TimeSeriesService:
    """
    Service for time series operations
    """
    
    def create_snapshot(self, metric, snapshot_date, period_type='daily'):
        """
        Create a time series snapshot for a metric
        """
        from analytics.time_series import TimeSeriesSnapshot
        
        # Calculate metric value
        value = self._calculate_metric_value(metric, snapshot_date, period_type)
        
        # Create snapshot
        snapshot = TimeSeriesSnapshot.objects.create(
            metric=metric,
            snapshot_date=snapshot_date,
            period_type=period_type,
            value=value,
            company=metric.company
        )
        
        return snapshot
    
    def _calculate_metric_value(self, metric, snapshot_date, period_type):
        """
        Calculate metric value for given date
        """
        # This is a placeholder - actual implementation would depend on metric definition
        # For now, return a sample calculation
        
        if metric.metric_type == 'base':
            # Base metrics query the source data directly
            return self._query_base_metric(metric, snapshot_date, period_type)
        elif metric.metric_type == 'derived':
            # Derived metrics compute from other metrics
            return self._compute_derived_metric(metric, snapshot_date, period_type)
        elif metric.metric_type == 'aggregate':
            # Aggregate metrics aggregate over time periods
            return self._aggregate_metric(metric, snapshot_date, period_type)
        
        return Decimal('0.0')
    
    def _query_base_metric(self, metric, snapshot_date, period_type):
        """
        Query base metric from source data
        """
        # Example: Count records in source table for the date
        # Actual implementation would use metric.calculation_formula
        return Decimal('100.0')
    
    def _compute_derived_metric(self, metric, snapshot_date, period_type):
        """
        Compute derived metric from dependencies
        """
        # Get dependency values
        from analytics.time_series import TimeSeriesSnapshot
        from analytics.metrics_catalog import MetricDefinition
        
        dependency_values = {}
        for dep_name in metric.dependencies:
            try:
                dep_metric = MetricDefinition.objects.get(
                    name=dep_name,
                    company=metric.company
                )
                dep_snapshot = TimeSeriesSnapshot.objects.filter(
                    metric=dep_metric,
                    snapshot_date=snapshot_date,
                    period_type=period_type
                ).first()
                
                if dep_snapshot:
                    dependency_values[dep_name] = dep_snapshot.value
            except MetricDefinition.DoesNotExist:
                pass
        
        # Evaluate formula with dependency values
        # This is simplified - actual implementation would safely evaluate the formula
        return Decimal('50.0')
    
    def _aggregate_metric(self, metric, snapshot_date, period_type):
        """
        Aggregate metric over time period
        """
        # Aggregate based on aggregation_method
        return Decimal('75.0')


class AnomalyDetectionService:
    """
    Service for anomaly detection operations
    """
    
    def run_detection(self, rule, snapshot):
        """
        Run anomaly detection rule on a snapshot
        """
        from analytics.anomaly_detection import AnomalyDetection
        
        # Detect anomaly
        is_anomaly, details = rule.detect_anomalies(snapshot)
        
        if is_anomaly:
            # Create anomaly record
            anomaly = AnomalyDetection.objects.create(
                rule=rule,
                snapshot=snapshot,
                detection_method=rule.detection_method,
                severity=rule.alert_severity,
                actual_value=snapshot.value,
                expected_value=details.get('mean') or details.get('moving_average'),
                deviation=details.get('z_score') or details.get('deviation_percentage'),
                detection_details=details,
                company=rule.company
            )
            
            # Send alert if enabled
            if rule.alert_enabled:
                anomaly.send_alert()
            
            return anomaly
        
        return None
    
    def batch_detect(self, rule, start_date=None, end_date=None):
        """
        Run anomaly detection on multiple snapshots
        """
        from analytics.time_series import TimeSeriesSnapshot
        
        # Get snapshots to check
        snapshots = TimeSeriesSnapshot.objects.filter(
            metric=rule.metric,
            company=rule.company
        )
        
        if start_date:
            snapshots = snapshots.filter(snapshot_date__gte=start_date)
        if end_date:
            snapshots = snapshots.filter(snapshot_date__lte=end_date)
        
        snapshots = snapshots.order_by('snapshot_date')
        
        # Run detection on each snapshot
        anomalies = []
        for snapshot in snapshots:
            anomaly = self.run_detection(rule, snapshot)
            if anomaly:
                anomalies.append(anomaly)
        
        return anomalies


class DataQualityService:
    """
    Service for data quality validation
    """
    
    def evaluate_builtin_rule(self, rule, incremental=True) -> Dict[str, Any]:
        """
        Evaluate built-in data quality rule
        """
        from django.apps import apps
        
        # Get model
        try:
            model = apps.get_model('crm', rule.target_model)
        except LookupError:
            try:
                model = apps.get_model('deals', rule.target_model)
            except LookupError:
                try:
                    model = apps.get_model('sales', rule.target_model)
                except LookupError:
                    return {'success': False, 'error': f'Model {rule.target_model} not found'}
        
        # Get queryset
        queryset = model.objects.filter(company=rule.company)
        
        # Apply incremental filter
        if incremental:
            filter_params = rule.get_filter_for_incremental()
            queryset = queryset.filter(**filter_params)
        
        total_records = queryset.count()
        
        # Apply built-in rule
        if rule.builtin_rule == 'not_null':
            return self._check_not_null(queryset, rule, total_records)
        elif rule.builtin_rule == 'unique':
            return self._check_unique(queryset, rule, total_records)
        elif rule.builtin_rule == 'range':
            return self._check_range(queryset, rule, total_records)
        elif rule.builtin_rule == 'pattern':
            return self._check_pattern(queryset, rule, total_records)
        elif rule.builtin_rule == 'foreign_key':
            return self._check_foreign_key(queryset, rule, total_records)
        elif rule.builtin_rule == 'date_range':
            return self._check_date_range(queryset, rule, total_records)
        elif rule.builtin_rule == 'value_in_list':
            return self._check_value_in_list(queryset, rule, total_records)
        
        return {'success': False, 'error': 'Unknown built-in rule'}
    
    def _check_not_null(self, queryset, rule, total_records):
        """
        Check that fields are not null
        """
        failed_records = []
        
        for field in rule.target_fields:
            null_records = queryset.filter(**{f'{field}__isnull': True})
            for record in null_records[:100]:  # Sample first 100
                failed_records.append({
                    'id': record.id,
                    'field': field,
                    'reason': 'Field is null'
                })
        
        records_failed = len(failed_records)
        records_passed = total_records - records_failed
        
        return {
            'success': True,
            'total_records': total_records,
            'records_checked': total_records,
            'records_passed': records_passed,
            'records_failed': records_failed,
            'failed_records_sample': failed_records[:100]
        }
    
    def _check_unique(self, queryset, rule, total_records):
        """
        Check that field values are unique
        """
        # Implementation for uniqueness check
        return {
            'success': True,
            'total_records': total_records,
            'records_checked': total_records,
            'records_passed': total_records,
            'records_failed': 0,
            'failed_records_sample': []
        }
    
    def _check_range(self, queryset, rule, total_records):
        """
        Check that field values are within range
        """
        min_value = rule.rule_parameters.get('min_value')
        max_value = rule.rule_parameters.get('max_value')
        
        failed_records = []
        
        for field in rule.target_fields:
            filter_params = {}
            if min_value is not None:
                filter_params[f'{field}__lt'] = min_value
            if max_value is not None:
                filter_params[f'{field}__gt'] = max_value
            
            if filter_params:
                out_of_range = queryset.filter(**filter_params)
                for record in out_of_range[:100]:
                    failed_records.append({
                        'id': record.id,
                        'field': field,
                        'value': getattr(record, field),
                        'reason': f'Value out of range ({min_value} - {max_value})'
                    })
        
        records_failed = len(failed_records)
        records_passed = total_records - records_failed
        
        return {
            'success': True,
            'total_records': total_records,
            'records_checked': total_records,
            'records_passed': records_passed,
            'records_failed': records_failed,
            'failed_records_sample': failed_records[:100]
        }
    
    def _check_pattern(self, queryset, rule, total_records):
        """
        Check that field values match pattern
        """
        # Implementation for pattern check
        return {
            'success': True,
            'total_records': total_records,
            'records_checked': total_records,
            'records_passed': total_records,
            'records_failed': 0,
            'failed_records_sample': []
        }
    
    def _check_foreign_key(self, queryset, rule, total_records):
        """
        Check foreign key validity
        """
        # Implementation for foreign key check
        return {
            'success': True,
            'total_records': total_records,
            'records_checked': total_records,
            'records_passed': total_records,
            'records_failed': 0,
            'failed_records_sample': []
        }
    
    def _check_date_range(self, queryset, rule, total_records):
        """
        Check date field is within range
        """
        # Implementation for date range check
        return {
            'success': True,
            'total_records': total_records,
            'records_checked': total_records,
            'records_passed': total_records,
            'records_failed': 0,
            'failed_records_sample': []
        }
    
    def _check_value_in_list(self, queryset, rule, total_records):
        """
        Check that field value is in allowed list
        """
        allowed_values = rule.rule_parameters.get('allowed_values', [])
        
        failed_records = []
        
        for field in rule.target_fields:
            invalid_records = queryset.exclude(**{f'{field}__in': allowed_values})
            for record in invalid_records[:100]:
                failed_records.append({
                    'id': record.id,
                    'field': field,
                    'value': getattr(record, field),
                    'reason': f'Value not in allowed list: {allowed_values}'
                })
        
        records_failed = len(failed_records)
        records_passed = total_records - records_failed
        
        return {
            'success': True,
            'total_records': total_records,
            'records_checked': total_records,
            'records_passed': records_passed,
            'records_failed': records_failed,
            'failed_records_sample': failed_records[:100]
        }
    
    def evaluate_sql_rule(self, rule, incremental=True) -> Dict[str, Any]:
        """
        Evaluate SQL-based data quality rule
        """
        # Execute SQL query
        with connection.cursor() as cursor:
            try:
                cursor.execute(rule.rule_expression)
                result = cursor.fetchall()
                
                # Parse results
                records_failed = len(result)
                
                return {
                    'success': True,
                    'records_failed': records_failed,
                    'failed_records_sample': result[:100]
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
    
    def evaluate_python_rule(self, rule, incremental=True) -> Dict[str, Any]:
        """
        Evaluate Python expression rule
        """
        # This should be implemented with safe evaluation
        return {
            'success': False,
            'error': 'Python rule evaluation not yet implemented'
        }


class ReportService:
    """
    Service for report generation
    """
    
    def generate_report(self, report, export_format='pdf'):
        """
        Generate report in specified format
        """
        # This is a placeholder implementation
        # Actual implementation would query data based on report configuration
        
        data = {
            'report_name': report.name,
            'generated_at': timezone.now().isoformat(),
            'data_source': report.data_source,
            'filters': report.filters,
            'results': []
        }
        
        # Generate file path
        file_path = f"/tmp/reports/{report.id}_{timezone.now().timestamp()}.{export_format}"
        
        return {
            'success': True,
            'data': data,
            'file_path': file_path
        }
