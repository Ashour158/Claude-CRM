# core/search/__init__.py
# Search abstraction layer

from .service import SearchService
from .backends import PostgresSearchBackend, ExternalSearchBackend
from .schemas import SearchResult, SearchQuery
from .filters import GDPRFilter

__all__ = [
    'SearchService',
    'PostgresSearchBackend',
    'ExternalSearchBackend',
    'SearchResult',
    'SearchQuery',
    'GDPRFilter',
]
