# analytics/vector_search.py
# Vector search index with OpenSearch kNN/pgvector support and fallback

import logging
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class VectorSearchBackend(ABC):
    """Abstract base class for vector search backends."""
    
    @abstractmethod
    def index_document(self, doc_id: str, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """Index a document with its vector embedding."""
        pass
    
    @abstractmethod
    def search(self, query_vector: List[float], k: int = 10, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index."""
        pass
    
    @abstractmethod
    def bulk_index(self, documents: List[Dict[str, Any]]) -> bool:
        """Bulk index multiple documents."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the backend is available."""
        pass


class OpenSearchKNNBackend(VectorSearchBackend):
    """
    OpenSearch k-NN backend for vector search.
    Uses OpenSearch's k-NN plugin for approximate nearest neighbor search.
    """
    
    def __init__(self, host: str, port: int, index_name: str, dimension: int = 768):
        """
        Initialize OpenSearch k-NN backend.
        
        Args:
            host: OpenSearch host
            port: OpenSearch port
            index_name: Name of the index
            dimension: Vector dimension size
        """
        self.host = host
        self.port = port
        self.index_name = index_name
        self.dimension = dimension
        self.client = None
        
        try:
            # Would initialize OpenSearch client here
            # from opensearchpy import OpenSearch
            # self.client = OpenSearch([{'host': host, 'port': port}])
            logger.info(f"Initialized OpenSearch backend: {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenSearch: {e}")
    
    def _create_index(self) -> bool:
        """Create k-NN index if it doesn't exist."""
        if not self.client:
            return False
        
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            },
            "mappings": {
                "properties": {
                    "vector": {
                        "type": "knn_vector",
                        "dimension": self.dimension,
                        "method": {
                            "name": "hnsw",
                            "space_type": "l2",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 24
                            }
                        }
                    },
                    "metadata": {
                        "type": "object",
                        "enabled": True
                    }
                }
            }
        }
        
        try:
            # self.client.indices.create(index=self.index_name, body=index_body)
            logger.info(f"Created OpenSearch index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
    def index_document(self, doc_id: str, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """Index a document with its vector."""
        if not self.client:
            logger.warning("OpenSearch client not initialized")
            return False
        
        if len(vector) != self.dimension:
            logger.error(f"Vector dimension mismatch: {len(vector)} != {self.dimension}")
            return False
        
        document = {
            "vector": vector,
            "metadata": metadata
        }
        
        try:
            # self.client.index(index=self.index_name, id=doc_id, body=document)
            logger.debug(f"Indexed document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            return False
    
    def search(self, query_vector: List[float], k: int = 10, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors using k-NN."""
        if not self.client:
            logger.warning("OpenSearch client not initialized")
            return []
        
        query = {
            "size": k,
            "query": {
                "knn": {
                    "vector": {
                        "vector": query_vector,
                        "k": k
                    }
                }
            }
        }
        
        # Add filters if provided
        if filters:
            query["query"] = {
                "bool": {
                    "must": [query["query"]],
                    "filter": [{"term": {key: value}} for key, value in filters.items()]
                }
            }
        
        try:
            # response = self.client.search(index=self.index_name, body=query)
            # results = [
            #     {
            #         'id': hit['_id'],
            #         'score': hit['_score'],
            #         'metadata': hit['_source']['metadata']
            #     }
            #     for hit in response['hits']['hits']
            # ]
            results = []  # Placeholder
            return results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document."""
        if not self.client:
            return False
        
        try:
            # self.client.delete(index=self.index_name, id=doc_id)
            logger.debug(f"Deleted document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def bulk_index(self, documents: List[Dict[str, Any]]) -> bool:
        """Bulk index multiple documents."""
        if not self.client:
            return False
        
        # Prepare bulk operations
        # bulk_data = []
        # for doc in documents:
        #     bulk_data.append({"index": {"_index": self.index_name, "_id": doc['id']}})
        #     bulk_data.append({"vector": doc['vector'], "metadata": doc['metadata']})
        
        try:
            # self.client.bulk(body=bulk_data)
            logger.info(f"Bulk indexed {len(documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Error bulk indexing: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check OpenSearch health."""
        if not self.client:
            return False
        
        try:
            # health = self.client.cluster.health()
            # return health['status'] in ['green', 'yellow']
            return False  # Placeholder
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


class PgVectorBackend(VectorSearchBackend):
    """
    PostgreSQL pgvector backend for vector search.
    Uses pgvector extension for vector similarity search.
    """
    
    def __init__(self, dimension: int = 768):
        """
        Initialize pgvector backend.
        
        Args:
            dimension: Vector dimension size
        """
        self.dimension = dimension
        logger.info(f"Initialized pgvector backend with dimension {dimension}")
    
    def _ensure_extension(self) -> bool:
        """Ensure pgvector extension is installed."""
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            logger.info("pgvector extension ensured")
            return True
        except Exception as e:
            logger.error(f"Error ensuring pgvector extension: {e}")
            return False
    
    def index_document(self, doc_id: str, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """Index a document with its vector."""
        from django.db import connection
        
        if len(vector) != self.dimension:
            logger.error(f"Vector dimension mismatch: {len(vector)} != {self.dimension}")
            return False
        
        # Convert vector to pgvector format
        vector_str = f"[{','.join(map(str, vector))}]"
        metadata_json = json.dumps(metadata)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO vector_search_index (doc_id, vector, metadata, indexed_at)
                    VALUES (%s, %s::vector, %s, NOW())
                    ON CONFLICT (doc_id) DO UPDATE SET
                        vector = EXCLUDED.vector,
                        metadata = EXCLUDED.metadata,
                        indexed_at = NOW()
                    """,
                    [doc_id, vector_str, metadata_json]
                )
            logger.debug(f"Indexed document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            return False
    
    def search(self, query_vector: List[float], k: int = 10, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors using cosine similarity."""
        from django.db import connection
        
        if len(query_vector) != self.dimension:
            logger.error(f"Query vector dimension mismatch")
            return []
        
        vector_str = f"[{','.join(map(str, query_vector))}]"
        
        # Build WHERE clause for filters
        where_clause = ""
        params = [vector_str, k]
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"metadata->>{repr(key)} = %s")
                params.insert(-1, value)
            where_clause = "WHERE " + " AND ".join(conditions)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT doc_id, metadata, 1 - (vector <=> %s::vector) as similarity
                    FROM vector_search_index
                    {where_clause}
                    ORDER BY vector <=> %s::vector
                    LIMIT %s
                    """,
                    params
                )
                
                results = [
                    {
                        'id': row[0],
                        'metadata': json.loads(row[1]) if isinstance(row[1], str) else row[1],
                        'score': float(row[2])
                    }
                    for row in cursor.fetchall()
                ]
            
            logger.debug(f"Found {len(results)} similar documents")
            return results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document."""
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM vector_search_index WHERE doc_id = %s", [doc_id])
            logger.debug(f"Deleted document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def bulk_index(self, documents: List[Dict[str, Any]]) -> bool:
        """Bulk index multiple documents."""
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                for doc in documents:
                    vector_str = f"[{','.join(map(str, doc['vector']))}]"
                    metadata_json = json.dumps(doc['metadata'])
                    
                    cursor.execute(
                        """
                        INSERT INTO vector_search_index (doc_id, vector, metadata, indexed_at)
                        VALUES (%s, %s::vector, %s, NOW())
                        ON CONFLICT (doc_id) DO UPDATE SET
                            vector = EXCLUDED.vector,
                            metadata = EXCLUDED.metadata,
                            indexed_at = NOW()
                        """,
                        [doc['id'], vector_str, metadata_json]
                    )
            
            logger.info(f"Bulk indexed {len(documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Error bulk indexing: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if pgvector is available."""
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


class FallbackSearchBackend(VectorSearchBackend):
    """
    Fallback search backend using traditional text search when vector search is unavailable.
    """
    
    def index_document(self, doc_id: str, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """Store metadata for text search fallback."""
        cache_key = f"fallback:doc:{doc_id}"
        cache.set(cache_key, metadata, timeout=86400)  # 24 hours
        logger.debug(f"Stored fallback metadata for: {doc_id}")
        return True
    
    def search(self, query_vector: List[float], k: int = 10, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Fallback to text-based search."""
        logger.warning("Using fallback search (vector search unavailable)")
        
        # This would implement traditional text search
        # For now, return empty results
        return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete fallback metadata."""
        cache_key = f"fallback:doc:{doc_id}"
        cache.delete(cache_key)
        return True
    
    def bulk_index(self, documents: List[Dict[str, Any]]) -> bool:
        """Bulk store fallback metadata."""
        for doc in documents:
            self.index_document(doc['id'], doc.get('vector', []), doc['metadata'])
        return True
    
    def health_check(self) -> bool:
        """Fallback is always available."""
        return True


class VectorSearchManager:
    """
    Manages vector search with automatic backend selection and fallback.
    """
    
    def __init__(self, dimension: int = 768):
        """
        Initialize vector search manager.
        
        Args:
            dimension: Vector dimension size
        """
        self.dimension = dimension
        self.backend = None
        self._initialize_backend()
    
    def _initialize_backend(self) -> None:
        """Initialize the best available backend."""
        # Try OpenSearch first
        if self._try_opensearch():
            logger.info("Using OpenSearch k-NN backend")
            return
        
        # Try pgvector
        if self._try_pgvector():
            logger.info("Using pgvector backend")
            return
        
        # Fall back to traditional search
        logger.warning("Vector search unavailable, using fallback")
        self.backend = FallbackSearchBackend()
    
    def _try_opensearch(self) -> bool:
        """Try to initialize OpenSearch backend."""
        try:
            host = getattr(settings, 'OPENSEARCH_HOST', 'localhost')
            port = getattr(settings, 'OPENSEARCH_PORT', 9200)
            index_name = getattr(settings, 'VECTOR_INDEX_NAME', 'crm_vectors')
            
            backend = OpenSearchKNNBackend(host, port, index_name, self.dimension)
            if backend.health_check():
                self.backend = backend
                return True
        except Exception as e:
            logger.debug(f"OpenSearch not available: {e}")
        
        return False
    
    def _try_pgvector(self) -> bool:
        """Try to initialize pgvector backend."""
        try:
            backend = PgVectorBackend(self.dimension)
            if backend.health_check():
                self.backend = backend
                return True
        except Exception as e:
            logger.debug(f"pgvector not available: {e}")
        
        return False
    
    def index(self, doc_id: str, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """Index a document."""
        if not self.backend:
            logger.error("No backend available")
            return False
        
        return self.backend.index_document(doc_id, vector, metadata)
    
    def search(self, query_vector: List[float], k: int = 10, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.backend:
            logger.error("No backend available")
            return []
        
        return self.backend.search(query_vector, k, filters)
    
    def delete(self, doc_id: str) -> bool:
        """Delete a document."""
        if not self.backend:
            return False
        
        return self.backend.delete_document(doc_id)
    
    def bulk_index(self, documents: List[Dict[str, Any]]) -> bool:
        """Bulk index documents."""
        if not self.backend:
            return False
        
        return self.backend.bulk_index(documents)


# Global vector search manager instance
vector_search_manager = VectorSearchManager()
