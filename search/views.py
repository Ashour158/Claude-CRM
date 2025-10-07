# search/views.py
# Search and Knowledge Layer Views

import time
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from crm.models import Account, Contact, Lead
from deals.models import Deal
from .models import SearchCache, QueryExpansion, SearchMetric, RelationshipGraph
from .serializers import (
    QueryExpansionSerializer, SearchMetricSerializer,
    RelationshipGraphSerializer, SearchCacheSerializer
)
from .services import (
    QueryExpansionService, PersonalizedRankingService,
    FacetedSearchService, RelationshipGraphService,
    SearchCacheService, ExplainabilityService
)


class QueryExpansionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing query expansion terms"""
    queryset = QueryExpansion.objects.all()
    serializer_class = QueryExpansionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        company = getattr(self.request, 'company', None)
        if company:
            return QueryExpansion.objects.filter(company=company)
        return QueryExpansion.objects.none()
    
    def perform_create(self, serializer):
        company = getattr(self.request, 'company', None)
        serializer.save(company=company, created_by=self.request.user)


class SearchMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing search metrics"""
    queryset = SearchMetric.objects.all()
    serializer_class = SearchMetricSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        company = getattr(self.request, 'company', None)
        if company:
            return SearchMetric.objects.filter(company=company)
        return SearchMetric.objects.none()
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get search metrics summary"""
        company = getattr(request, 'company', None)
        if not company:
            return Response({'error': 'Company required'}, status=status.HTTP_400_BAD_REQUEST)
        
        metrics = SearchMetric.objects.filter(company=company)
        
        summary = {
            'total_searches': metrics.count(),
            'cache_hit_rate': 0,
            'avg_execution_time': 0,
            'popular_queries': [],
            'popular_entity_types': []
        }
        
        if metrics.exists():
            total = metrics.count()
            cache_hits = metrics.filter(cache_hit=True).count()
            summary['cache_hit_rate'] = cache_hits / total if total > 0 else 0
            
            from django.db.models import Avg
            avg_time = metrics.aggregate(Avg('execution_time_ms'))['execution_time_ms__avg']
            summary['avg_execution_time'] = round(avg_time, 2) if avg_time else 0
            
            # Popular queries
            from django.db.models import Count
            popular_queries = metrics.values('query').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            summary['popular_queries'] = list(popular_queries)
            
            # Popular entity types
            popular_types = metrics.values('entity_type').annotate(
                count=Count('id')
            ).order_by('-count')
            summary['popular_entity_types'] = list(popular_types)
        
        return Response(summary)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def advanced_search(request):
    """
    Advanced search with facets, ranking, and caching
    
    Query Parameters:
    - q: Search query (required)
    - entity_type: Comma-separated entity types (accounts, contacts, leads, deals)
    - owner: Filter by owner ID
    - status: Filter by status
    - territory: Filter by territory ID
    - explain: Include explainability (true/false)
    """
    start_time = time.time()
    
    company = getattr(request, 'company', None)
    if not company:
        return Response({'error': 'Company required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    query = request.GET.get('q', '').strip()
    if not query:
        return Response({'error': 'Query parameter "q" is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Parse entity types
    entity_types_param = request.GET.get('entity_type', 'accounts,contacts,leads,deals')
    entity_types = [e.strip() for e in entity_types_param.split(',') if e.strip()]
    
    # Parse facets
    facets = {}
    if request.GET.get('owner'):
        facets['owner'] = request.GET.get('owner')
    if request.GET.get('status'):
        facets['status'] = request.GET.get('status')
    if request.GET.get('territory'):
        facets['territory'] = request.GET.get('territory')
    
    explain = request.GET.get('explain', 'false').lower() == 'true'
    
    # Check cache
    cache_key = SearchCacheService.generate_cache_key(query, entity_types, facets, company.id)
    cached_results = SearchCacheService.get_cached_results(cache_key, company)
    
    if cached_results:
        execution_time = int((time.time() - start_time) * 1000)
        
        # Log metric
        SearchMetric.objects.create(
            company=company,
            user=user,
            query=query,
            entity_type=','.join(entity_types),
            result_count=cached_results['results'].get('total_results', 0),
            execution_time_ms=execution_time,
            cache_hit=True,
            facets_applied=facets
        )
        
        response_data = cached_results['results']
        response_data['cache_hit'] = True
        response_data['execution_time_ms'] = execution_time
        return Response(response_data)
    
    # Query expansion
    expanded_queries = QueryExpansionService.expand_query(query, company)
    
    # Search across entity types
    results = {}
    all_results = []
    
    if 'accounts' in entity_types:
        accounts_qs = Account.objects.filter(company=company)
        
        # Apply search
        q_filter = Q()
        for exp_query in expanded_queries:
            q_filter |= (
                Q(name__icontains=exp_query) |
                Q(email__icontains=exp_query) |
                Q(phone__icontains=exp_query) |
                Q(industry__icontains=exp_query)
            )
        accounts_qs = accounts_qs.filter(q_filter)
        
        # Apply facets
        accounts_qs = FacetedSearchService.apply_facets(accounts_qs, facets, 'accounts')
        
        # Rank results
        accounts_list = list(accounts_qs[:50])  # Limit to 50
        accounts_ranked = PersonalizedRankingService.rank_results(accounts_list, user, 'accounts')
        
        results['accounts'] = [
            {
                'id': str(a.id),
                'name': a.name,
                'type': a.type,
                'industry': a.industry,
                'owner': str(a.owner.id) if a.owner else None,
            }
            for a in accounts_ranked[:20]  # Top 20
        ]
        all_results.extend([(a, 'accounts') for a in accounts_ranked[:20]])
    
    if 'contacts' in entity_types:
        contacts_qs = Contact.objects.filter(company=company)
        
        # Apply search
        q_filter = Q()
        for exp_query in expanded_queries:
            q_filter |= (
                Q(first_name__icontains=exp_query) |
                Q(last_name__icontains=exp_query) |
                Q(email__icontains=exp_query) |
                Q(phone__icontains=exp_query)
            )
        contacts_qs = contacts_qs.filter(q_filter)
        
        # Apply facets
        contacts_qs = FacetedSearchService.apply_facets(contacts_qs, facets, 'contacts')
        
        # Rank results
        contacts_list = list(contacts_qs[:50])
        contacts_ranked = PersonalizedRankingService.rank_results(contacts_list, user, 'contacts')
        
        results['contacts'] = [
            {
                'id': str(c.id),
                'first_name': c.first_name,
                'last_name': c.last_name,
                'full_name': c.full_name,
                'email': c.email,
                'account': str(c.account.id) if c.account else None,
                'owner': str(c.owner.id) if c.owner else None,
            }
            for c in contacts_ranked[:20]
        ]
        all_results.extend([(c, 'contacts') for c in contacts_ranked[:20]])
    
    if 'leads' in entity_types:
        leads_qs = Lead.objects.filter(company=company)
        
        # Apply search
        q_filter = Q()
        for exp_query in expanded_queries:
            q_filter |= (
                Q(first_name__icontains=exp_query) |
                Q(last_name__icontains=exp_query) |
                Q(company_name__icontains=exp_query) |
                Q(email__icontains=exp_query)
            )
        leads_qs = leads_qs.filter(q_filter)
        
        # Apply facets
        leads_qs = FacetedSearchService.apply_facets(leads_qs, facets, 'leads')
        
        # Rank results
        leads_list = list(leads_qs[:50])
        leads_ranked = PersonalizedRankingService.rank_results(leads_list, user, 'leads')
        
        results['leads'] = [
            {
                'id': str(l.id),
                'first_name': l.first_name,
                'last_name': l.last_name,
                'company_name': l.company_name,
                'email': l.email,
                'status': l.status,
                'rating': l.rating,
                'owner': str(l.owner.id) if l.owner else None,
            }
            for l in leads_ranked[:20]
        ]
        all_results.extend([(l, 'leads') for l in leads_ranked[:20]])
    
    if 'deals' in entity_types:
        deals_qs = Deal.objects.filter(company=company)
        
        # Apply search
        q_filter = Q()
        for exp_query in expanded_queries:
            q_filter |= (
                Q(name__icontains=exp_query) |
                Q(description__icontains=exp_query)
            )
        deals_qs = deals_qs.filter(q_filter)
        
        # Apply facets
        deals_qs = FacetedSearchService.apply_facets(deals_qs, facets, 'deals')
        
        # Rank results
        deals_list = list(deals_qs[:50])
        deals_ranked = PersonalizedRankingService.rank_results(deals_list, user, 'deals')
        
        results['deals'] = [
            {
                'id': str(d.id),
                'name': d.name,
                'amount': str(d.amount) if d.amount else None,
                'stage': d.stage,
                'status': d.status,
                'owner': str(d.owner.id) if d.owner else None,
            }
            for d in deals_ranked[:20]
        ]
        all_results.extend([(d, 'deals') for d in deals_ranked[:20]])
    
    # Get facets for each entity type
    facets_data = {}
    for entity_type in entity_types:
        if entity_type == 'accounts':
            facets_data['accounts'] = FacetedSearchService.get_facets(
                Account.objects.filter(company=company), 'accounts'
            )
        elif entity_type == 'contacts':
            facets_data['contacts'] = FacetedSearchService.get_facets(
                Contact.objects.filter(company=company), 'contacts'
            )
        elif entity_type == 'leads':
            facets_data['leads'] = FacetedSearchService.get_facets(
                Lead.objects.filter(company=company), 'leads'
            )
        elif entity_type == 'deals':
            facets_data['deals'] = FacetedSearchService.get_facets(
                Deal.objects.filter(company=company), 'deals'
            )
    
    # Add explanations if requested
    explanations = {}
    if explain:
        for obj, entity_type in all_results[:10]:  # Explain top 10
            explanation = ExplainabilityService.explain_result(obj, query, user, entity_type)
            result_key = f"{entity_type}:{obj.id}"
            explanations[result_key] = explanation
    
    execution_time = int((time.time() - start_time) * 1000)
    
    total_results = sum(len(v) for v in results.values() if isinstance(v, list))
    
    response_data = {
        'query': query,
        'expanded_queries': expanded_queries[1:] if len(expanded_queries) > 1 else [],
        'results': results,
        'facets': facets_data,
        'total_results': total_results,
        'cache_hit': False,
        'execution_time_ms': execution_time,
    }
    
    if explain:
        response_data['explanations'] = explanations
    
    # Cache results
    SearchCacheService.cache_results(cache_key, query, entity_types, response_data, execution_time, facets, company)
    
    # Log metric
    SearchMetric.objects.create(
        company=company,
        user=user,
        query=query,
        entity_type=','.join(entity_types),
        result_count=total_results,
        execution_time_ms=execution_time,
        cache_hit=False,
        facets_applied=facets
    )
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def relationship_graph(request):
    """
    Query cross-object relationships
    
    Query Parameters:
    - source_type: Source entity type (required)
    - source_id: Source entity ID (required)
    - target_type: Target entity type (optional, for path queries)
    - depth: Depth for related objects (default: 1)
    """
    source_type = request.GET.get('source_type')
    source_id = request.GET.get('source_id')
    target_type = request.GET.get('target_type')
    depth = int(request.GET.get('depth', 1))
    
    if not source_type or not source_id:
        return Response(
            {'error': 'source_type and source_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if target_type:
        # Find paths
        paths = RelationshipGraphService.find_path(source_type, source_id, target_type)
        return Response({
            'source_type': source_type,
            'source_id': source_id,
            'target_type': target_type,
            'paths': paths,
            'path_count': len(paths)
        })
    else:
        # Get related objects
        related = RelationshipGraphService.get_related_objects(source_type, source_id, depth)
        return Response({
            'source_type': source_type,
            'source_id': source_id,
            'related_objects': related
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rebuild_graph(request):
    """Rebuild relationship graph for the company"""
    company = getattr(request, 'company', None)
    if not company:
        return Response({'error': 'Company required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        RelationshipGraphService.build_graph(company)
        return Response({
            'message': 'Relationship graph rebuilt successfully',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_interaction(request):
    """
    Track user interaction with search results
    
    Body:
    - search_metric_id: ID of the search metric
    - result_id: ID of the clicked result
    - result_rank: Rank of the clicked result
    """
    search_metric_id = request.data.get('search_metric_id')
    result_id = request.data.get('result_id')
    result_rank = request.data.get('result_rank')
    
    if not all([search_metric_id, result_id, result_rank]):
        return Response(
            {'error': 'search_metric_id, result_id, and result_rank are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        metric = SearchMetric.objects.get(id=search_metric_id, user=request.user)
        metric.clicked_result_ids.append(str(result_id))
        metric.clicked_result_rank.append(int(result_rank))
        metric.save()
        
        return Response({
            'message': 'Interaction tracked successfully',
            'metric_id': str(metric.id)
        })
    except SearchMetric.DoesNotExist:
        return Response(
            {'error': 'Search metric not found'},
            status=status.HTTP_404_NOT_FOUND
        )
