# search/admin.py
# Admin configuration for search models

from django.contrib import admin
from .models import SearchCache, QueryExpansion, SearchMetric, RelationshipGraph


@admin.register(SearchCache)
class SearchCacheAdmin(admin.ModelAdmin):
    list_display = ['query', 'query_hash', 'result_count', 'hit_count', 'execution_time_ms', 'expires_at', 'created_at']
    list_filter = ['entity_types', 'created_at', 'expires_at']
    search_fields = ['query', 'query_hash']
    readonly_fields = ['query_hash', 'hit_count', 'last_hit', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(QueryExpansion)
class QueryExpansionAdmin(admin.ModelAdmin):
    list_display = ['term', 'term_type', 'priority', 'is_active', 'created_at']
    list_filter = ['term_type', 'is_active', 'created_at']
    search_fields = ['term', 'expansions']
    ordering = ['-priority', 'term']


@admin.register(SearchMetric)
class SearchMetricAdmin(admin.ModelAdmin):
    list_display = ['query', 'user', 'entity_type', 'result_count', 'execution_time_ms', 'cache_hit', 'created_at']
    list_filter = ['entity_type', 'cache_hit', 'created_at']
    search_fields = ['query', 'user__email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(RelationshipGraph)
class RelationshipGraphAdmin(admin.ModelAdmin):
    list_display = ['source_type', 'source_id', 'relationship_type', 'target_type', 'target_id', 'weight', 'created_at']
    list_filter = ['source_type', 'target_type', 'relationship_type', 'created_at']
    search_fields = ['source_id', 'target_id']
    ordering = ['-created_at']
