# analytics/tests/test_analytics_extended.py
# Tests for extended analytics features

import pytest
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from analytics.metrics_catalog import MetricDefinition, MetricComputationDAG
from analytics.time_series import TimeSeriesSnapshot, TimeSeriesPipeline
from analytics.anomaly_detection import AnomalyDetectionRule, AnomalyDetection
from analytics.data_quality import DataQualityRule, DataQualityCheck
from analytics.services import (
    TimeSeriesService,
    AnomalyDetectionService,
    DataQualityService
)


@pytest.mark.django_db
class TestMetricsCatalog:
    """Test metrics catalog functionality"""
    
    def test_create_metric_definition(self, company, user):
        """Test creating a metric definition"""
        metric = MetricDefinition.objects.create(
            name='total_revenue',
            display_name='Total Revenue',
            description='Total revenue for the period',
            category='revenue',
            metric_type='base',
            data_source='sales_orders',
            calculation_formula='SUM(amount)',
            aggregation_method='sum',
            unit='USD',
            owner=user,
            company=company
        )
        
        assert metric.id is not None
        assert metric.name == 'total_revenue'
        assert metric.version == 1
    
    def test_metric_lineage(self, company, user):
        """Test metric lineage tracking"""
        # Create parent metric
        parent_metric = MetricDefinition.objects.create(
            name='base_revenue',
            display_name='Base Revenue',
            category='revenue',
            metric_type='base',
            data_source='sales',
            calculation_formula='SUM(amount)',
            owner=user,
            company=company
        )
        
        # Create derived metric
        derived_metric = MetricDefinition.objects.create(
            name='revenue_with_tax',
            display_name='Revenue with Tax',
            category='revenue',
            metric_type='derived',
            data_source='sales',
            calculation_formula='base_revenue * 1.1',
            dependencies=['base_revenue'],
            parent_metric=parent_metric,
            version=2,
            owner=user,
            company=company
        )
        
        lineage = derived_metric.get_lineage()
        assert len(lineage) == 2
        assert lineage[0]['name'] == 'revenue_with_tax'
        assert lineage[1]['name'] == 'base_revenue'
    
    def test_dependency_graph(self, company, user):
        """Test dependency graph generation"""
        metric = MetricDefinition.objects.create(
            name='conversion_rate',
            display_name='Conversion Rate',
            category='conversion',
            metric_type='derived',
            data_source='leads',
            calculation_formula='converted_leads / total_leads',
            dependencies=['converted_leads', 'total_leads'],
            owner=user,
            company=company
        )
        
        graph = metric.get_dependency_graph()
        assert 'conversion_rate' in graph
        assert 'converted_leads' in graph['conversion_rate']
        assert 'total_leads' in graph['conversion_rate']


@pytest.mark.django_db
class TestMetricComputationDAG:
    """Test DAG computation functionality"""
    
    def test_dag_validation(self, company):
        """Test DAG cycle detection"""
        # Create valid DAG
        valid_dag = MetricComputationDAG.objects.create(
            name='Valid DAG',
            dag_definition={
                'nodes': ['A', 'B', 'C'],
                'edges': {
                    'A': ['B'],
                    'B': ['C'],
                    'C': []
                }
            },
            execution_order=['A', 'B', 'C'],
            company=company
        )
        
        is_valid, message = valid_dag.validate_dag()
        assert is_valid
        
        # Create DAG with cycle
        cyclic_dag = MetricComputationDAG.objects.create(
            name='Cyclic DAG',
            dag_definition={
                'nodes': ['A', 'B', 'C'],
                'edges': {
                    'A': ['B'],
                    'B': ['C'],
                    'C': ['A']  # Creates cycle
                }
            },
            execution_order=['A', 'B', 'C'],
            company=company
        )
        
        is_valid, message = cyclic_dag.validate_dag()
        assert not is_valid
        assert 'Cycle detected' in message
    
    def test_topological_sort(self, company):
        """Test topological sort of DAG"""
        dag = MetricComputationDAG.objects.create(
            name='Test DAG',
            dag_definition={
                'nodes': ['A', 'B', 'C', 'D'],
                'edges': {
                    'A': ['B', 'C'],
                    'B': ['D'],
                    'C': ['D'],
                    'D': []
                }
            },
            execution_order=[],
            company=company
        )
        
        sorted_order = dag.topological_sort()
        assert len(sorted_order) == 4
        # A should come before B and C
        assert sorted_order.index('A') < sorted_order.index('B')
        assert sorted_order.index('A') < sorted_order.index('C')
        # B and C should come before D
        assert sorted_order.index('B') < sorted_order.index('D')
        assert sorted_order.index('C') < sorted_order.index('D')


@pytest.mark.django_db
class TestTimeSeries:
    """Test time series functionality"""
    
    def test_create_snapshot(self, company, user):
        """Test creating time series snapshot"""
        # Create metric
        metric = MetricDefinition.objects.create(
            name='daily_sales',
            display_name='Daily Sales',
            category='revenue',
            metric_type='base',
            data_source='sales',
            calculation_formula='SUM(amount)',
            owner=user,
            company=company
        )
        
        # Create snapshot
        snapshot = TimeSeriesSnapshot.objects.create(
            metric=metric,
            snapshot_date=timezone.now().date(),
            period_type='daily',
            value=Decimal('1000.00'),
            company=company
        )
        
        assert snapshot.id is not None
        assert snapshot.value == Decimal('1000.00')
    
    def test_change_tracking(self, company, user):
        """Test automatic change tracking"""
        metric = MetricDefinition.objects.create(
            name='test_metric',
            display_name='Test Metric',
            category='custom',
            metric_type='base',
            data_source='test',
            calculation_formula='COUNT(*)',
            owner=user,
            company=company
        )
        
        # Create first snapshot
        snapshot1 = TimeSeriesSnapshot.objects.create(
            metric=metric,
            snapshot_date=timezone.now().date() - timedelta(days=1),
            period_type='daily',
            value=Decimal('100.00'),
            company=company
        )
        
        # Create second snapshot
        snapshot2 = TimeSeriesSnapshot.objects.create(
            metric=metric,
            snapshot_date=timezone.now().date(),
            period_type='daily',
            value=Decimal('120.00'),
            company=company
        )
        
        assert snapshot2.previous_value == Decimal('100.00')
        assert snapshot2.absolute_change == Decimal('20.00')
        assert snapshot2.percent_change == Decimal('20.00')


@pytest.mark.django_db
class TestAnomalyDetection:
    """Test anomaly detection functionality"""
    
    def test_zscore_detection(self, company, user):
        """Test z-score anomaly detection"""
        # Create metric
        metric = MetricDefinition.objects.create(
            name='daily_orders',
            display_name='Daily Orders',
            category='activity',
            metric_type='base',
            data_source='orders',
            calculation_formula='COUNT(*)',
            owner=user,
            company=company
        )
        
        # Create historical snapshots (normal range)
        base_date = timezone.now().date() - timedelta(days=30)
        for i in range(30):
            TimeSeriesSnapshot.objects.create(
                metric=metric,
                snapshot_date=base_date + timedelta(days=i),
                period_type='daily',
                value=Decimal(str(100 + (i % 10))),  # Values between 100-110
                company=company
            )
        
        # Create anomaly detection rule
        rule = AnomalyDetectionRule.objects.create(
            name='Orders Anomaly',
            metric=metric,
            detection_method='zscore',
            zscore_threshold=Decimal('2.0'),
            lookback_period=30,
            alert_enabled=True,
            company=company
        )
        
        # Create anomalous snapshot
        anomalous_snapshot = TimeSeriesSnapshot.objects.create(
            metric=metric,
            snapshot_date=timezone.now().date(),
            period_type='daily',
            value=Decimal('200.00'),  # Anomalously high
            company=company
        )
        
        # Detect anomaly
        is_anomaly, details = rule.detect_anomalies(anomalous_snapshot)
        
        assert is_anomaly
        assert details['method'] == 'zscore'
        assert abs(details['z_score']) > 2.0
    
    def test_threshold_detection(self, company, user):
        """Test threshold-based anomaly detection"""
        metric = MetricDefinition.objects.create(
            name='error_rate',
            display_name='Error Rate',
            category='quality',
            metric_type='base',
            data_source='logs',
            calculation_formula='COUNT(errors)',
            owner=user,
            company=company
        )
        
        rule = AnomalyDetectionRule.objects.create(
            name='Error Rate Alert',
            metric=metric,
            detection_method='threshold',
            upper_threshold=Decimal('10.00'),
            lower_threshold=Decimal('0.00'),
            alert_enabled=True,
            company=company
        )
        
        # Normal snapshot
        normal_snapshot = TimeSeriesSnapshot.objects.create(
            metric=metric,
            snapshot_date=timezone.now().date() - timedelta(days=1),
            period_type='daily',
            value=Decimal('5.00'),
            company=company
        )
        
        is_anomaly, _ = rule.detect_anomalies(normal_snapshot)
        assert not is_anomaly
        
        # Anomalous snapshot
        anomalous_snapshot = TimeSeriesSnapshot.objects.create(
            metric=metric,
            snapshot_date=timezone.now().date(),
            period_type='daily',
            value=Decimal('15.00'),
            company=company
        )
        
        is_anomaly, details = rule.detect_anomalies(anomalous_snapshot)
        assert is_anomaly
        assert details['direction'] == 'high'


@pytest.mark.django_db
class TestDataQuality:
    """Test data quality validation"""
    
    def test_not_null_rule(self, company, user):
        """Test not null validation rule"""
        rule = DataQualityRule.objects.create(
            name='Email Not Null',
            description='Email field must not be null',
            category='completeness',
            target_model='Lead',
            target_fields=['email'],
            rule_type='builtin',
            builtin_rule='not_null',
            rule_expression='',
            severity='error',
            owner=user,
            company=company
        )
        
        assert rule.id is not None
        assert rule.builtin_rule == 'not_null'
    
    def test_range_rule(self, company, user):
        """Test range validation rule"""
        rule = DataQualityRule.objects.create(
            name='Amount Range',
            description='Amount must be positive',
            category='validity',
            target_model='Deal',
            target_fields=['amount'],
            rule_type='builtin',
            builtin_rule='range',
            rule_expression='',
            rule_parameters={
                'min_value': 0,
                'max_value': 1000000
            },
            severity='warning',
            owner=user,
            company=company
        )
        
        assert rule.rule_parameters['min_value'] == 0
        assert rule.rule_parameters['max_value'] == 1000000
    
    def test_incremental_evaluation(self, company, user):
        """Test incremental rule evaluation"""
        rule = DataQualityRule.objects.create(
            name='Test Rule',
            category='completeness',
            target_model='Lead',
            target_fields=['email'],
            rule_type='builtin',
            builtin_rule='not_null',
            rule_expression='',
            is_incremental=True,
            last_evaluated_timestamp=timezone.now() - timedelta(hours=1),
            owner=user,
            company=company
        )
        
        filters = rule.get_filter_for_incremental()
        assert 'updated_at__gt' in filters


@pytest.mark.django_db
class TestServices:
    """Test service layer functionality"""
    
    def test_time_series_service(self, company, user):
        """Test TimeSeriesService"""
        metric = MetricDefinition.objects.create(
            name='test_metric',
            display_name='Test Metric',
            category='custom',
            metric_type='base',
            data_source='test',
            calculation_formula='COUNT(*)',
            owner=user,
            company=company
        )
        
        service = TimeSeriesService()
        snapshot = service.create_snapshot(
            metric=metric,
            snapshot_date=timezone.now().date()
        )
        
        assert snapshot is not None
        assert snapshot.metric == metric
    
    def test_anomaly_detection_service(self, company, user):
        """Test AnomalyDetectionService"""
        metric = MetricDefinition.objects.create(
            name='test_metric',
            display_name='Test Metric',
            category='custom',
            metric_type='base',
            data_source='test',
            calculation_formula='COUNT(*)',
            owner=user,
            company=company
        )
        
        # Create historical data
        base_date = timezone.now().date() - timedelta(days=10)
        for i in range(10):
            TimeSeriesSnapshot.objects.create(
                metric=metric,
                snapshot_date=base_date + timedelta(days=i),
                period_type='daily',
                value=Decimal('100.00'),
                company=company
            )
        
        rule = AnomalyDetectionRule.objects.create(
            name='Test Rule',
            metric=metric,
            detection_method='threshold',
            upper_threshold=Decimal('150.00'),
            company=company
        )
        
        # Create anomalous snapshot
        anomalous_snapshot = TimeSeriesSnapshot.objects.create(
            metric=metric,
            snapshot_date=timezone.now().date(),
            period_type='daily',
            value=Decimal('200.00'),
            company=company
        )
        
        service = AnomalyDetectionService()
        anomaly = service.run_detection(rule, anomalous_snapshot)
        
        assert anomaly is not None
        assert anomaly.snapshot == anomalous_snapshot
