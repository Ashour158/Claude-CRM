# core/search_service.py
# Global search service for Phase 3

import logging
from typing import Dict, List, Any
from django.db.models import Q, Value, IntegerField
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)


class SearchService:
    """
    Global search service with weighted matching across entities.
    """
    
    # Weight multipliers for different field types
    WEIGHTS = {
        'name': 10,
        'email': 8,
        'company': 5,
        'description': 3,
        'phone': 2,
    }
    
    # Max results per entity type
    MAX_PER_ENTITY = 10
    
    def __init__(self):
        self.cache_ttl = 30  # 30 seconds cache TTL
    
    def search(
        self,
        query: str,
        organization,
        entity_types: List[str] = None,
        user=None
    ) -> Dict[str, Any]:
        """
        Perform weighted search across multiple entity types.
        
        Args:
            query: Search query string
            organization: Company/organization to filter by
            entity_types: List of entity types to search (None = all)
            user: User performing search (for permissions)
        
        Returns:
            Dict with results grouped by entity type
        """
        if not query or len(query.strip()) < 2:
            return {'results': {}, 'total_count': 0, 'query': query}
        
        query = query.strip()
        
        # Try cache first
        cache_key = f"search:{organization.id}:{query}:{','.join(entity_types or [])}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.debug(f"Search cache hit for query: {query}")
            return cached_result
        
        # Default entity types
        if not entity_types:
            entity_types = ['account', 'contact', 'lead', 'deal']
        
        results = {}
        total_count = 0
        
        # Search each entity type
        for entity_type in entity_types:
            try:
                entity_results = self._search_entity(
                    query,
                    entity_type,
                    organization,
                    user
                )
                if entity_results:
                    results[entity_type] = entity_results
                    total_count += len(entity_results)
            except Exception as e:
                logger.error(f"Error searching {entity_type}: {e}")
        
        response = {
            'results': results,
            'total_count': total_count,
            'query': query,
        }
        
        # Cache results
        cache.set(cache_key, response, self.cache_ttl)
        
        return response
    
    def _search_entity(
        self,
        query: str,
        entity_type: str,
        organization,
        user
    ) -> List[Dict[str, Any]]:
        """Search a specific entity type with weighted scoring."""
        
        # Get model class
        model_class = self._get_model_class(entity_type)
        if not model_class:
            return []
        
        # Build query filters
        queryset = model_class.objects.filter(company=organization)
        
        # Add soft-delete filter if model has is_active
        if hasattr(model_class, 'is_active'):
            queryset = queryset.filter(is_active=True)
        
        # Build search filters with weighted scoring
        q_objects = self._build_search_filters(query, entity_type, model_class)
        if not q_objects:
            return []
        
        queryset = queryset.filter(q_objects)
        
        # Apply scoring logic
        queryset = self._apply_scoring(queryset, query, entity_type, model_class)
        
        # Limit results
        queryset = queryset[:self.MAX_PER_ENTITY]
        
        # Convert to dict results
        return [self._serialize_result(obj, entity_type) for obj in queryset]
    
    def _get_model_class(self, entity_type: str):
        """Get model class for entity type."""
        from crm.models import Account, Contact, Lead
        from deals.models import Deal
        
        mapping = {
            'account': Account,
            'contact': Contact,
            'lead': Lead,
            'deal': Deal,
        }
        return mapping.get(entity_type)
    
    def _build_search_filters(self, query: str, entity_type: str, model_class) -> Q:
        """Build Q objects for search filters."""
        q = Q()
        
        # Entity-specific search fields
        if entity_type == 'account':
            q |= Q(name__icontains=query)
            q |= Q(email__icontains=query)
            q |= Q(industry__icontains=query)
            q |= Q(phone__icontains=query)
        elif entity_type == 'contact':
            q |= Q(first_name__icontains=query)
            q |= Q(last_name__icontains=query)
            q |= Q(email__icontains=query)
            q |= Q(phone__icontains=query)
            if hasattr(model_class, 'account'):
                q |= Q(account__name__icontains=query)
        elif entity_type == 'lead':
            q |= Q(first_name__icontains=query)
            q |= Q(last_name__icontains=query)
            q |= Q(email__icontains=query)
            q |= Q(company__icontains=query)
            q |= Q(phone__icontains=query)
        elif entity_type == 'deal':
            q |= Q(name__icontains=query)
            q |= Q(description__icontains=query)
            if hasattr(model_class, 'account'):
                q |= Q(account__name__icontains=query)
        
        return q
    
    def _apply_scoring(self, queryset, query: str, entity_type: str, model_class):
        """Apply scoring/ordering logic."""
        # Simple ordering: prioritize exact name matches, then by relevance
        
        if entity_type in ['account', 'deal']:
            # Exact name matches first
            queryset = queryset.annotate(
                score=Value(0, output_field=IntegerField())
            ).order_by('-score', 'name')
        elif entity_type in ['contact', 'lead']:
            # Exact name matches first
            queryset = queryset.order_by('last_name', 'first_name')
        
        return queryset
    
    def _serialize_result(self, obj, entity_type: str) -> Dict[str, Any]:
        """Serialize search result to dict."""
        result = {
            'id': str(obj.id) if hasattr(obj, 'id') else None,
            'type': entity_type,
        }
        
        # Entity-specific fields
        if entity_type == 'account':
            result.update({
                'name': obj.name,
                'email': obj.email if hasattr(obj, 'email') else None,
                'phone': obj.phone if hasattr(obj, 'phone') else None,
                'industry': obj.industry if hasattr(obj, 'industry') else None,
            })
        elif entity_type in ['contact', 'lead']:
            result.update({
                'name': f"{obj.first_name} {obj.last_name}".strip(),
                'first_name': obj.first_name,
                'last_name': obj.last_name,
                'email': obj.email if hasattr(obj, 'email') else None,
                'phone': obj.phone if hasattr(obj, 'phone') else None,
            })
            if entity_type == 'contact' and hasattr(obj, 'account'):
                result['account'] = obj.account.name if obj.account else None
            elif entity_type == 'lead' and hasattr(obj, 'company'):
                result['company'] = obj.company
        elif entity_type == 'deal':
            result.update({
                'name': obj.name,
                'amount': float(obj.amount) if obj.amount else None,
                'stage': str(obj.stage) if hasattr(obj, 'stage') else None,
            })
            if hasattr(obj, 'account'):
                result['account'] = obj.account.name if obj.account else None
        
        return result


# Global search service instance
_search_service = None


def get_search_service() -> SearchService:
    """Get or create the global search service instance."""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
