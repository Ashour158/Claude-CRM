# core/search/serializers.py
# Serializers for search API

from rest_framework import serializers


class SearchRequestSerializer(serializers.Serializer):
    """Serializer for search request"""
    query = serializers.CharField(
        required=True,
        max_length=500,
        help_text="Search query string"
    )
    models = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of models to search (Account, Contact, Lead, Deal)"
    )
    filters = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Additional filters to apply"
    )
    fuzzy = serializers.BooleanField(
        default=True,
        help_text="Enable fuzzy matching for typo tolerance"
    )
    max_results = serializers.IntegerField(
        default=50,
        min_value=1,
        max_value=100,
        help_text="Maximum number of results to return"
    )
    offset = serializers.IntegerField(
        default=0,
        min_value=0,
        help_text="Pagination offset"
    )
    sort_by = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Field to sort by"
    )
    sort_order = serializers.ChoiceField(
        choices=['asc', 'desc'],
        default='desc',
        help_text="Sort order"
    )
    apply_gdpr = serializers.BooleanField(
        default=True,
        help_text="Apply GDPR filtering to results"
    )


class SearchResultSerializer(serializers.Serializer):
    """Serializer for search result"""
    model = serializers.CharField()
    record_id = serializers.CharField()
    score = serializers.FloatField()
    data = serializers.JSONField()
    highlights = serializers.JSONField(required=False)
    matched_fields = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    pii_filtered = serializers.BooleanField(default=False)


class SearchResponseSerializer(serializers.Serializer):
    """Serializer for search response"""
    query = serializers.JSONField()
    results = SearchResultSerializer(many=True)
    total_count = serializers.IntegerField()
    execution_time_ms = serializers.FloatField()
    backend = serializers.CharField()
    filters_applied = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    api_version = serializers.CharField(default='v1')
    timestamp = serializers.DateTimeField()
    pagination = serializers.JSONField()


class AutocompleteRequestSerializer(serializers.Serializer):
    """Serializer for autocomplete request"""
    query = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Partial query string"
    )
    field = serializers.CharField(
        required=True,
        help_text="Field to get suggestions from (name, email, etc.)"
    )
    limit = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=50,
        help_text="Maximum number of suggestions"
    )


class AutocompleteResponseSerializer(serializers.Serializer):
    """Serializer for autocomplete response"""
    suggestions = serializers.ListField(
        child=serializers.CharField()
    )
