# core/search/backends/postgres.py
# Postgres full-text search backend with trigram support

from typing import List, Dict, Any, Optional
import time
from django.db import connection
from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Greatest, Coalesce
from django.contrib.postgres.search import (
    SearchVector, SearchQuery as DjangoSearchQuery, SearchRank, TrigramSimilarity
)
from django.apps import apps
import logging

from .base import BaseSearchBackend
from ..schemas import SearchQuery, SearchResult, SearchScoringConfig

logger = logging.getLogger(__name__)


class PostgresSearchBackend(BaseSearchBackend):
    """
    PostgreSQL-based search backend using full-text search and trigram similarity.
    Supports fuzzy matching, relevance ranking, and cross-model search.
    """
    
    # Map model names to Django model classes
    SEARCHABLE_MODELS = {
        'Account': 'crm.Account',
        'Contact': 'crm.Contact',
        'Lead': 'crm.Lead',
        'Deal': 'deals.Deal',
    }
    
    # Define searchable fields for each model
    SEARCH_FIELDS = {
        'Account': ['name', 'email', 'phone', 'website', 'industry', 'description'],
        'Contact': ['first_name', 'last_name', 'full_name', 'email', 'phone', 'mobile', 'title', 'department'],
        'Lead': ['first_name', 'last_name', 'full_name', 'company_name', 'email', 'phone', 'mobile', 'industry'],
        'Deal': ['name', 'description'],
    }
    
    # PII fields that need special handling
    PII_FIELDS = {'email', 'phone', 'mobile', 'fax', 'date_of_birth'}
    
    def __init__(self, scoring_config: Optional[SearchScoringConfig] = None):
        """Initialize with scoring configuration"""
        self.scoring_config = scoring_config or SearchScoringConfig()
    
    def search(
        self, 
        query: SearchQuery, 
        models: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Execute search across specified models using Postgres full-text search.
        """
        start_time = time.time()
        results = []
        
        # Determine which models to search
        search_models = models or list(self.SEARCHABLE_MODELS.keys())
        
        for model_name in search_models:
            if model_name not in self.SEARCHABLE_MODELS:
                logger.warning(f"Model {model_name} not searchable, skipping")
                continue
            
            try:
                model_results = self._search_model(query, model_name)
                results.extend(model_results)
            except Exception as e:
                logger.error(f"Error searching {model_name}: {e}", exc_info=True)
        
        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        
        # Apply offset and limit
        results = results[query.offset:query.offset + query.max_results]
        
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Search completed in {execution_time:.2f}ms, found {len(results)} results")
        
        return results
    
    def _search_model(self, query: SearchQuery, model_name: str) -> List[SearchResult]:
        """Search a specific model"""
        # Get Django model
        model_path = self.SEARCHABLE_MODELS[model_name]
        model = apps.get_model(model_path)
        
        # Get searchable fields
        search_fields = self.SEARCH_FIELDS.get(model_name, [])
        if not search_fields:
            return []
        
        # Build base queryset with company filter
        queryset = model.objects.filter(company_id=query.company_id)
        
        # Filter active records unless specified
        if not query.include_inactive and hasattr(model, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        # Apply additional filters
        for filter_key, filter_value in query.filters.items():
            if hasattr(model, filter_key):
                queryset = queryset.filter(**{filter_key: filter_value})
        
        # Use trigram similarity for fuzzy matching
        if query.fuzzy:
            results = self._fuzzy_search(queryset, query.query_string, search_fields, model_name)
        else:
            results = self._exact_search(queryset, query.query_string, search_fields, model_name)
        
        return results
    
    def _fuzzy_search(
        self, 
        queryset, 
        query_string: str, 
        search_fields: List[str],
        model_name: str
    ) -> List[SearchResult]:
        """Perform fuzzy search using trigram similarity"""
        results = []
        
        # Calculate similarity for each field and take the maximum
        similarity_annotations = {}
        for field in search_fields:
            if hasattr(queryset.model, field):
                similarity_annotations[f'{field}_similarity'] = TrigramSimilarity(field, query_string)
        
        if not similarity_annotations:
            return []
        
        # Annotate with similarities
        queryset = queryset.annotate(**similarity_annotations)
        
        # Calculate max similarity across all fields
        max_similarity_fields = [F(key) for key in similarity_annotations.keys()]
        queryset = queryset.annotate(
            max_similarity=Greatest(*max_similarity_fields)
        )
        
        # Filter by minimum similarity threshold (0.1 = 10% similarity)
        queryset = queryset.filter(max_similarity__gte=0.1)
        
        # Order by similarity
        queryset = queryset.order_by('-max_similarity')
        
        # Limit results for performance
        queryset = queryset[:100]
        
        # Convert to SearchResult objects
        for record in queryset:
            score = float(record.max_similarity * 100)  # Convert to 0-100 scale
            
            # Apply field weight boosting
            matched_fields = []
            for field in search_fields:
                similarity_key = f'{field}_similarity'
                if hasattr(record, similarity_key):
                    field_similarity = getattr(record, similarity_key, 0)
                    if field_similarity > 0.1:
                        matched_fields.append(field)
                        # Apply field weight
                        field_weight = self.scoring_config.get_field_weight(field)
                        score *= (1 + (field_weight * 0.1))
            
            # Apply recency boost if applicable
            if hasattr(record, 'updated_at'):
                from datetime import datetime, timezone
                days_old = (datetime.now(timezone.utc) - record.updated_at).days
                if days_old < self.scoring_config.recency_decay_days:
                    recency_factor = 1 - (days_old / self.scoring_config.recency_decay_days)
                    score *= (1 + recency_factor * 0.2)
            
            # Cap score at 100
            score = min(score, 100.0)
            
            # Extract record data
            data = self._extract_record_data(record, search_fields)
            
            results.append(SearchResult(
                model=model_name,
                record_id=str(record.id),
                score=score,
                data=data,
                matched_fields=matched_fields,
            ))
        
        return results
    
    def _exact_search(
        self, 
        queryset, 
        query_string: str, 
        search_fields: List[str],
        model_name: str
    ) -> List[SearchResult]:
        """Perform exact/prefix search"""
        results = []
        
        # Build Q object for OR search across fields
        q_objects = Q()
        for field in search_fields:
            if hasattr(queryset.model, field):
                # Case-insensitive contains
                q_objects |= Q(**{f'{field}__icontains': query_string})
        
        queryset = queryset.filter(q_objects)
        queryset = queryset[:100]
        
        # Convert to SearchResult objects
        for record in queryset:
            # Calculate simple score based on matches
            matched_fields = []
            score = 50.0  # Base score for exact match
            
            for field in search_fields:
                if hasattr(record, field):
                    field_value = str(getattr(record, field, '') or '')
                    if query_string.lower() in field_value.lower():
                        matched_fields.append(field)
                        field_weight = self.scoring_config.get_field_weight(field)
                        score += field_weight
            
            score = min(score, 100.0)
            
            # Extract record data
            data = self._extract_record_data(record, search_fields)
            
            results.append(SearchResult(
                model=model_name,
                record_id=str(record.id),
                score=score,
                data=data,
                matched_fields=matched_fields,
            ))
        
        return results
    
    def _extract_record_data(self, record, fields: List[str]) -> Dict[str, Any]:
        """Extract searchable data from a record"""
        data = {
            'id': str(record.id),
        }
        
        # Extract specified fields
        for field in fields:
            if hasattr(record, field):
                value = getattr(record, field, None)
                if value is not None:
                    data[field] = str(value) if not isinstance(value, (str, int, float, bool)) else value
        
        # Add commonly needed fields
        if hasattr(record, 'created_at'):
            data['created_at'] = record.created_at.isoformat()
        if hasattr(record, 'updated_at'):
            data['updated_at'] = record.updated_at.isoformat()
        
        return data
    
    def index_record(self, model: str, record_id: str, data: Dict[str, Any]) -> bool:
        """
        For Postgres backend, indexing is automatic via database triggers.
        This method is a no-op but maintains interface compatibility.
        """
        return True
    
    def delete_record(self, model: str, record_id: str) -> bool:
        """
        For Postgres backend, deletion is automatic.
        This method is a no-op but maintains interface compatibility.
        """
        return True
    
    def bulk_index(self, model: str, records: List[Dict[str, Any]]) -> int:
        """
        For Postgres backend, indexing is automatic.
        This method is a no-op but maintains interface compatibility.
        """
        return len(records)
    
    def rebuild_index(self, models: Optional[List[str]] = None) -> bool:
        """
        Rebuild search indexes by running VACUUM and ANALYZE.
        """
        try:
            with connection.cursor() as cursor:
                search_models = models or list(self.SEARCHABLE_MODELS.keys())
                
                for model_name in search_models:
                    if model_name in self.SEARCHABLE_MODELS:
                        model = apps.get_model(self.SEARCHABLE_MODELS[model_name])
                        table_name = model._meta.db_table
                        
                        # Analyze table for query planning
                        cursor.execute(f'ANALYZE {table_name};')
                        logger.info(f"Analyzed table: {table_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error rebuilding indexes: {e}", exc_info=True)
            return False
    
    def get_suggestions(
        self, 
        query: str, 
        field: str, 
        limit: int = 10
    ) -> List[str]:
        """
        Get autocomplete suggestions using trigram similarity.
        """
        suggestions = []
        
        try:
            # Search across all models for the specified field
            for model_name, model_path in self.SEARCHABLE_MODELS.items():
                model = apps.get_model(model_path)
                
                if hasattr(model, field):
                    # Get distinct values with similarity
                    queryset = model.objects.annotate(
                        similarity=TrigramSimilarity(field, query)
                    ).filter(
                        similarity__gte=0.3
                    ).values_list(field, flat=True).distinct()[:limit]
                    
                    suggestions.extend([str(s) for s in queryset if s])
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}", exc_info=True)
        
        return list(set(suggestions))[:limit]
    
    def health_check(self) -> Dict[str, Any]:
        """Check Postgres connection and extension availability"""
        health = {
            'backend': 'PostgresSearchBackend',
            'status': 'healthy',
            'extensions': {},
            'tables': {}
        }
        
        try:
            with connection.cursor() as cursor:
                # Check pg_trgm extension
                cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm');")
                health['extensions']['pg_trgm'] = cursor.fetchone()[0]
                
                # Check table statistics
                for model_name, model_path in self.SEARCHABLE_MODELS.items():
                    model = apps.get_model(model_path)
                    health['tables'][model_name] = {
                        'table': model._meta.db_table,
                        'count': model.objects.count()
                    }
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
            logger.error(f"Health check failed: {e}", exc_info=True)
        
        return health
