# analytics/serializers_extended.py
# Serializers for extended analytics features

from rest_framework import serializers
from analytics.metrics_catalog import (
    MetricDefinition,
    MetricLineage,
    MetricComputationDAG
)
from analytics.time_series import (
    TimeSeriesSnapshot,
    TimeSeriesPipeline,
    TimeSeriesAggregation
)
from analytics.anomaly_detection import (
    AnomalyDetectionRule,
    AnomalyDetection,
    AnomalyAlert
)
from analytics.report_scheduling import (
    ReportSchedule,
    ReportSnapshot,
    ReportSnapshotAccess
)
from analytics.data_quality import (
    DataQualityRule,
    DataQualityCheck,
    DataQualityAlert,
    DataQualityAlertNotification,
    DataQualityDashboard
)


class MetricDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for MetricDefinition"""
    
    lineage = serializers.SerializerMethodField()
    dependency_graph = serializers.SerializerMethodField()
    
    class Meta:
        model = MetricDefinition
        fields = [
            'id', 'name', 'display_name', 'description', 'category',
            'metric_type', 'data_source', 'calculation_formula',
            'aggregation_method', 'unit', 'format_pattern',
            'dependencies', 'version', 'parent_metric', 'owner',
            'is_public', 'cache_duration', 'lineage', 'dependency_graph',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'lineage', 'dependency_graph']
    
    def get_lineage(self, obj):
        return obj.get_lineage()
    
    def get_dependency_graph(self, obj):
        return obj.get_dependency_graph()


class MetricComputationDAGSerializer(serializers.ModelSerializer):
    """Serializer for MetricComputationDAG"""
    
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = MetricComputationDAG
        fields = [
            'id', 'name', 'description', 'dag_definition',
            'execution_order', 'version', 'parent_dag',
            'is_active', 'last_computed', 'is_valid',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_valid']
    
    def get_is_valid(self, obj):
        is_valid, message = obj.validate_dag()
        return {'valid': is_valid, 'message': message}
    
    def validate_dag_definition(self, value):
        """Validate DAG definition"""
        if 'edges' not in value:
            raise serializers.ValidationError("DAG definition must contain 'edges'")
        return value


class TimeSeriesSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for TimeSeriesSnapshot"""
    
    metric_name = serializers.CharField(source='metric.name', read_only=True)
    
    class Meta:
        model = TimeSeriesSnapshot
        fields = [
            'id', 'metric', 'metric_name', 'snapshot_date', 'period_type',
            'value', 'previous_value', 'absolute_change', 'percent_change',
            'moving_average_7d', 'moving_average_30d', 
            'computation_timestamp', 'data_quality_score', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'metric_name', 'previous_value', 'absolute_change',
            'percent_change', 'moving_average_7d', 'moving_average_30d',
            'computation_timestamp', 'created_at', 'updated_at'
        ]


class TimeSeriesPipelineSerializer(serializers.ModelSerializer):
    """Serializer for TimeSeriesPipeline"""
    
    class Meta:
        model = TimeSeriesPipeline
        fields = [
            'id', 'name', 'description', 'metrics', 'schedule_type',
            'schedule_time', 'is_active', 'last_run', 'next_run',
            'retry_on_failure', 'max_retries',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_run', 'next_run', 'created_at', 'updated_at']


class AnomalyDetectionRuleSerializer(serializers.ModelSerializer):
    """Serializer for AnomalyDetectionRule"""
    
    metric_name = serializers.CharField(source='metric.name', read_only=True)
    
    class Meta:
        model = AnomalyDetectionRule
        fields = [
            'id', 'name', 'description', 'metric', 'metric_name',
            'detection_method', 'zscore_threshold', 'upper_threshold',
            'lower_threshold', 'lookback_period', 'deviation_percentage',
            'alert_enabled', 'alert_recipients', 'alert_severity',
            'is_active', 'last_checked',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'metric_name', 'last_checked', 'created_at', 'updated_at']


class AnomalyDetectionSerializer(serializers.ModelSerializer):
    """Serializer for AnomalyDetection"""
    
    metric_name = serializers.CharField(source='snapshot.metric.name', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    
    class Meta:
        model = AnomalyDetection
        fields = [
            'id', 'rule', 'rule_name', 'snapshot', 'metric_name',
            'detected_at', 'detection_method', 'severity',
            'expected_value', 'actual_value', 'deviation',
            'detection_details', 'status', 'investigated_by',
            'investigated_at', 'resolution_notes',
            'alert_sent', 'alert_sent_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'metric_name', 'rule_name', 'detected_at',
            'alert_sent', 'alert_sent_at', 'created_at', 'updated_at'
        ]


class ReportScheduleSerializer(serializers.ModelSerializer):
    """Serializer for ReportSchedule"""
    
    report_name = serializers.CharField(source='report.name', read_only=True)
    
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'report', 'report_name', 'name', 'description',
            'schedule_type', 'cron_expression', 'interval_minutes',
            'schedule_time', 'schedule_day_of_week', 'schedule_day_of_month',
            'timezone', 'recipients', 'delivery_method', 'export_format',
            'is_active', 'last_run', 'next_run',
            'retry_on_failure', 'max_retries',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'report_name', 'last_run', 'next_run', 'created_at', 'updated_at']


class ReportSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for ReportSnapshot"""
    
    report_name = serializers.CharField(source='report.name', read_only=True)
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportSnapshot
        fields = [
            'id', 'schedule', 'report', 'report_name', 'generated_at',
            'generated_by', 'export_format', 'result_data', 'file_path',
            'file_size', 'status', 'error_message', 'execution_time_ms',
            'row_count', 'expires_at', 'download_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'report_name', 'generated_at', 'file_path',
            'file_size', 'execution_time_ms', 'row_count',
            'download_url', 'created_at', 'updated_at'
        ]
    
    def get_download_url(self, obj):
        return obj.get_download_url()


class DataQualityRuleSerializer(serializers.ModelSerializer):
    """Serializer for DataQualityRule"""
    
    class Meta:
        model = DataQualityRule
        fields = [
            'id', 'name', 'description', 'category', 'target_model',
            'target_fields', 'rule_type', 'builtin_rule', 'rule_expression',
            'rule_parameters', 'severity', 'failure_threshold_percentage',
            'evaluation_frequency', 'is_incremental', 'last_evaluated_timestamp',
            'alert_enabled', 'alert_recipients', 'is_active', 'last_run',
            'owner',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'last_evaluated_timestamp', 'last_run',
            'created_at', 'updated_at'
        ]


class DataQualityCheckSerializer(serializers.ModelSerializer):
    """Serializer for DataQualityCheck"""
    
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    
    class Meta:
        model = DataQualityCheck
        fields = [
            'id', 'rule', 'rule_name', 'executed_at', 'execution_time_ms',
            'status', 'total_records', 'records_checked', 'records_passed',
            'records_failed', 'failure_percentage', 'check_details',
            'error_message', 'failed_records_sample',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'rule_name', 'executed_at', 'execution_time_ms',
            'created_at', 'updated_at'
        ]


class DataQualityAlertSerializer(serializers.ModelSerializer):
    """Serializer for DataQualityAlert"""
    
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    
    class Meta:
        model = DataQualityAlert
        fields = [
            'id', 'check', 'rule', 'rule_name', 'severity', 'title',
            'message', 'status', 'acknowledged_by', 'acknowledged_at',
            'resolved_by', 'resolved_at', 'resolution_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'rule_name', 'acknowledged_at', 'resolved_at',
            'created_at', 'updated_at'
        ]


class DataQualityDashboardSerializer(serializers.ModelSerializer):
    """Serializer for DataQualityDashboard"""
    
    summary = serializers.SerializerMethodField()
    
    class Meta:
        model = DataQualityDashboard
        fields = [
            'id', 'name', 'description', 'rules', 'owner',
            'is_public', 'shared_with', 'summary',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'summary', 'created_at', 'updated_at']
    
    def get_summary(self, obj):
        return obj.get_summary()
