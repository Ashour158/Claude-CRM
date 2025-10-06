# core/search/views.py
# Global search views

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .service import GlobalSearchService


class GlobalSearchView(APIView):
    """
    Global search endpoint across multiple entity types.
    
    GET /api/v1/search/?q=<query>&types=<comma-separated-types>&limit=<limit>
    
    Query parameters:
    - q: Search query string (required, min 2 characters)
    - types: Comma-separated list of entity types (optional, default: all)
            Valid types: account, contact, lead, deal
    - limit: Maximum results per entity type (optional, default: 50, max: 100)
    
    Example:
    /api/v1/search/?q=john&types=contact,lead&limit=20
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Handle global search request.
        """
        # Get query parameter
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({
                'error': 'Query parameter "q" is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(query) < 2:
            return Response({
                'error': 'Query must be at least 2 characters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get entity types filter
        types_param = request.query_params.get('types', '')
        entity_types = None
        if types_param:
            entity_types = [t.strip() for t in types_param.split(',') if t.strip()]
            
            # Validate entity types
            valid_types = ['account', 'contact', 'lead', 'deal']
            invalid_types = [t for t in entity_types if t not in valid_types]
            if invalid_types:
                return Response({
                    'error': f'Invalid entity types: {", ".join(invalid_types)}',
                    'valid_types': valid_types
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get limit
        try:
            limit = int(request.query_params.get('limit', '50'))
            limit = min(max(limit, 1), 100)  # Clamp between 1 and 100
        except ValueError:
            limit = 50
        
        # Get company from request
        company = getattr(request, 'company', None)
        if not company:
            return Response({
                'error': 'No company context'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform search
        search_service = GlobalSearchService(company, request.user)
        results = search_service.search(query, entity_types, limit)
        
        return Response(results)


class SearchSuggestionsView(APIView):
    """
    Quick search suggestions endpoint.
    Returns top 5 results per entity type.
    
    GET /api/v1/search/suggestions/?q=<query>
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Handle search suggestions request.
        """
        query = request.query_params.get('q', '').strip()
        
        if not query or len(query) < 2:
            return Response({
                'suggestions': []
            })
        
        company = getattr(request, 'company', None)
        if not company:
            return Response({
                'error': 'No company context'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform search with limit of 5 per type
        search_service = GlobalSearchService(company, request.user)
        results = search_service.search(query, None, 5)
        
        # Flatten results for suggestions
        suggestions = []
        for entity_type, entities in results['results'].items():
            for entity in entities:
                suggestions.append({
                    'type': entity_type,
                    'id': entity['id'],
                    'text': entity['title'],
                    'subtitle': entity['subtitle'],
                })
        
        # Sort by score if available
        suggestions.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return Response({
            'query': query,
            'suggestions': suggestions[:20]  # Top 20 overall
        })
