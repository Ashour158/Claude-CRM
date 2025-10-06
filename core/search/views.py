# core/search/views.py
# API views for search

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import logging

from .service import SearchService
from .serializers import (
    SearchRequestSerializer,
    SearchResponseSerializer,
    AutocompleteRequestSerializer,
    AutocompleteResponseSerializer
)

logger = logging.getLogger(__name__)


class SearchView(APIView):
    """
    Global search endpoint across all CRM models.
    
    POST /api/v1/search/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Execute search query.
        
        Request body:
        {
            "query": "search terms",
            "models": ["Account", "Contact"],  // Optional
            "filters": {"is_active": true},    // Optional
            "fuzzy": true,                      // Optional
            "max_results": 50,                  // Optional
            "offset": 0,                        // Optional
            "apply_gdpr": true                  // Optional
        }
        """
        # Validate request
        serializer = SearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        try:
            # Get company ID from request user
            company_id = self._get_company_id(request.user)
            if not company_id:
                return Response(
                    {'error': 'User not associated with a company'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get user role for GDPR filtering
            user_role = self._get_user_role(request.user)
            
            # Initialize search service
            search_service = SearchService()
            
            # Execute search
            response = search_service.search(
                query_string=data['query'],
                company_id=company_id,
                user_id=str(request.user.id),
                user_role=user_role,
                models=data.get('models'),
                filters=data.get('filters', {}),
                fuzzy=data.get('fuzzy', True),
                max_results=data.get('max_results', 50),
                offset=data.get('offset', 0),
                apply_gdpr=data.get('apply_gdpr', True),
            )
            
            # Serialize response
            response_dict = response.to_dict()
            
            return Response(response_dict, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return Response(
                {'error': 'Search failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_company_id(self, user):
        """Get company ID for the user"""
        # Check if user has company access
        if hasattr(user, 'company_access'):
            access = user.company_access.filter(is_active=True).first()
            if access:
                return str(access.company_id)
        return None
    
    def _get_user_role(self, user):
        """Get user role for GDPR filtering"""
        if hasattr(user, 'company_access'):
            access = user.company_access.filter(is_active=True).first()
            if access:
                return access.role
        return None


class AutocompleteView(APIView):
    """
    Autocomplete suggestions endpoint.
    
    GET /api/v1/search/autocomplete/?query=test&field=name&limit=10
    """
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def get(self, request):
        """
        Get autocomplete suggestions.
        
        Query parameters:
        - query: Partial query string
        - field: Field to get suggestions from
        - limit: Maximum number of suggestions (default: 10)
        """
        # Validate request
        serializer = AutocompleteRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        try:
            # Initialize search service
            search_service = SearchService()
            
            # Get suggestions
            suggestions = search_service.get_suggestions(
                query=data['query'],
                field=data['field'],
                limit=data.get('limit', 10)
            )
            
            # Serialize response
            response_serializer = AutocompleteResponseSerializer({
                'suggestions': suggestions
            })
            
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Autocomplete failed: {e}", exc_info=True)
            return Response(
                {'error': 'Autocomplete failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SearchHealthView(APIView):
    """
    Search service health check endpoint.
    
    GET /api/v1/search/health/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Check search service health"""
        try:
            search_service = SearchService()
            health = search_service.health_check()
            
            status_code = (
                status.HTTP_200_OK if health.get('status') == 'healthy'
                else status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
            return Response(health, status=status_code)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return Response(
                {
                    'service': 'SearchService',
                    'status': 'unhealthy',
                    'error': str(e)
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
