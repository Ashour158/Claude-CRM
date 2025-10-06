# core/search/backends/external.py
# External search engine backend (Meilisearch, OpenSearch, etc.)

from typing import List, Dict, Any, Optional
import time
import logging

from .base import BaseSearchBackend
from ..schemas import SearchQuery, SearchResult

logger = logging.getLogger(__name__)


class ExternalSearchBackend(BaseSearchBackend):
    """
    External search engine backend for services like Meilisearch, OpenSearch, Elasticsearch.
    This is a stub implementation that can be extended for specific search engines.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize external search backend.
        
        Args:
            config: Configuration dictionary with:
                - engine: 'meilisearch', 'opensearch', 'elasticsearch'
                - host: Search engine host URL
                - api_key: Authentication key
                - index_prefix: Prefix for index names
        """
        self.config = config or {}
        self.engine = self.config.get('engine', 'meilisearch')
        self.host = self.config.get('host', 'http://localhost:7700')
        self.api_key = self.config.get('api_key', '')
        self.index_prefix = self.config.get('index_prefix', 'crm_')
        self.client = None
        
        # Initialize client if config is provided
        if self.config:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize search engine client"""
        try:
            if self.engine == 'meilisearch':
                self._initialize_meilisearch()
            elif self.engine == 'opensearch':
                self._initialize_opensearch()
            elif self.engine == 'elasticsearch':
                self._initialize_elasticsearch()
            else:
                logger.warning(f"Unknown search engine: {self.engine}")
        except Exception as e:
            logger.error(f"Failed to initialize {self.engine} client: {e}", exc_info=True)
    
    def _initialize_meilisearch(self):
        """Initialize Meilisearch client"""
        try:
            import meilisearch
            self.client = meilisearch.Client(self.host, self.api_key)
            logger.info(f"Initialized Meilisearch client at {self.host}")
        except ImportError:
            logger.warning("meilisearch package not installed. Install with: pip install meilisearch")
        except Exception as e:
            logger.error(f"Failed to initialize Meilisearch: {e}", exc_info=True)
    
    def _initialize_opensearch(self):
        """Initialize OpenSearch client"""
        try:
            from opensearchpy import OpenSearch
            self.client = OpenSearch(
                hosts=[self.host],
                http_auth=(self.config.get('username'), self.config.get('password')),
                use_ssl=True,
                verify_certs=True,
            )
            logger.info(f"Initialized OpenSearch client at {self.host}")
        except ImportError:
            logger.warning("opensearch-py package not installed. Install with: pip install opensearch-py")
        except Exception as e:
            logger.error(f"Failed to initialize OpenSearch: {e}", exc_info=True)
    
    def _initialize_elasticsearch(self):
        """Initialize Elasticsearch client"""
        try:
            from elasticsearch import Elasticsearch
            self.client = Elasticsearch(
                [self.host],
                api_key=self.api_key,
            )
            logger.info(f"Initialized Elasticsearch client at {self.host}")
        except ImportError:
            logger.warning("elasticsearch package not installed. Install with: pip install elasticsearch")
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch: {e}", exc_info=True)
    
    def search(
        self, 
        query: SearchQuery, 
        models: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Execute search query using external search engine.
        """
        if not self.client:
            logger.warning("External search client not initialized, returning empty results")
            return []
        
        start_time = time.time()
        results = []
        
        try:
            if self.engine == 'meilisearch':
                results = self._search_meilisearch(query, models)
            elif self.engine == 'opensearch':
                results = self._search_opensearch(query, models)
            elif self.engine == 'elasticsearch':
                results = self._search_elasticsearch(query, models)
            else:
                logger.warning(f"Search not implemented for engine: {self.engine}")
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
        
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"External search completed in {execution_time:.2f}ms, found {len(results)} results")
        
        return results
    
    def _search_meilisearch(self, query: SearchQuery, models: Optional[List[str]]) -> List[SearchResult]:
        """Search using Meilisearch"""
        results = []
        search_models = models or ['Account', 'Contact', 'Lead', 'Deal']
        
        for model in search_models:
            try:
                index_name = f"{self.index_prefix}{model.lower()}"
                index = self.client.index(index_name)
                
                # Execute search
                search_params = {
                    'limit': query.max_results,
                    'offset': query.offset,
                }
                
                # Add filters
                if query.filters:
                    filter_parts = []
                    for key, value in query.filters.items():
                        filter_parts.append(f'{key} = "{value}"')
                    if filter_parts:
                        search_params['filter'] = ' AND '.join(filter_parts)
                
                response = index.search(query.query_string, search_params)
                
                # Convert to SearchResult
                for hit in response['hits']:
                    results.append(SearchResult(
                        model=model,
                        record_id=str(hit['id']),
                        score=hit.get('_rankingScore', 50.0) * 100,
                        data=hit,
                        matched_fields=hit.get('_formatted', {}).keys() if '_formatted' in hit else [],
                    ))
            except Exception as e:
                logger.error(f"Error searching {model} in Meilisearch: {e}", exc_info=True)
        
        return results
    
    def _search_opensearch(self, query: SearchQuery, models: Optional[List[str]]) -> List[SearchResult]:
        """Search using OpenSearch"""
        results = []
        search_models = models or ['Account', 'Contact', 'Lead', 'Deal']
        
        for model in search_models:
            try:
                index_name = f"{self.index_prefix}{model.lower()}"
                
                # Build query
                body = {
                    'query': {
                        'multi_match': {
                            'query': query.query_string,
                            'fields': ['*'],
                            'fuzziness': 'AUTO' if query.fuzzy else '0',
                        }
                    },
                    'size': query.max_results,
                    'from': query.offset,
                }
                
                # Add filters
                if query.filters:
                    bool_query = {
                        'bool': {
                            'must': body['query'],
                            'filter': []
                        }
                    }
                    for key, value in query.filters.items():
                        bool_query['bool']['filter'].append({'term': {key: value}})
                    body['query'] = bool_query
                
                response = self.client.search(index=index_name, body=body)
                
                # Convert to SearchResult
                for hit in response['hits']['hits']:
                    results.append(SearchResult(
                        model=model,
                        record_id=str(hit['_id']),
                        score=hit['_score'] * 10,  # Normalize score
                        data=hit['_source'],
                        matched_fields=hit.get('matched_queries', []),
                    ))
            except Exception as e:
                logger.error(f"Error searching {model} in OpenSearch: {e}", exc_info=True)
        
        return results
    
    def _search_elasticsearch(self, query: SearchQuery, models: Optional[List[str]]) -> List[SearchResult]:
        """Search using Elasticsearch"""
        # Similar to OpenSearch implementation
        return self._search_opensearch(query, models)
    
    def index_record(self, model: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Index a single record in external search engine"""
        if not self.client:
            return False
        
        try:
            index_name = f"{self.index_prefix}{model.lower()}"
            
            if self.engine == 'meilisearch':
                index = self.client.index(index_name)
                data['id'] = record_id
                index.add_documents([data])
            elif self.engine in ('opensearch', 'elasticsearch'):
                self.client.index(index=index_name, id=record_id, body=data)
            
            logger.debug(f"Indexed {model}:{record_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index {model}:{record_id}: {e}", exc_info=True)
            return False
    
    def delete_record(self, model: str, record_id: str) -> bool:
        """Delete a record from external search engine"""
        if not self.client:
            return False
        
        try:
            index_name = f"{self.index_prefix}{model.lower()}"
            
            if self.engine == 'meilisearch':
                index = self.client.index(index_name)
                index.delete_document(record_id)
            elif self.engine in ('opensearch', 'elasticsearch'):
                self.client.delete(index=index_name, id=record_id)
            
            logger.debug(f"Deleted {model}:{record_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {model}:{record_id}: {e}", exc_info=True)
            return False
    
    def bulk_index(self, model: str, records: List[Dict[str, Any]]) -> int:
        """Index multiple records in bulk"""
        if not self.client:
            return 0
        
        try:
            index_name = f"{self.index_prefix}{model.lower()}"
            
            if self.engine == 'meilisearch':
                index = self.client.index(index_name)
                index.add_documents(records)
                count = len(records)
            elif self.engine in ('opensearch', 'elasticsearch'):
                from elasticsearch.helpers import bulk
                actions = [
                    {
                        '_index': index_name,
                        '_id': record.get('id'),
                        '_source': record
                    }
                    for record in records
                ]
                count, _ = bulk(self.client, actions)
            else:
                count = 0
            
            logger.info(f"Bulk indexed {count} {model} records")
            return count
        except Exception as e:
            logger.error(f"Failed to bulk index {model}: {e}", exc_info=True)
            return 0
    
    def rebuild_index(self, models: Optional[List[str]] = None) -> bool:
        """Rebuild indexes for specified models"""
        if not self.client:
            return False
        
        try:
            from django.apps import apps
            
            search_models = models or ['Account', 'Contact', 'Lead', 'Deal']
            model_mapping = {
                'Account': 'crm.Account',
                'Contact': 'crm.Contact',
                'Lead': 'crm.Lead',
                'Deal': 'deals.Deal',
            }
            
            for model_name in search_models:
                if model_name not in model_mapping:
                    continue
                
                # Get Django model
                model = apps.get_model(model_mapping[model_name])
                
                # Get all records
                records = []
                for obj in model.objects.all():
                    record = {'id': str(obj.id)}
                    # Add searchable fields
                    for field in model._meta.fields:
                        field_name = field.name
                        if not field_name.startswith('_'):
                            value = getattr(obj, field_name, None)
                            if value is not None:
                                record[field_name] = str(value)
                    records.append(record)
                
                # Bulk index
                self.bulk_index(model_name, records)
                logger.info(f"Rebuilt index for {model_name}: {len(records)} records")
            
            return True
        except Exception as e:
            logger.error(f"Failed to rebuild indexes: {e}", exc_info=True)
            return False
    
    def get_suggestions(
        self, 
        query: str, 
        field: str, 
        limit: int = 10
    ) -> List[str]:
        """Get autocomplete suggestions"""
        # Stub implementation
        logger.warning("Autocomplete not yet implemented for external search")
        return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check external search engine health"""
        health = {
            'backend': 'ExternalSearchBackend',
            'engine': self.engine,
            'status': 'unknown',
            'client_initialized': self.client is not None,
        }
        
        if not self.client:
            health['status'] = 'not_configured'
            return health
        
        try:
            if self.engine == 'meilisearch':
                health_info = self.client.health()
                health['status'] = health_info.get('status', 'unknown')
            elif self.engine in ('opensearch', 'elasticsearch'):
                health_info = self.client.info()
                health['status'] = 'healthy'
                health['version'] = health_info.get('version', {}).get('number')
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
            logger.error(f"Health check failed: {e}", exc_info=True)
        
        return health
