# search/services.py
# Search and Knowledge Layer Services

import hashlib
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.db.models import Q, QuerySet, F, Count, Max
from django.core.cache import cache
from django.utils import timezone
from django.db import connection
from crm.models import Account, Contact, Lead
from deals.models import Deal
from .models import SearchCache, QueryExpansion, SearchMetric, RelationshipGraph


class QueryExpansionService:
    """Service for expanding search queries with synonyms and acronyms"""
    
    @staticmethod
    def expand_query(query: str, company) -> List[str]:
        """Expand query with synonyms and acronyms"""
        expansions = QueryExpansion.objects.filter(
            company=company,
            is_active=True
        ).order_by('-priority')
        
        expanded_terms = [query]
        query_lower = query.lower()
        
        for expansion in expansions:
            term_lower = expansion.term.lower()
            if term_lower in query_lower:
                for exp in expansion.expansions:
                    expanded_query = query_lower.replace(term_lower, exp.lower())
                    if expanded_query not in expanded_terms:
                        expanded_terms.append(expanded_query)
        
        return expanded_terms


class PersonalizedRankingService:
    """Service for personalized search result ranking"""
    
    # Ranking weights
    RECENCY_WEIGHT = 0.3
    OWNERSHIP_WEIGHT = 0.4
    INTERACTION_WEIGHT = 0.3
    
    @staticmethod
    def calculate_score(obj, user, interaction_count: int = 0) -> float:
        """Calculate personalized ranking score"""
        score = 0.0
        
        # Recency score (0-1): More recent = higher score
        days_old = (timezone.now() - obj.created_at).days
        recency_score = max(0, 1 - (days_old / 365))  # Decay over a year
        score += recency_score * PersonalizedRankingService.RECENCY_WEIGHT
        
        # Ownership score (0-1): Owner gets highest score
        if hasattr(obj, 'owner') and obj.owner == user:
            ownership_score = 1.0
        else:
            ownership_score = 0.5  # Non-owners get partial score
        score += ownership_score * PersonalizedRankingService.OWNERSHIP_WEIGHT
        
        # Interaction score (0-1): Based on past interactions
        interaction_score = min(1.0, interaction_count / 10)  # Cap at 10 interactions
        score += interaction_score * PersonalizedRankingService.INTERACTION_WEIGHT
        
        return score
    
    @staticmethod
    def rank_results(results: List[Any], user, entity_type: str) -> List[Any]:
        """Rank search results based on personalization"""
        # Get interaction counts from metrics
        recent_metrics = SearchMetric.objects.filter(
            user=user,
            entity_type=entity_type,
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        interaction_counts = {}
        for metric in recent_metrics:
            for result_id in metric.clicked_result_ids:
                interaction_counts[result_id] = interaction_counts.get(result_id, 0) + 1
        
        # Calculate scores
        scored_results = []
        for result in results:
            result_id = str(result.id)
            interaction_count = interaction_counts.get(result_id, 0)
            score = PersonalizedRankingService.calculate_score(result, user, interaction_count)
            scored_results.append((score, result))
        
        # Sort by score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return [result for score, result in scored_results]


class FacetedSearchService:
    """Service for faceted search with filters"""
    
    FACET_CONFIGS = {
        'accounts': {
            'owner': 'owner__id',
            'type': 'type',
            'industry': 'industry',
            'territory': 'territory__id',
            'is_active': 'is_active',
        },
        'contacts': {
            'owner': 'owner__id',
            'account': 'account__id',
            'is_active': 'is_active',
        },
        'leads': {
            'owner': 'owner__id',
            'status': 'status',
            'rating': 'rating',
            'source': 'source',
            'territory': 'territory__id',
        },
        'deals': {
            'owner': 'owner__id',
            'status': 'status',
            'stage': 'stage',
            'account': 'account__id',
        }
    }
    
    @staticmethod
    def get_facets(queryset: QuerySet, entity_type: str) -> Dict[str, List[Dict]]:
        """Get available facets for an entity type"""
        facets = {}
        
        if entity_type not in FacetedSearchService.FACET_CONFIGS:
            return facets
        
        facet_config = FacetedSearchService.FACET_CONFIGS[entity_type]
        
        for facet_name, facet_field in facet_config.items():
            # Count items for each facet value
            facet_values = queryset.values(facet_field).annotate(
                count=Count('id')
            ).order_by('-count')[:10]  # Top 10 values
            
            facets[facet_name] = [
                {
                    'value': item[facet_field],
                    'count': item['count']
                }
                for item in facet_values if item[facet_field] is not None
            ]
        
        return facets
    
    @staticmethod
    def apply_facets(queryset: QuerySet, facets: Dict[str, Any], entity_type: str) -> QuerySet:
        """Apply facet filters to queryset"""
        if entity_type not in FacetedSearchService.FACET_CONFIGS:
            return queryset
        
        facet_config = FacetedSearchService.FACET_CONFIGS[entity_type]
        
        for facet_name, facet_value in facets.items():
            if facet_name in facet_config and facet_value:
                facet_field = facet_config[facet_name]
                if isinstance(facet_value, list):
                    queryset = queryset.filter(**{f"{facet_field}__in": facet_value})
                else:
                    queryset = queryset.filter(**{facet_field: facet_value})
        
        return queryset


class RelationshipGraphService:
    """Service for cross-object relationship queries"""
    
    @staticmethod
    def build_graph(company):
        """Build/update relationship graph for a company"""
        # Clear existing relationships for company
        # Note: This is a simplified approach; in production, use incremental updates
        
        # Lead → Account/Contact relationships
        from crm.models import Lead
        leads = Lead.objects.filter(company=company, converted_account__isnull=False)
        for lead in leads:
            if lead.converted_account:
                RelationshipGraph.objects.update_or_create(
                    source_type='lead',
                    source_id=str(lead.id),
                    target_type='account',
                    target_id=str(lead.converted_account.id),
                    relationship_type='converted_to',
                    defaults={'weight': 1.0}
                )
            if lead.converted_contact:
                RelationshipGraph.objects.update_or_create(
                    source_type='lead',
                    source_id=str(lead.id),
                    target_type='contact',
                    target_id=str(lead.converted_contact.id),
                    relationship_type='converted_to',
                    defaults={'weight': 1.0}
                )
        
        # Contact → Account relationships
        contacts = Contact.objects.filter(company=company, account__isnull=False)
        for contact in contacts:
            RelationshipGraph.objects.update_or_create(
                source_type='contact',
                source_id=str(contact.id),
                target_type='account',
                target_id=str(contact.account.id),
                relationship_type='belongs_to',
                defaults={'weight': 1.0}
            )
        
        # Deal → Account/Contact relationships
        deals = Deal.objects.filter(company=company)
        for deal in deals:
            RelationshipGraph.objects.update_or_create(
                source_type='deal',
                source_id=str(deal.id),
                target_type='account',
                target_id=str(deal.account.id),
                relationship_type='associated_with',
                defaults={'weight': 1.0}
            )
            if deal.contact:
                RelationshipGraph.objects.update_or_create(
                    source_type='deal',
                    source_id=str(deal.id),
                    target_type='contact',
                    target_id=str(deal.contact.id),
                    relationship_type='associated_with',
                    defaults={'weight': 1.0}
                )
    
    @staticmethod
    def find_path(source_type: str, source_id: str, target_type: str, max_depth: int = 3) -> List[List[Dict]]:
        """Find paths between two objects in the relationship graph"""
        paths = []
        visited = set()
        
        def dfs(current_type, current_id, path, depth):
            if depth > max_depth:
                return
            
            if current_type == target_type and len(path) > 1:
                paths.append(list(path))
                return
            
            node_key = f"{current_type}:{current_id}"
            if node_key in visited:
                return
            
            visited.add(node_key)
            
            # Find outgoing relationships
            relationships = RelationshipGraph.objects.filter(
                source_type=current_type,
                source_id=current_id
            )
            
            for rel in relationships:
                new_path = path + [{
                    'type': rel.target_type,
                    'id': rel.target_id,
                    'relationship': rel.relationship_type,
                    'weight': rel.weight
                }]
                dfs(rel.target_type, rel.target_id, new_path, depth + 1)
            
            visited.remove(node_key)
        
        dfs(source_type, source_id, [{'type': source_type, 'id': source_id}], 0)
        return paths
    
    @staticmethod
    def get_related_objects(entity_type: str, entity_id: str, depth: int = 1) -> Dict[str, List[str]]:
        """Get all related objects up to specified depth"""
        related = {}
        
        # Direct relationships
        relationships = RelationshipGraph.objects.filter(
            Q(source_type=entity_type, source_id=entity_id) |
            Q(target_type=entity_type, target_id=entity_id)
        )
        
        for rel in relationships:
            if rel.source_type == entity_type and rel.source_id == entity_id:
                # Outgoing relationship
                if rel.target_type not in related:
                    related[rel.target_type] = []
                related[rel.target_type].append(rel.target_id)
            else:
                # Incoming relationship
                if rel.source_type not in related:
                    related[rel.source_type] = []
                related[rel.source_type].append(rel.source_id)
        
        return related


class SearchCacheService:
    """Service for semantic caching of search queries"""
    
    CACHE_TTL = 3600  # 1 hour in seconds
    
    @staticmethod
    def generate_cache_key(query: str, entity_types: List[str], facets: Dict, company_id) -> str:
        """Generate cache key from query parameters"""
        # Normalize query
        normalized_query = query.lower().strip()
        
        # Create a stable representation of parameters
        params = {
            'query': normalized_query,
            'entity_types': sorted(entity_types),
            'facets': sorted(facets.items()) if facets else [],
            'company_id': str(company_id)
        }
        
        # Generate hash
        params_str = str(params)
        return hashlib.sha256(params_str.encode()).hexdigest()
    
    @staticmethod
    def get_cached_results(cache_key: str, company) -> Optional[Dict]:
        """Get cached search results"""
        try:
            cached = SearchCache.objects.get(
                query_hash=cache_key,
                company=company,
                expires_at__gt=timezone.now()
            )
            
            # Update hit count
            cached.hit_count = F('hit_count') + 1
            cached.last_hit = timezone.now()
            cached.save(update_fields=['hit_count', 'last_hit'])
            
            return {
                'results': cached.results,
                'cache_hit': True,
                'cached_at': cached.created_at,
                'hit_count': cached.hit_count
            }
        except SearchCache.DoesNotExist:
            return None
    
    @staticmethod
    def cache_results(cache_key: str, query: str, entity_types: List[str], 
                     results: Dict, execution_time: int, facets: Dict, company):
        """Cache search results"""
        expires_at = timezone.now() + timedelta(seconds=SearchCacheService.CACHE_TTL)
        
        SearchCache.objects.update_or_create(
            query_hash=cache_key,
            company=company,
            defaults={
                'query': query,
                'entity_types': entity_types,
                'results': results,
                'result_count': sum(len(v) for v in results.values() if isinstance(v, list)),
                'filters': facets,
                'execution_time_ms': execution_time,
                'expires_at': expires_at,
                'hit_count': 0
            }
        )
    
    @staticmethod
    def cleanup_expired_cache():
        """Remove expired cache entries"""
        SearchCache.objects.filter(expires_at__lte=timezone.now()).delete()


class ExplainabilityService:
    """Service for search result explainability"""
    
    @staticmethod
    def explain_result(result: Any, query: str, user, entity_type: str) -> Dict:
        """Explain why a result was returned and its ranking"""
        explanation = {
            'result_id': str(result.id),
            'entity_type': entity_type,
            'scores': {},
            'total_score': 0.0,
            'matched_fields': [],
            'ranking_factors': []
        }
        
        # Lexical matching
        query_terms = query.lower().split()
        matched_fields = []
        
        # Check which fields matched
        search_fields = {
            'accounts': ['name', 'email', 'phone', 'industry'],
            'contacts': ['first_name', 'last_name', 'email', 'phone'],
            'leads': ['first_name', 'last_name', 'company_name', 'email'],
            'deals': ['name', 'description']
        }
        
        if entity_type in search_fields:
            for field in search_fields[entity_type]:
                if hasattr(result, field):
                    field_value = str(getattr(result, field) or '').lower()
                    for term in query_terms:
                        if term in field_value:
                            matched_fields.append({
                                'field': field,
                                'term': term,
                                'score': 1.0
                            })
        
        explanation['matched_fields'] = matched_fields
        lexical_score = min(1.0, len(matched_fields) * 0.2)
        explanation['scores']['lexical'] = lexical_score
        
        # Personalization score
        interaction_count = SearchMetric.objects.filter(
            user=user,
            entity_type=entity_type,
            clicked_result_ids__contains=[str(result.id)],
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        personalization_score = PersonalizedRankingService.calculate_score(
            result, user, interaction_count
        )
        explanation['scores']['personalization'] = personalization_score
        
        # Boosting factors
        boosting_factors = []
        if hasattr(result, 'owner') and result.owner == user:
            boosting_factors.append({'factor': 'ownership', 'boost': 0.4})
        
        days_old = (timezone.now() - result.created_at).days
        if days_old <= 7:
            boosting_factors.append({'factor': 'recent', 'boost': 0.2})
        
        explanation['ranking_factors'] = boosting_factors
        boost_score = sum(f['boost'] for f in boosting_factors)
        explanation['scores']['boosting'] = boost_score
        
        # Total score
        explanation['total_score'] = lexical_score + personalization_score + boost_score
        
        return explanation
