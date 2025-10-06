# core/search/__init__.py
# Global search module exports

from .service import GlobalSearchService
from .views import GlobalSearchView, SearchSuggestionsView

__all__ = ['GlobalSearchService', 'GlobalSearchView', 'SearchSuggestionsView']
