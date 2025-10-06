# core/search/service.py
# Main search service facade

from typing import List, Dict, Any, Optional
import time
import logging
from django.conf import settings

from .backends.base import BaseSearchBackend
from .backends.postgres import PostgresSearchBackend
from .backends.external import ExternalSearchBackend
from .schemas import SearchQuery, SearchResult, SearchResponse, SearchScoringConfig
from .filters import GDPRFilter

logger = logging.getLogger(__name__)


class SearchService:
    """
    Main search service facade that abstracts backend implementation.
    Provides unified interface for search operations across different backends.
    """
    
    # Backend registry
    _backends = {
        'postgres': PostgresSearchBackend,
        'external': ExternalSearchBackend,
    }
    
    def __init__(self, backend_name: str = None, config: Dict[str, Any] = None):
        """
        Initialize search service with specified backend.
        
        Args:
            backend_name: Name of backend to use ('postgres' or 'external')
                         If None, uses value from settings.SEARCH_BACKEND
            config: Backend-specific configuration
        """
        # Get backend from settings or parameter
        self.backend_name = backend_name or getattr(
            settings, 'SEARCH_BACKEND', 'postgres'
        )
        
        # Get configuration from settings or parameter
        self.config = config or getattr(
            settings, 'SEARCH_CONFIG', {}
        )
        
        # Initialize backend
        self.backend = self._create_backend()
        
        # Initialize GDPR filter
        gdpr_config = self.config.get('gdpr', {})
        self.gdpr_filter = GDPRFilter(gdpr_config)
        
        # Initialize scoring config
        scoring_config_dict = self.config.get('scoring', {})
        self.scoring_config = SearchScoringConfig(**scoring_config_dict) if scoring_config_dict else SearchScoringConfig()
        
        logger.info(f"SearchService initialized with {self.backend_name} backend")
    
    def _create_backend(self) -> BaseSearchBackend:
        """Create backend instance"""
        backend_class = self._backends.get(self.backend_name)
        if not backend_class:
            logger.warning(f"Unknown backend: {self.backend_name}, falling back to postgres")
            backend_class = PostgresSearchBackend
        
        # Create backend with config
        backend_config = self.config.get('backend', {})
        
        if backend_class == PostgresSearchBackend:
            return backend_class(self.scoring_config)
        elif backend_class == ExternalSearchBackend:
            return backend_class(backend_config)
        else:
            return backend_class()
    
    def search(
        self,
        query_string: str,
        company_id: str,
        user_id: str = None,
        user_role: str = None,
        models: Optional[List[str]] = None,
        filters: Dict[str, Any] = None,
        fuzzy: bool = True,
        max_results: int = 50,
        offset: int = 0,
        apply_gdpr: bool = True,
    ) -> SearchResponse:
        """
        Execute search across CRM models.
        
        Args:
            query_string: Search query string
            company_id: Company ID for multi-tenant isolation
            user_id: ID of user performing search (for GDPR filtering)
            user_role: Role of user performing search (for GDPR filtering)
            models: List of model names to search (None = all)
            filters: Additional filters to apply
            fuzzy: Enable fuzzy matching
            max_results: Maximum number of results to return
            offset: Pagination offset
            apply_gdpr: Whether to apply GDPR filtering
        
        Returns:
            SearchResponse with results and metadata
        """
        start_time = time.time()
        
        # Build search query
        search_query = SearchQuery(
            query_string=query_string,
            company_id=company_id,
            user_id=user_id,
            fuzzy=fuzzy,
            max_results=max_results,
            offset=offset,
            filters=filters or {},
            boost_fields=self.scoring_config.field_weights,
        )
        
        try:
            # Execute search
            results = self.backend.search(search_query, models)
            
            # Apply GDPR filtering if enabled
            filters_applied = []
            if apply_gdpr:
                results = self._apply_gdpr_filtering(results, user_id, user_role)
                filters_applied.append('GDPR')
            
            # Build response
            execution_time = (time.time() - start_time) * 1000
            
            response = SearchResponse(
                query=search_query,
                results=results,
                total_count=len(results),
                execution_time_ms=execution_time,
                backend=self.backend.get_backend_name(),
                filters_applied=filters_applied,
            )
            
            logger.info(
                f"Search completed: query='{query_string}', "
                f"results={len(results)}, time={execution_time:.2f}ms"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            # Return empty response on error
            return SearchResponse(
                query=search_query,
                results=[],
                total_count=0,
                execution_time_ms=(time.time() - start_time) * 1000,
                backend=self.backend.get_backend_name(),
            )
    
    def _apply_gdpr_filtering(
        self, 
        results: List[SearchResult],
        user_id: str = None,
        user_role: str = None
    ) -> List[SearchResult]:
        """Apply GDPR filtering to search results"""
        filtered_results = []
        
        for result in results:
            # Filter data
            filtered_data = self.gdpr_filter.filter_result(
                result.data,
                user_id=user_id,
                user_role=user_role
            )
            
            # Update result
            result.data = filtered_data
            result.pii_filtered = (filtered_data != result.data)
            
            filtered_results.append(result)
        
        return filtered_results
    
    def get_suggestions(
        self,
        query: str,
        field: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get autocomplete suggestions.
        
        Args:
            query: Partial query string
            field: Field to get suggestions from
            limit: Maximum number of suggestions
        
        Returns:
            List of suggestion strings
        """
        try:
            return self.backend.get_suggestions(query, field, limit)
        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}", exc_info=True)
            return []
    
    def index_record(
        self,
        model: str,
        record_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Index a single record for search.
        
        Args:
            model: Model name
            record_id: Record ID
            data: Record data to index
        
        Returns:
            True if successful
        """
        try:
            return self.backend.index_record(model, record_id, data)
        except Exception as e:
            logger.error(f"Failed to index record: {e}", exc_info=True)
            return False
    
    def delete_record(self, model: str, record_id: str) -> bool:
        """
        Delete a record from search index.
        
        Args:
            model: Model name
            record_id: Record ID
        
        Returns:
            True if successful
        """
        try:
            return self.backend.delete_record(model, record_id)
        except Exception as e:
            logger.error(f"Failed to delete record: {e}", exc_info=True)
            return False
    
    def bulk_index(self, model: str, records: List[Dict[str, Any]]) -> int:
        """
        Index multiple records in bulk.
        
        Args:
            model: Model name
            records: List of records to index
        
        Returns:
            Number of successfully indexed records
        """
        try:
            return self.backend.bulk_index(model, records)
        except Exception as e:
            logger.error(f"Failed to bulk index: {e}", exc_info=True)
            return 0
    
    def rebuild_index(self, models: Optional[List[str]] = None) -> bool:
        """
        Rebuild search index.
        
        Args:
            models: List of model names (None = all)
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Rebuilding search index for: {models or 'all models'}")
            return self.backend.rebuild_index(models)
        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}", exc_info=True)
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check search backend health.
        
        Returns:
            Health status dictionary
        """
        try:
            backend_health = self.backend.health_check()
            return {
                'service': 'SearchService',
                'backend': self.backend_name,
                'status': backend_health.get('status', 'unknown'),
                'details': backend_health,
                'gdpr_enabled': self.config.get('gdpr', {}).get('mask_pii', False),
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return {
                'service': 'SearchService',
                'backend': self.backend_name,
                'status': 'unhealthy',
                'error': str(e),
            }
    
    def switch_backend(self, backend_name: str) -> bool:
        """
        Switch to a different search backend.
        
        Args:
            backend_name: Name of backend to switch to
        
        Returns:
            True if successful
        """
        try:
            if backend_name not in self._backends:
                logger.error(f"Unknown backend: {backend_name}")
                return False
            
            self.backend_name = backend_name
            self.backend = self._create_backend()
            
            logger.info(f"Switched to {backend_name} backend")
            return True
        except Exception as e:
            logger.error(f"Failed to switch backend: {e}", exc_info=True)
            return False
    
    @classmethod
    def register_backend(cls, name: str, backend_class: type):
        """
        Register a custom search backend.
        
        Args:
            name: Backend name
            backend_class: Backend class (must inherit from BaseSearchBackend)
        """
        if not issubclass(backend_class, BaseSearchBackend):
            raise ValueError("Backend must inherit from BaseSearchBackend")
        
        cls._backends[name] = backend_class
        logger.info(f"Registered custom backend: {name}")
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about current backend"""
        return {
            'name': self.backend_name,
            'class': self.backend.__class__.__name__,
            'available_backends': list(self._backends.keys()),
        }
