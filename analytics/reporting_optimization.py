# analytics/reporting_optimization.py
# Reporting query plan cache and materialized aggregates

import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db import connection, models
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek

logger = logging.getLogger(__name__)


class QueryPlanCache:
    """
    Caches database query execution plans for reporting queries.
    Improves performance by reusing optimized query plans.
    """
    
    CACHE_PREFIX = 'query:plan'
    CACHE_VERSION = 'v1'
    DEFAULT_TIMEOUT = 86400  # 24 hours
    
    @classmethod
    def get_cache_key(cls, query_hash: str) -> str:
        """Generate cache key for query plan."""
        return f"{cls.CACHE_PREFIX}:{cls.CACHE_VERSION}:{query_hash}"
    
    @classmethod
    def compute_query_hash(cls, sql: str, params: Optional[Tuple] = None) -> str:
        """Compute hash for SQL query."""
        query_str = f"{sql}:{params}"
        return hashlib.md5(query_str.encode()).hexdigest()
    
    @classmethod
    def get_query_plan(cls, sql: str) -> Optional[Dict[str, Any]]:
        """
        Get execution plan for SQL query.
        
        Args:
            sql: SQL query string
            
        Returns:
            Query execution plan from EXPLAIN
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"EXPLAIN (FORMAT JSON) {sql}")
                plan = cursor.fetchone()[0]
                return plan[0] if isinstance(plan, list) else plan
        except Exception as e:
            logger.error(f"Error getting query plan: {e}")
            return None
    
    @classmethod
    def cache_query_plan(cls, sql: str, params: Optional[Tuple] = None,
                        timeout: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Cache query execution plan.
        
        Args:
            sql: SQL query string
            params: Query parameters
            timeout: Cache timeout in seconds
            
        Returns:
            Query plan dictionary
        """
        query_hash = cls.compute_query_hash(sql, params)
        cache_key = cls.get_cache_key(query_hash)
        
        # Get plan from database
        plan = cls.get_query_plan(sql)
        
        if plan:
            timeout = timeout or cls.DEFAULT_TIMEOUT
            cache.set(cache_key, plan, timeout)
            logger.info(f"Cached query plan: {query_hash[:16]}")
        
        return plan
    
    @classmethod
    def get_cached_plan(cls, sql: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
        """Get cached query plan."""
        query_hash = cls.compute_query_hash(sql, params)
        cache_key = cls.get_cache_key(query_hash)
        
        plan = cache.get(cache_key)
        
        if plan:
            logger.debug(f"Cache hit for query plan: {query_hash[:16]}")
        else:
            logger.debug(f"Cache miss for query plan: {query_hash[:16]}")
        
        return plan
    
    @classmethod
    def analyze_query_performance(cls, sql: str, params: Optional[Tuple] = None) -> Dict[str, Any]:
        """
        Analyze query performance using cached or fresh plan.
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            Performance analysis dictionary
        """
        plan = cls.get_cached_plan(sql, params)
        
        if not plan:
            plan = cls.cache_query_plan(sql, params)
        
        if not plan:
            return {'error': 'Could not get query plan'}
        
        # Extract performance metrics from plan
        analysis = {
            'estimated_cost': plan.get('Plan', {}).get('Total Cost', 0),
            'estimated_rows': plan.get('Plan', {}).get('Plan Rows', 0),
            'node_type': plan.get('Plan', {}).get('Node Type', 'Unknown'),
            'parallel_aware': plan.get('Plan', {}).get('Parallel Aware', False),
            'uses_index': 'Index' in plan.get('Plan', {}).get('Node Type', ''),
        }
        
        return analysis


class MaterializedAggregateManager:
    """
    Manages materialized aggregates for reporting.
    Pre-computes common aggregations for fast query response.
    """
    
    CACHE_PREFIX = 'aggregate:materialized'
    CACHE_VERSION = 'v1'
    DEFAULT_TIMEOUT = 3600  # 1 hour
    
    # Common aggregate types
    AGGREGATE_TYPES = {
        'count': Count,
        'sum': Sum,
        'avg': Avg,
        'min': Min,
        'max': Max,
    }
    
    @classmethod
    def get_cache_key(cls, entity_type: str, aggregate_name: str,
                      company_id: Optional[str] = None,
                      dimensions: Optional[List[str]] = None,
                      filters: Optional[Dict] = None) -> str:
        """Generate cache key for materialized aggregate."""
        filter_hash = ''
        if filters:
            filter_hash = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:8]
        
        dim_str = '_'.join(sorted(dimensions)) if dimensions else 'none'
        
        if company_id:
            key_data = f"{cls.CACHE_PREFIX}:{cls.CACHE_VERSION}:{company_id}:{entity_type}:{aggregate_name}:{dim_str}:{filter_hash}"
        else:
            key_data = f"{cls.CACHE_PREFIX}:{cls.CACHE_VERSION}:global:{entity_type}:{aggregate_name}:{dim_str}:{filter_hash}"
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @classmethod
    def materialize_aggregate(cls, entity_type: str, aggregate_config: Dict[str, Any],
                             model_class: models.Model, company_id: Optional[str] = None,
                             filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Materialize an aggregate computation.
        
        Args:
            entity_type: Type of entity
            aggregate_config: Configuration with 'name', 'type', 'field', 'dimensions'
            model_class: Django model class
            company_id: Optional company UUID
            filters: Additional filters
            
        Returns:
            Materialized aggregate result
        """
        aggregate_name = aggregate_config['name']
        aggregate_type = aggregate_config['type']
        field_name = aggregate_config['field']
        dimensions = aggregate_config.get('dimensions', [])
        
        logger.info(f"Materializing aggregate {entity_type}.{aggregate_name}")
        
        # Build queryset
        queryset = model_class.objects.all()
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        if filters:
            queryset = queryset.filter(**filters)
        
        # Apply grouping dimensions
        if dimensions:
            queryset = queryset.values(*dimensions)
        
        # Apply aggregate function
        agg_func = cls.AGGREGATE_TYPES.get(aggregate_type)
        if not agg_func:
            return {'error': f'Unknown aggregate type: {aggregate_type}'}
        
        agg_field = f'{aggregate_name}_value'
        queryset = queryset.annotate(**{agg_field: agg_func(field_name)})
        
        # Execute query
        results = list(queryset)
        
        # Format results
        formatted_results = {
            'aggregate_name': aggregate_name,
            'aggregate_type': aggregate_type,
            'field': field_name,
            'dimensions': dimensions,
            'data': results,
            'computed_at': timezone.now().isoformat(),
            'record_count': len(results)
        }
        
        return formatted_results
    
    @classmethod
    def cache_aggregate(cls, entity_type: str, aggregate_config: Dict[str, Any],
                       result: Dict[str, Any], company_id: Optional[str] = None,
                       filters: Optional[Dict] = None, timeout: Optional[int] = None) -> None:
        """Cache materialized aggregate."""
        aggregate_name = aggregate_config['name']
        dimensions = aggregate_config.get('dimensions', [])
        
        cache_key = cls.get_cache_key(
            entity_type, aggregate_name, company_id, dimensions, filters
        )
        timeout = timeout or cls.DEFAULT_TIMEOUT
        
        cache.set(cache_key, result, timeout)
        logger.info(f"Cached materialized aggregate {entity_type}.{aggregate_name}")
    
    @classmethod
    def get_cached_aggregate(cls, entity_type: str, aggregate_name: str,
                            company_id: Optional[str] = None,
                            dimensions: Optional[List[str]] = None,
                            filters: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Get cached materialized aggregate."""
        cache_key = cls.get_cache_key(
            entity_type, aggregate_name, company_id, dimensions, filters
        )
        
        result = cache.get(cache_key)
        
        if result:
            logger.debug(f"Cache hit for materialized aggregate {entity_type}.{aggregate_name}")
        else:
            logger.debug(f"Cache miss for materialized aggregate {entity_type}.{aggregate_name}")
        
        return result
    
    @classmethod
    def invalidate_aggregates(cls, entity_type: str, company_id: Optional[str] = None) -> None:
        """Invalidate all materialized aggregates for an entity type."""
        logger.info(f"Invalidating materialized aggregates for {entity_type}")
        # In production, would use Redis SCAN


class ReportingPresets:
    """
    Defines common reporting aggregates that should be pre-computed.
    """
    
    # Lead aggregates
    LEAD_AGGREGATES = [
        {
            'name': 'leads_by_status',
            'type': 'count',
            'field': 'id',
            'dimensions': ['status'],
        },
        {
            'name': 'leads_by_source',
            'type': 'count',
            'field': 'id',
            'dimensions': ['source'],
        },
        {
            'name': 'avg_lead_score',
            'type': 'avg',
            'field': 'lead_score',
            'dimensions': [],
        },
        {
            'name': 'leads_by_owner',
            'type': 'count',
            'field': 'id',
            'dimensions': ['owner_id'],
        },
        {
            'name': 'leads_by_date',
            'type': 'count',
            'field': 'id',
            'dimensions': ['created_date'],
            'time_dimension': 'day',
        },
    ]
    
    # Deal aggregates
    DEAL_AGGREGATES = [
        {
            'name': 'deals_by_stage',
            'type': 'count',
            'field': 'id',
            'dimensions': ['stage'],
        },
        {
            'name': 'revenue_by_stage',
            'type': 'sum',
            'field': 'amount',
            'dimensions': ['stage'],
        },
        {
            'name': 'avg_deal_size',
            'type': 'avg',
            'field': 'amount',
            'dimensions': [],
        },
        {
            'name': 'deals_by_owner',
            'type': 'count',
            'field': 'id',
            'dimensions': ['owner_id'],
        },
        {
            'name': 'revenue_by_month',
            'type': 'sum',
            'field': 'amount',
            'dimensions': ['close_date'],
            'time_dimension': 'month',
        },
    ]
    
    # Account aggregates
    ACCOUNT_AGGREGATES = [
        {
            'name': 'accounts_by_type',
            'type': 'count',
            'field': 'id',
            'dimensions': ['type'],
        },
        {
            'name': 'accounts_by_industry',
            'type': 'count',
            'field': 'id',
            'dimensions': ['industry'],
        },
        {
            'name': 'total_revenue',
            'type': 'sum',
            'field': 'annual_revenue',
            'dimensions': [],
        },
    ]
    
    @classmethod
    def get_aggregates_for_entity(cls, entity_type: str) -> List[Dict[str, Any]]:
        """Get preset aggregates for an entity type."""
        if entity_type == 'lead':
            return cls.LEAD_AGGREGATES
        elif entity_type == 'deal':
            return cls.DEAL_AGGREGATES
        elif entity_type == 'account':
            return cls.ACCOUNT_AGGREGATES
        else:
            return []


class ReportingOptimizer:
    """
    Combines query plan caching and materialized aggregates for optimized reporting.
    """
    
    @classmethod
    def execute_report(cls, report_config: Dict[str, Any],
                      model_class: Optional[models.Model] = None,
                      company_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute optimized report query.
        
        Args:
            report_config: Report configuration with aggregates and filters
            model_class: Django model class
            company_id: Optional company UUID
            
        Returns:
            Report results with aggregates
        """
        entity_type = report_config.get('entity_type')
        aggregates = report_config.get('aggregates', [])
        filters = report_config.get('filters', {})
        
        logger.info(f"Executing optimized report for {entity_type}")
        
        results = {}
        
        for aggregate_config in aggregates:
            aggregate_name = aggregate_config['name']
            
            # Try to get from cache
            cached_agg = MaterializedAggregateManager.get_cached_aggregate(
                entity_type, aggregate_name, company_id,
                aggregate_config.get('dimensions', []), filters
            )
            
            if cached_agg:
                results[aggregate_name] = cached_agg
            else:
                # Compute and cache
                if model_class:
                    agg_result = MaterializedAggregateManager.materialize_aggregate(
                        entity_type, aggregate_config, model_class, company_id, filters
                    )
                    
                    MaterializedAggregateManager.cache_aggregate(
                        entity_type, aggregate_config, agg_result, company_id, filters
                    )
                    
                    results[aggregate_name] = agg_result
        
        return {
            'entity_type': entity_type,
            'aggregates': results,
            'executed_at': timezone.now().isoformat()
        }
    
    @classmethod
    def precompute_common_reports(cls, entity_type: str, model_class: models.Model,
                                 company_id: Optional[str] = None) -> None:
        """
        Precompute common report aggregates.
        Should be run periodically (e.g., via Celery task).
        
        Args:
            entity_type: Type of entity
            model_class: Django model class
            company_id: Optional company UUID
        """
        logger.info(f"Precomputing common reports for {entity_type}")
        
        aggregates = ReportingPresets.get_aggregates_for_entity(entity_type)
        
        for aggregate_config in aggregates:
            try:
                # Materialize aggregate
                result = MaterializedAggregateManager.materialize_aggregate(
                    entity_type, aggregate_config, model_class, company_id
                )
                
                # Cache it
                MaterializedAggregateManager.cache_aggregate(
                    entity_type, aggregate_config, result, company_id
                )
                
                logger.info(f"Precomputed {aggregate_config['name']}")
            except Exception as e:
                logger.error(f"Error precomputing {aggregate_config['name']}: {e}")
