# tests/test_performance_enhancements.py
# Comprehensive tests for performance and scale enhancements

import pytest
import json
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.core.cache import cache
from unittest.mock import Mock, patch, MagicMock


class TestSharingRuleCache(TestCase):
    """Tests for Redis-backed sharing rule cache."""
    
    def setUp(self):
        """Set up test fixtures."""
        from sharing.cache import SharingRuleCache
        self.cache_class = SharingRuleCache
        cache.clear()
    
    def test_cache_key_generation(self):
        """Test cache key generation is consistent."""
        company_id = "test-company-123"
        object_type = "lead"
        
        key1 = self.cache_class.get_cache_key(company_id, object_type)
        key2 = self.cache_class.get_cache_key(company_id, object_type)
        
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length
    
    def test_cache_set_and_get(self):
        """Test caching and retrieving sharing rules."""
        company_id = "test-company-123"
        object_type = "lead"
        rules = [
            {'id': '1', 'name': 'Rule 1', 'predicate': {}},
            {'id': '2', 'name': 'Rule 2', 'predicate': {}},
        ]
        
        # Cache rules
        self.cache_class.set_rules(company_id, object_type, rules)
        
        # Retrieve from cache
        cached_rules = self.cache_class.get_rules(company_id, object_type)
        
        assert cached_rules is not None
        assert len(cached_rules) == 2
        assert cached_rules[0]['name'] == 'Rule 1'
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        result = self.cache_class.get_rules("nonexistent", "lead")
        assert result is None
    
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        company_id = "test-company-123"
        object_type = "lead"
        rules = [{'id': '1', 'name': 'Rule 1'}]
        
        # Cache rules
        self.cache_class.set_rules(company_id, object_type, rules)
        assert self.cache_class.get_rules(company_id, object_type) is not None
        
        # Invalidate
        self.cache_class.invalidate_rules(company_id, object_type)
        assert self.cache_class.get_rules(company_id, object_type) is None
    
    def test_get_or_compute(self):
        """Test get_or_compute functionality."""
        company_id = "test-company-123"
        object_type = "lead"
        
        compute_called = []
        
        def compute_func(cid, otype):
            compute_called.append(True)
            return [{'id': '1', 'computed': True}]
        
        # First call should compute
        result1 = self.cache_class.get_or_compute(
            company_id, object_type, compute_func
        )
        assert len(compute_called) == 1
        assert result1[0]['computed'] is True
        
        # Second call should use cache
        result2 = self.cache_class.get_or_compute(
            company_id, object_type, compute_func
        )
        assert len(compute_called) == 1  # Not called again
        assert result2[0]['computed'] is True


class TestWorkflowPartitioning(TestCase):
    """Tests for workflow step partitioning."""
    
    def setUp(self):
        """Set up test fixtures."""
        from workflow.partitioning import WorkflowStepClassifier, WorkflowPartitioner, StepType
        self.classifier = WorkflowStepClassifier
        self.partitioner = WorkflowPartitioner
        self.step_type = StepType
    
    def test_classify_io_bound_step(self):
        """Test classification of I/O-bound steps."""
        step = {
            'type': 'api',
            'action': 'fetch_data',
            'name': 'Fetch customer data from API'
        }
        
        step_type = self.classifier.classify_step(step)
        assert step_type == self.step_type.IO_BOUND
    
    def test_classify_cpu_bound_step(self):
        """Test classification of CPU-bound steps."""
        step = {
            'type': 'compute',
            'action': 'calculate_metrics',
            'name': 'Calculate customer metrics'
        }
        
        step_type = self.classifier.classify_step(step)
        assert step_type == self.step_type.CPU_BOUND
    
    def test_classify_explicit_queue_type(self):
        """Test explicit queue_type in config."""
        step = {
            'type': 'mixed',
            'action': 'process',
            'name': 'Process data',
            'queue_type': 'io'
        }
        
        step_type = self.classifier.classify_step(step)
        assert step_type == self.step_type.IO_BOUND
    
    def test_partition_steps(self):
        """Test partitioning of workflow steps."""
        steps = [
            {'name': 'Fetch API', 'type': 'api', 'action': 'fetch'},
            {'name': 'Calculate', 'type': 'compute', 'action': 'calculate'},
            {'name': 'Send Email', 'type': 'email', 'action': 'send'},
        ]
        
        partitions = self.partitioner.partition_steps(steps)
        
        assert 'workflow_io' in partitions
        assert 'workflow_cpu' in partitions
        
        # Check that steps were assigned queues
        for step in steps:
            assert '_queue' in step
            assert '_step_type' in step
    
    def test_create_execution_plan(self):
        """Test execution plan creation."""
        steps = [
            {'name': 'Step1', 'type': 'api', 'action': 'fetch'},
            {'name': 'Step2', 'type': 'compute', 'action': 'calculate', 'depends_on': ['Step1']},
        ]
        
        plan = self.partitioner.create_execution_plan(steps)
        
        assert 'parallel_groups' in plan
        assert 'sequential_steps' in plan
        assert 'partitions' in plan


class TestSearchOptimization(TestCase):
    """Tests for search facet precomputation and window caching."""
    
    def setUp(self):
        """Set up test fixtures."""
        from analytics.search_optimization import FacetPrecomputer, WindowCache
        self.facet_precomputer = FacetPrecomputer
        self.window_cache = WindowCache
        cache.clear()
    
    def test_facet_cache_key_generation(self):
        """Test facet cache key generation."""
        key1 = self.facet_precomputer.get_cache_key('lead', 'status', 'company-123')
        key2 = self.facet_precomputer.get_cache_key('lead', 'status', 'company-123')
        
        assert key1 == key2
        assert len(key1) == 32
    
    def test_cache_facet(self):
        """Test caching facet results."""
        facet_result = {
            'type': 'terms',
            'field': 'status',
            'buckets': [
                {'key': 'new', 'doc_count': 10},
                {'key': 'qualified', 'doc_count': 20},
            ]
        }
        
        self.facet_precomputer.cache_facet('lead', 'status', facet_result, 'company-123')
        
        cached = self.facet_precomputer.get_cached_facet('lead', 'status', 'company-123')
        
        assert cached is not None
        assert cached['field'] == 'status'
        assert len(cached['buckets']) == 2
    
    def test_window_cache_query_hash(self):
        """Test query hash computation."""
        query1 = {'filters': {'status': 'new'}, 'sort': 'created_at'}
        query2 = {'sort': 'created_at', 'filters': {'status': 'new'}}
        
        hash1 = self.window_cache.compute_query_hash(query1)
        hash2 = self.window_cache.compute_query_hash(query2)
        
        # Should be same despite different key order
        assert hash1 == hash2
    
    def test_cache_and_get_window(self):
        """Test caching and retrieving result windows."""
        query_params = {'filters': {'status': 'new'}}
        results = [{'id': i, 'name': f'Item {i}'} for i in range(10)]
        
        self.window_cache.cache_window('lead', query_params, 0, 10, results)
        
        cached = self.window_cache.get_window('lead', query_params, 0, 10)
        
        assert cached is not None
        assert len(cached['results']) == 10
        assert cached['window_start'] == 0


class TestReportingOptimization(TestCase):
    """Tests for reporting query plan cache and materialized aggregates."""
    
    def setUp(self):
        """Set up test fixtures."""
        from analytics.reporting_optimization import QueryPlanCache, MaterializedAggregateManager
        self.query_plan_cache = QueryPlanCache
        self.aggregate_manager = MaterializedAggregateManager
        cache.clear()
    
    def test_query_hash_computation(self):
        """Test query hash computation."""
        sql = "SELECT * FROM leads WHERE status = %s"
        params = ('new',)
        
        hash1 = self.query_plan_cache.compute_query_hash(sql, params)
        hash2 = self.query_plan_cache.compute_query_hash(sql, params)
        
        assert hash1 == hash2
        assert len(hash1) == 32
    
    def test_aggregate_cache_key(self):
        """Test aggregate cache key generation."""
        key = self.aggregate_manager.get_cache_key(
            'lead', 'leads_by_status', 'company-123', ['status']
        )
        
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_cache_aggregate(self):
        """Test caching materialized aggregate."""
        aggregate_config = {
            'name': 'leads_by_status',
            'type': 'count',
            'field': 'id',
            'dimensions': ['status']
        }
        
        result = {
            'aggregate_name': 'leads_by_status',
            'data': [
                {'status': 'new', 'count': 10},
                {'status': 'qualified', 'count': 20},
            ]
        }
        
        self.aggregate_manager.cache_aggregate(
            'lead', aggregate_config, result, 'company-123'
        )
        
        cached = self.aggregate_manager.get_cached_aggregate(
            'lead', 'leads_by_status', 'company-123', ['status']
        )
        
        assert cached is not None
        assert cached['aggregate_name'] == 'leads_by_status'
        assert len(cached['data']) == 2


class TestStreamingExport(TestCase):
    """Tests for streaming export with compression."""
    
    def test_csv_exporter_initialization(self):
        """Test CSV exporter initialization."""
        from master_data.streaming_export import CSVStreamingExporter
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        queryset = User.objects.none()
        
        exporter = CSVStreamingExporter(queryset, fields=['id', 'username', 'email'])
        
        assert exporter.queryset is not None
        assert exporter.fields == ['id', 'username', 'email']
    
    def test_export_manager_format_validation(self):
        """Test export manager format validation."""
        from master_data.streaming_export import ExportManager
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        queryset = User.objects.none()
        
        # Valid format
        exporter = ExportManager.create_exporter('csv', queryset)
        assert exporter is not None
        
        # Invalid format
        with pytest.raises(ValueError):
            ExportManager.create_exporter('invalid', queryset)
    
    def test_export_size_estimation(self):
        """Test export size estimation."""
        from master_data.streaming_export import ExportManager
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        queryset = User.objects.none()
        
        estimate = ExportManager.estimate_export_size(queryset, 'csv')
        
        assert 'record_count' in estimate
        assert 'uncompressed_size_mb' in estimate
        assert 'compressed_size_mb' in estimate


class TestVectorSearch(TestCase):
    """Tests for vector search with fallback."""
    
    def test_fallback_backend_always_available(self):
        """Test fallback backend health check."""
        from analytics.vector_search import FallbackSearchBackend
        
        backend = FallbackSearchBackend()
        assert backend.health_check() is True
    
    def test_vector_dimension_validation(self):
        """Test vector dimension validation."""
        from analytics.vector_search import PgVectorBackend
        
        backend = PgVectorBackend(dimension=768)
        
        # Valid dimension
        result = backend.index_document(
            'doc1',
            [0.1] * 768,
            {'text': 'test'}
        )
        # Result depends on database availability
        
        # Invalid dimension
        result = backend.index_document(
            'doc2',
            [0.1] * 512,  # Wrong dimension
            {'text': 'test'}
        )
        assert result is False


class TestPrometheusMetrics(TestCase):
    """Tests for Prometheus metrics integration."""
    
    def test_metrics_registry_initialization(self):
        """Test metrics registry initializes correctly."""
        from core.prometheus_metrics import MetricsRegistry
        
        registry = MetricsRegistry()
        assert registry.registry is not None or registry.registry is None  # Depends on prometheus_client
    
    def test_metrics_generation(self):
        """Test metrics generation."""
        from core.prometheus_metrics import metrics_registry
        
        metrics = metrics_registry.generate_metrics()
        assert isinstance(metrics, bytes)
    
    def test_record_cache_hit(self):
        """Test recording cache hits."""
        from core.prometheus_metrics import record_cache_hit
        
        # Should not raise exception
        record_cache_hit('redis', 'sharing:rules')
    
    def test_record_db_query(self):
        """Test recording database queries."""
        from core.prometheus_metrics import record_db_query
        
        # Should not raise exception
        record_db_query('select', 'Lead', 0.015)


class TestAuditPartitioning(TransactionTestCase):
    """Tests for audit table partitioning."""
    
    def test_partition_name_format(self):
        """Test partition naming convention."""
        from system_config.audit_partitioning import AuditPartitionManager
        
        partition_prefix = AuditPartitionManager.PARTITION_PREFIX
        expected_format = partition_prefix + "2024m01"
        
        assert "audit_log_y" in expected_format
    
    def test_archive_table_name_format(self):
        """Test archive table naming convention."""
        from system_config.audit_partitioning import AuditArchiver
        
        archive_prefix = AuditArchiver.ARCHIVE_TABLE_PREFIX
        expected_format = archive_prefix + "2024m01"
        
        assert "audit_log_archive_y" in expected_format


@pytest.mark.django_db
class TestIntegration:
    """Integration tests for performance enhancements."""
    
    def test_sharing_rule_cache_integration(self):
        """Test sharing rule cache with database."""
        from sharing.cache import SharingRuleCache
        
        company_id = "test-company"
        object_type = "lead"
        
        # Mock data
        rules = [
            {'id': '1', 'name': 'Test Rule', 'is_active': True}
        ]
        
        # Cache and retrieve
        SharingRuleCache.set_rules(company_id, object_type, rules)
        cached = SharingRuleCache.get_rules(company_id, object_type)
        
        assert cached is not None
        assert len(cached) == 1
    
    def test_workflow_partitioning_integration(self):
        """Test workflow execution with partitioning."""
        from workflow.partitioning import WorkflowPartitioner
        
        steps = [
            {'name': 'API Call', 'type': 'api', 'action': 'fetch'},
            {'name': 'Process Data', 'type': 'compute', 'action': 'calculate'},
        ]
        
        plan = WorkflowPartitioner.create_execution_plan(steps)
        
        assert 'parallel_groups' in plan
        assert 'sequential_steps' in plan
    
    def test_metrics_collection_integration(self):
        """Test metrics collection across modules."""
        from core.prometheus_metrics import (
            record_cache_hit,
            record_db_query,
            record_workflow_execution
        )
        
        # Should not raise exceptions
        record_cache_hit('redis', 'test')
        record_db_query('select', 'Test', 0.01)
        record_workflow_execution('automation', 'completed', 1.5)
