# core/search/backends/__init__.py
# Search backend implementations

from .base import BaseSearchBackend
from .postgres import PostgresSearchBackend
from .external import ExternalSearchBackend

__all__ = [
    'BaseSearchBackend',
    'PostgresSearchBackend',
    'ExternalSearchBackend',
]
