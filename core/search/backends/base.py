# core/search/backends/base.py
# Base search backend interface

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..schemas import SearchQuery, SearchResult


class BaseSearchBackend(ABC):
    """
    Abstract base class for search backends.
    All search engines must implement this interface.
    """
    
    @abstractmethod
    def search(
        self, 
        query: SearchQuery, 
        models: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Execute search query across specified models.
        
        Args:
            query: SearchQuery object with search parameters
            models: List of model names to search (e.g., ['Account', 'Contact', 'Lead'])
                   If None, searches all supported models
        
        Returns:
            List of SearchResult objects with scores
        """
        pass
    
    @abstractmethod
    def index_record(self, model: str, record_id: str, data: Dict[str, Any]) -> bool:
        """
        Index a single record for search.
        
        Args:
            model: Model name (e.g., 'Account', 'Contact')
            record_id: Unique identifier for the record
            data: Dictionary of fields to index
        
        Returns:
            True if indexing successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_record(self, model: str, record_id: str) -> bool:
        """
        Remove a record from search index.
        
        Args:
            model: Model name
            record_id: Unique identifier for the record
        
        Returns:
            True if deletion successful, False otherwise
        """
        pass
    
    @abstractmethod
    def bulk_index(self, model: str, records: List[Dict[str, Any]]) -> int:
        """
        Index multiple records in bulk.
        
        Args:
            model: Model name
            records: List of record dictionaries with 'id' and data fields
        
        Returns:
            Number of successfully indexed records
        """
        pass
    
    @abstractmethod
    def rebuild_index(self, models: Optional[List[str]] = None) -> bool:
        """
        Rebuild search index for specified models.
        
        Args:
            models: List of model names to rebuild. If None, rebuilds all.
        
        Returns:
            True if rebuild successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_suggestions(
        self, 
        query: str, 
        field: str, 
        limit: int = 10
    ) -> List[str]:
        """
        Get autocomplete suggestions for a query.
        
        Args:
            query: Partial search query
            field: Field to get suggestions from (e.g., 'name', 'email')
            limit: Maximum number of suggestions
        
        Returns:
            List of suggestion strings
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check backend health and return status information.
        
        Returns:
            Dictionary with health status and metrics
        """
        pass
    
    def get_backend_name(self) -> str:
        """
        Get the name of this backend.
        
        Returns:
            Backend name as string
        """
        return self.__class__.__name__
