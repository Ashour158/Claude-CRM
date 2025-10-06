# core/search/service.py
# Global search service for Phase 3

from django.db.models import Q, Value, IntegerField
from django.core.cache import cache
from crm.models import Account, Contact, Lead
from deals.models import Deal
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GlobalSearchService:
    """
    Service for performing global search across multiple models.
    Provides basic union search with scoring heuristics.
    """
    
    # Search configuration
    SEARCH_MODELS = {
        'account': Account,
        'contact': Contact,
        'lead': Lead,
        'deal': Deal,
    }
    
    # Field weights for scoring
    FIELD_WEIGHTS = {
        'name': 10,
        'email': 8,
        'company_name': 7,
        'title': 6,
        'description': 3,
        'notes': 2,
    }
    
    # Cache TTL (seconds)
    CACHE_TTL = 30
    
    def __init__(self, company, user=None):
        """
        Initialize search service.
        
        Args:
            company: Company instance to scope search
            user: Optional user for permission filtering
        """
        self.company = company
        self.user = user
    
    def search(self, query: str, entity_types: List[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Perform global search across specified entity types.
        
        Args:
            query: Search query string
            entity_types: List of entity types to search (e.g., ['account', 'contact'])
                         If None, searches all types
            limit: Maximum results per entity type
        
        Returns:
            Dictionary with search results organized by entity type
        """
        if not query or len(query.strip()) < 2:
            return {
                'query': query,
                'total_results': 0,
                'results': {},
                'cached': False
            }
        
        query = query.strip()
        
        # Try cache first
        cache_key = self._get_cache_key(query, entity_types, limit)
        cached_results = cache.get(cache_key)
        if cached_results:
            cached_results['cached'] = True
            return cached_results
        
        # Determine which entity types to search
        if entity_types:
            search_types = {k: v for k, v in self.SEARCH_MODELS.items() if k in entity_types}
        else:
            search_types = self.SEARCH_MODELS
        
        # Perform search on each entity type
        results = {}
        total_count = 0
        
        for entity_type, model in search_types.items():
            try:
                entity_results = self._search_entity(model, entity_type, query, limit)
                if entity_results:
                    results[entity_type] = entity_results
                    total_count += len(entity_results)
            except Exception as e:
                logger.error(f"Error searching {entity_type}: {e}")
                continue
        
        # Build response
        response = {
            'query': query,
            'total_results': total_count,
            'results': results,
            'cached': False
        }
        
        # Cache results
        cache.set(cache_key, response, self.CACHE_TTL)
        
        return response
    
    def _search_entity(self, model, entity_type: str, query: str, limit: int) -> List[Dict]:
        """
        Search a specific entity type.
        
        Args:
            model: Django model class
            entity_type: Entity type name
            query: Search query
            limit: Maximum results
        
        Returns:
            List of result dictionaries with scoring
        """
        # Build search filters based on entity type
        search_filters = self._build_search_filters(entity_type, query)
        
        if not search_filters:
            return []
        
        # Execute query
        queryset = model.objects.filter(
            Q(company=self.company) & search_filters
        ).distinct()[:limit]
        
        # Convert to result dictionaries with scoring
        results = []
        for obj in queryset:
            result = self._serialize_result(obj, entity_type, query)
            results.append(result)
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def _build_search_filters(self, entity_type: str, query: str) -> Q:
        """
        Build Q object filters for an entity type.
        """
        filters = Q()
        
        if entity_type == 'account':
            filters |= Q(name__icontains=query)
            filters |= Q(domain__icontains=query)
            filters |= Q(industry__icontains=query)
            filters |= Q(description__icontains=query)
        
        elif entity_type == 'contact':
            filters |= Q(first_name__icontains=query)
            filters |= Q(last_name__icontains=query)
            filters |= Q(email__icontains=query)
            filters |= Q(title__icontains=query)
            if hasattr(Contact, 'phone'):
                filters |= Q(phone__icontains=query)
        
        elif entity_type == 'lead':
            filters |= Q(first_name__icontains=query)
            filters |= Q(last_name__icontains=query)
            filters |= Q(email__icontains=query)
            filters |= Q(company_name__icontains=query)
            filters |= Q(title__icontains=query)
        
        elif entity_type == 'deal':
            filters |= Q(name__icontains=query)
            filters |= Q(description__icontains=query)
            # Also search related account name
            filters |= Q(account__name__icontains=query)
        
        return filters
    
    def _serialize_result(self, obj, entity_type: str, query: str) -> Dict:
        """
        Convert a model instance to a search result dictionary.
        Also calculates a relevance score.
        """
        result = {
            'id': str(obj.id),
            'type': entity_type,
            'score': 0,
        }
        
        # Entity-specific serialization
        if entity_type == 'account':
            result.update({
                'title': obj.name,
                'subtitle': obj.industry if hasattr(obj, 'industry') and obj.industry else '',
                'description': obj.description[:200] if obj.description else '',
                'metadata': {
                    'domain': obj.domain if hasattr(obj, 'domain') else None,
                }
            })
            # Calculate score
            if query.lower() in obj.name.lower():
                result['score'] += self.FIELD_WEIGHTS['name']
            if obj.description and query.lower() in obj.description.lower():
                result['score'] += self.FIELD_WEIGHTS['description']
        
        elif entity_type == 'contact':
            full_name = f"{obj.first_name} {obj.last_name}".strip()
            result.update({
                'title': full_name,
                'subtitle': obj.email,
                'description': obj.title if hasattr(obj, 'title') and obj.title else '',
                'metadata': {
                    'account': obj.account.name if hasattr(obj, 'account') and obj.account else None,
                }
            })
            # Calculate score
            if query.lower() in full_name.lower():
                result['score'] += self.FIELD_WEIGHTS['name']
            if query.lower() in obj.email.lower():
                result['score'] += self.FIELD_WEIGHTS['email']
            if hasattr(obj, 'title') and obj.title and query.lower() in obj.title.lower():
                result['score'] += self.FIELD_WEIGHTS['title']
        
        elif entity_type == 'lead':
            full_name = f"{obj.first_name} {obj.last_name}".strip()
            result.update({
                'title': full_name,
                'subtitle': obj.email,
                'description': obj.company_name if hasattr(obj, 'company_name') and obj.company_name else '',
                'metadata': {
                    'status': obj.status if hasattr(obj, 'status') else None,
                    'source': obj.source if hasattr(obj, 'source') else None,
                }
            })
            # Calculate score
            if query.lower() in full_name.lower():
                result['score'] += self.FIELD_WEIGHTS['name']
            if query.lower() in obj.email.lower():
                result['score'] += self.FIELD_WEIGHTS['email']
            if hasattr(obj, 'company_name') and obj.company_name and query.lower() in obj.company_name.lower():
                result['score'] += self.FIELD_WEIGHTS['company_name']
        
        elif entity_type == 'deal':
            result.update({
                'title': obj.name,
                'subtitle': obj.account.name if obj.account else '',
                'description': obj.description[:200] if obj.description else '',
                'metadata': {
                    'amount': str(obj.amount) if obj.amount else None,
                    'stage': obj.stage,
                    'status': obj.status,
                }
            })
            # Calculate score
            if query.lower() in obj.name.lower():
                result['score'] += self.FIELD_WEIGHTS['name']
            if obj.account and query.lower() in obj.account.name.lower():
                result['score'] += self.FIELD_WEIGHTS['company_name']
            if obj.description and query.lower() in obj.description.lower():
                result['score'] += self.FIELD_WEIGHTS['description']
        
        # Default score if no matches (should not happen due to filters)
        if result['score'] == 0:
            result['score'] = 1
        
        return result
    
    def _get_cache_key(self, query: str, entity_types: List[str], limit: int) -> str:
        """
        Generate cache key for search results.
        """
        types_str = '_'.join(sorted(entity_types)) if entity_types else 'all'
        return f"global_search:{self.company.id}:{query}:{types_str}:{limit}"
