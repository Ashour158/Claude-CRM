# analytics/search_optimization.py
# Search facet precomputation layer and window caching

import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class FacetConfig:
    """Configuration for search facets."""
    
    # Common facet fields across entities
    COMMON_FACETS = {
        'status': {'type': 'terms', 'size': 50},
        'priority': {'type': 'terms', 'size': 20},
        'owner': {'type': 'terms', 'size': 100},
        'created_date': {'type': 'date_histogram', 'interval': 'month'},
        'modified_date': {'type': 'date_histogram', 'interval': 'week'},
    }
    
    # Entity-specific facets
    ENTITY_FACETS = {
        'lead': {
            'source': {'type': 'terms', 'size': 30},
            'industry': {'type': 'terms', 'size': 50},
            'lead_score': {'type': 'range', 'ranges': [(0, 25), (26, 50), (51, 75), (76, 100)]},
        },
        'deal': {
            'stage': {'type': 'terms', 'size': 20},
            'probability': {'type': 'range', 'ranges': [(0, 25), (26, 50), (51, 75), (76, 100)]},
            'amount': {'type': 'range', 'ranges': [(0, 10000), (10001, 50000), (50001, 100000), (100001, None)]},
        },
        'account': {
            'type': {'type': 'terms', 'size': 20},
            'industry': {'type': 'terms', 'size': 50},
            'revenue': {'type': 'range', 'ranges': [(0, 100000), (100001, 1000000), (1000001, 10000000), (10000001, None)]},
        },
        'contact': {
            'role': {'type': 'terms', 'size': 30},
            'department': {'type': 'terms', 'size': 40},
        }
    }
    
    # Precomputation schedule (in seconds)
    PRECOMPUTE_INTERVAL = 300  # 5 minutes
    PRECOMPUTE_TIMEOUT = 3600  # 1 hour cache
    
    # Window sizes for trending facets
    WINDOW_SIZES = {
        'hour': 3600,
        'day': 86400,
        'week': 604800,
        'month': 2592000
    }


class FacetPrecomputer:
    """
    Precomputes search facets for faster query response.
    Runs periodically to update cached facet data.
    """
    
    CACHE_PREFIX = 'facets:precomputed'
    CACHE_VERSION = 'v1'
    
    @classmethod
    def get_cache_key(cls, entity_type: str, facet_name: str, 
                      company_id: Optional[str] = None, filters: Optional[Dict] = None) -> str:
        """Generate cache key for precomputed facet."""
        filter_hash = ''
        if filters:
            filter_hash = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:8]
        
        if company_id:
            key_data = f"{cls.CACHE_PREFIX}:{cls.CACHE_VERSION}:{company_id}:{entity_type}:{facet_name}:{filter_hash}"
        else:
            key_data = f"{cls.CACHE_PREFIX}:{cls.CACHE_VERSION}:global:{entity_type}:{facet_name}:{filter_hash}"
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @classmethod
    def precompute_facet(cls, entity_type: str, facet_name: str, facet_config: Dict[str, Any],
                        model_class: models.Model, company_id: Optional[str] = None,
                        filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Precompute facet values for an entity type.
        
        Args:
            entity_type: Type of entity (lead, deal, account, contact)
            facet_name: Name of the facet field
            facet_config: Facet configuration
            model_class: Django model class
            company_id: Optional company UUID for multi-tenant filtering
            filters: Additional filters to apply
            
        Returns:
            Dictionary with facet results
        """
        logger.info(f"Precomputing facet {entity_type}.{facet_name}")
        
        # Build base queryset
        queryset = model_class.objects.all()
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        if filters:
            queryset = queryset.filter(**filters)
        
        facet_type = facet_config.get('type', 'terms')
        
        if facet_type == 'terms':
            # Count distinct values
            result = cls._compute_terms_facet(queryset, facet_name, facet_config)
        elif facet_type == 'range':
            # Aggregate by ranges
            result = cls._compute_range_facet(queryset, facet_name, facet_config)
        elif facet_type == 'date_histogram':
            # Aggregate by date intervals
            result = cls._compute_date_histogram_facet(queryset, facet_name, facet_config)
        else:
            result = {'error': f'Unknown facet type: {facet_type}'}
        
        # Add metadata
        result['_meta'] = {
            'entity_type': entity_type,
            'facet_name': facet_name,
            'computed_at': timezone.now().isoformat(),
            'total_records': queryset.count()
        }
        
        return result
    
    @classmethod
    def _compute_terms_facet(cls, queryset, field_name: str, config: Dict) -> Dict[str, Any]:
        """Compute terms facet (distinct value counts)."""
        from django.db.models import Count
        
        size = config.get('size', 50)
        
        # Group by field and count
        values = (
            queryset.values(field_name)
            .annotate(count=Count('id'))
            .order_by('-count')[:size]
        )
        
        return {
            'type': 'terms',
            'field': field_name,
            'buckets': [
                {'key': v[field_name], 'doc_count': v['count']}
                for v in values
            ]
        }
    
    @classmethod
    def _compute_range_facet(cls, queryset, field_name: str, config: Dict) -> Dict[str, Any]:
        """Compute range facet (value ranges)."""
        from django.db.models import Q
        
        ranges = config.get('ranges', [])
        buckets = []
        
        for range_spec in ranges:
            from_val, to_val = range_spec
            
            q = Q()
            if from_val is not None:
                q &= Q(**{f'{field_name}__gte': from_val})
            if to_val is not None:
                q &= Q(**{f'{field_name}__lt': to_val})
            
            count = queryset.filter(q).count()
            
            buckets.append({
                'key': f'{from_val}-{to_val}' if to_val else f'{from_val}+',
                'from': from_val,
                'to': to_val,
                'doc_count': count
            })
        
        return {
            'type': 'range',
            'field': field_name,
            'buckets': buckets
        }
    
    @classmethod
    def _compute_date_histogram_facet(cls, queryset, field_name: str, config: Dict) -> Dict[str, Any]:
        """Compute date histogram facet."""
        from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
        from django.db.models import Count
        
        interval = config.get('interval', 'month')
        
        # Choose truncation function based on interval
        if interval == 'month':
            trunc_func = TruncMonth
        elif interval == 'week':
            trunc_func = TruncWeek
        else:
            trunc_func = TruncDay
        
        # Group by truncated date
        values = (
            queryset.annotate(period=trunc_func(field_name))
            .values('period')
            .annotate(count=Count('id'))
            .order_by('period')
        )
        
        return {
            'type': 'date_histogram',
            'field': field_name,
            'interval': interval,
            'buckets': [
                {
                    'key': v['period'].isoformat() if v['period'] else None,
                    'doc_count': v['count']
                }
                for v in values
            ]
        }
    
    @classmethod
    def cache_facet(cls, entity_type: str, facet_name: str, result: Dict[str, Any],
                   company_id: Optional[str] = None, filters: Optional[Dict] = None,
                   timeout: Optional[int] = None) -> None:
        """Cache precomputed facet result."""
        cache_key = cls.get_cache_key(entity_type, facet_name, company_id, filters)
        timeout = timeout or FacetConfig.PRECOMPUTE_TIMEOUT
        
        cache.set(cache_key, result, timeout)
        logger.info(f"Cached facet {entity_type}.{facet_name}")
    
    @classmethod
    def get_cached_facet(cls, entity_type: str, facet_name: str,
                        company_id: Optional[str] = None, 
                        filters: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Get cached facet result."""
        cache_key = cls.get_cache_key(entity_type, facet_name, company_id, filters)
        result = cache.get(cache_key)
        
        if result:
            logger.debug(f"Cache hit for facet {entity_type}.{facet_name}")
        else:
            logger.debug(f"Cache miss for facet {entity_type}.{facet_name}")
        
        return result
    
    @classmethod
    def invalidate_facets(cls, entity_type: str, company_id: Optional[str] = None) -> None:
        """Invalidate all cached facets for an entity type."""
        logger.info(f"Invalidating facets for {entity_type}")
        # In production, would use Redis SCAN to find and delete matching keys


class WindowCache:
    """
    Implements sliding window caching for search results.
    Caches result windows (pages) to avoid re-querying.
    """
    
    CACHE_PREFIX = 'search:window'
    CACHE_VERSION = 'v1'
    DEFAULT_TIMEOUT = 600  # 10 minutes
    
    @classmethod
    def get_cache_key(cls, entity_type: str, query_hash: str, 
                      window_start: int, window_size: int) -> str:
        """Generate cache key for result window."""
        key_data = f"{cls.CACHE_PREFIX}:{cls.CACHE_VERSION}:{entity_type}:{query_hash}:{window_start}:{window_size}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @classmethod
    def compute_query_hash(cls, query_params: Dict[str, Any]) -> str:
        """Compute hash for query parameters."""
        # Sort and serialize query params for consistent hashing
        query_str = json.dumps(query_params, sort_keys=True)
        return hashlib.md5(query_str.encode()).hexdigest()
    
    @classmethod
    def cache_window(cls, entity_type: str, query_params: Dict[str, Any],
                    window_start: int, window_size: int, results: List[Dict],
                    timeout: Optional[int] = None) -> None:
        """
        Cache a result window.
        
        Args:
            entity_type: Type of entity
            query_params: Query parameters
            window_start: Start offset of the window
            window_size: Size of the window
            results: List of result dictionaries
            timeout: Cache timeout in seconds
        """
        query_hash = cls.compute_query_hash(query_params)
        cache_key = cls.get_cache_key(entity_type, query_hash, window_start, window_size)
        timeout = timeout or cls.DEFAULT_TIMEOUT
        
        window_data = {
            'results': results,
            'window_start': window_start,
            'window_size': window_size,
            'cached_at': timezone.now().isoformat()
        }
        
        cache.set(cache_key, window_data, timeout)
        logger.info(f"Cached search window {entity_type} [{window_start}:{window_start+window_size}]")
    
    @classmethod
    def get_window(cls, entity_type: str, query_params: Dict[str, Any],
                  window_start: int, window_size: int) -> Optional[Dict[str, Any]]:
        """Get cached result window."""
        query_hash = cls.compute_query_hash(query_params)
        cache_key = cls.get_cache_key(entity_type, query_hash, window_start, window_size)
        
        window_data = cache.get(cache_key)
        
        if window_data:
            logger.debug(f"Cache hit for search window {entity_type} [{window_start}:{window_start+window_size}]")
        else:
            logger.debug(f"Cache miss for search window {entity_type} [{window_start}:{window_start+window_size}]")
        
        return window_data
    
    @classmethod
    def invalidate_windows(cls, entity_type: str) -> None:
        """Invalidate all cached windows for an entity type."""
        logger.info(f"Invalidating search windows for {entity_type}")
        # In production, would use Redis SCAN


class SearchOptimizer:
    """
    Combines facet precomputation and window caching for optimized search.
    """
    
    @classmethod
    def execute_search(cls, entity_type: str, query_params: Dict[str, Any],
                      page: int = 1, page_size: int = 50,
                      model_class: Optional[models.Model] = None,
                      company_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute optimized search with caching.
        
        Args:
            entity_type: Type of entity to search
            query_params: Search query parameters
            page: Page number (1-indexed)
            page_size: Results per page
            model_class: Django model class
            company_id: Optional company UUID
            
        Returns:
            Search results with facets
        """
        window_start = (page - 1) * page_size
        
        # Try to get cached window
        cached_window = WindowCache.get_window(
            entity_type, query_params, window_start, page_size
        )
        
        if cached_window:
            results = cached_window['results']
        else:
            # Execute search query
            if model_class:
                queryset = model_class.objects.all()
                if company_id:
                    queryset = queryset.filter(company_id=company_id)
                
                # Apply search filters
                # ... (would implement actual search logic here)
                
                results = list(queryset[window_start:window_start + page_size].values())
                
                # Cache the window
                WindowCache.cache_window(
                    entity_type, query_params, window_start, page_size, results
                )
            else:
                results = []
        
        # Get precomputed facets
        facets = cls.get_facets_for_entity(entity_type, company_id, query_params)
        
        return {
            'results': results,
            'facets': facets,
            'page': page,
            'page_size': page_size,
            'total': len(results)  # Would get actual count from database
        }
    
    @classmethod
    def get_facets_for_entity(cls, entity_type: str, company_id: Optional[str] = None,
                             filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Get all facets for an entity type, using cache when available."""
        entity_facets = FacetConfig.ENTITY_FACETS.get(entity_type, {})
        common_facets = FacetConfig.COMMON_FACETS
        
        all_facets = {**common_facets, **entity_facets}
        
        result_facets = {}
        
        for facet_name, facet_config in all_facets.items():
            # Try to get from cache
            cached_facet = FacetPrecomputer.get_cached_facet(
                entity_type, facet_name, company_id, filters
            )
            
            if cached_facet:
                result_facets[facet_name] = cached_facet
            else:
                # Would trigger precomputation or return empty facet
                result_facets[facet_name] = {
                    'type': facet_config['type'],
                    'field': facet_name,
                    'buckets': [],
                    '_meta': {'status': 'not_computed'}
                }
        
        return result_facets
