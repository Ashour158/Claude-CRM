# search/models.py
# Search and Knowledge Layer Models

from django.db import models
from django.contrib.postgres.fields import ArrayField
from core.models import CompanyIsolatedModel, User


class SearchCache(CompanyIsolatedModel):
    """Cache for search queries with semantic fingerprints"""
    
    query = models.TextField(db_index=True)
    query_hash = models.CharField(max_length=64, db_index=True, help_text="Hash of normalized query")
    entity_types = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    results = models.JSONField(help_text="Cached search results")
    result_count = models.IntegerField(default=0)
    filters = models.JSONField(null=True, blank=True, help_text="Applied filters")
    
    # Performance metrics
    execution_time_ms = models.IntegerField(help_text="Query execution time in milliseconds")
    hit_count = models.IntegerField(default=0, help_text="Number of times this cache was hit")
    last_hit = models.DateTimeField(null=True, blank=True)
    
    # Expiry
    expires_at = models.DateTimeField(db_index=True)
    
    class Meta:
        db_table = 'search_cache'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'query_hash']),
            models.Index(fields=['company', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Cache: {self.query[:50]}"


class QueryExpansion(CompanyIsolatedModel):
    """Query expansion dictionary for synonyms and acronyms"""
    
    term = models.CharField(max_length=255, db_index=True, help_text="Original term")
    expansions = ArrayField(
        models.CharField(max_length=255),
        help_text="List of synonyms and expanded forms"
    )
    term_type = models.CharField(
        max_length=20,
        choices=[
            ('synonym', 'Synonym'),
            ('acronym', 'Acronym'),
            ('abbreviation', 'Abbreviation'),
        ],
        default='synonym'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.IntegerField(default=0, help_text="Higher priority terms are applied first")
    
    class Meta:
        db_table = 'search_query_expansion'
        ordering = ['-priority', 'term']
        indexes = [
            models.Index(fields=['company', 'term']),
            models.Index(fields=['company', 'is_active']),
        ]
        unique_together = [['company', 'term', 'term_type']]
    
    def __str__(self):
        return f"{self.term} → {', '.join(self.expansions[:3])}"


class SearchMetric(CompanyIsolatedModel):
    """Track search metrics and analytics"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_metrics')
    query = models.TextField()
    entity_type = models.CharField(max_length=50, blank=True)
    result_count = models.IntegerField(default=0)
    
    # Interaction tracking
    clicked_result_ids = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="IDs of results user clicked on"
    )
    clicked_result_rank = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True,
        help_text="Ranks of clicked results"
    )
    
    # Performance
    execution_time_ms = models.IntegerField()
    cache_hit = models.BooleanField(default=False)
    
    # Facets applied
    facets_applied = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'search_metrics'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'user', '-created_at']),
            models.Index(fields=['company', 'entity_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"Search: {self.query[:50]} by {self.user}"


class RelationshipGraph(models.Model):
    """Cross-object relationships for knowledge graph queries"""
    
    source_type = models.CharField(max_length=50, db_index=True)
    source_id = models.CharField(max_length=50, db_index=True)
    target_type = models.CharField(max_length=50, db_index=True)
    target_id = models.CharField(max_length=50, db_index=True)
    relationship_type = models.CharField(
        max_length=50,
        choices=[
            ('converted_to', 'Converted To'),
            ('associated_with', 'Associated With'),
            ('owned_by', 'Owned By'),
            ('belongs_to', 'Belongs To'),
            ('related_to', 'Related To'),
        ]
    )
    weight = models.FloatField(default=1.0, help_text="Relationship strength")
    metadata = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'search_relationship_graph'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source_type', 'source_id']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['relationship_type']),
        ]
        unique_together = [['source_type', 'source_id', 'target_type', 'target_id', 'relationship_type']]
    
    def __str__(self):
        return f"{self.source_type}:{self.source_id} --{self.relationship_type}--> {self.target_type}:{self.target_id}"
