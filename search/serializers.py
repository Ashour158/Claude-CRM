# search/serializers.py
# Search and Knowledge Layer Serializers

from rest_framework import serializers
from .models import SearchCache, QueryExpansion, SearchMetric, RelationshipGraph


class QueryExpansionSerializer(serializers.ModelSerializer):
    """Serializer for query expansion terms"""
    
    class Meta:
        model = QueryExpansion
        fields = [
            'id', 'term', 'expansions', 'term_type', 'is_active',
            'priority', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SearchCacheSerializer(serializers.ModelSerializer):
    """Serializer for search cache"""
    
    class Meta:
        model = SearchCache
        fields = [
            'id', 'query', 'query_hash', 'entity_types', 'results',
            'result_count', 'filters', 'execution_time_ms', 'hit_count',
            'last_hit', 'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SearchMetricSerializer(serializers.ModelSerializer):
    """Serializer for search metrics"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = SearchMetric
        fields = [
            'id', 'user', 'user_email', 'query', 'entity_type',
            'result_count', 'clicked_result_ids', 'clicked_result_rank',
            'execution_time_ms', 'cache_hit', 'facets_applied', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RelationshipGraphSerializer(serializers.ModelSerializer):
    """Serializer for relationship graph"""
    
    class Meta:
        model = RelationshipGraph
        fields = [
            'id', 'source_type', 'source_id', 'target_type', 'target_id',
            'relationship_type', 'weight', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
