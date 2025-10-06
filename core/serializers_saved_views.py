# core/serializers_saved_views.py
# Serializers for Saved Views

from rest_framework import serializers
from core.models_saved_views import SavedListView


class SavedListViewSerializer(serializers.ModelSerializer):
    """Serializer for SavedListView model."""
    
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    
    class Meta:
        model = SavedListView
        fields = [
            'id', 'name', 'description', 'entity_type', 'definition',
            'owner', 'owner_email', 'is_private', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner_email']
    
    def validate_definition(self, value):
        """
        Validate definition structure.
        """
        # Ensure definition has required keys
        if not isinstance(value, dict):
            raise serializers.ValidationError("Definition must be a dictionary")
        
        # Validate filters
        filters = value.get('filters', [])
        if not isinstance(filters, list):
            raise serializers.ValidationError("Filters must be a list")
        
        for filter_def in filters:
            if not isinstance(filter_def, dict):
                raise serializers.ValidationError("Each filter must be a dictionary")
            if 'field' not in filter_def or 'operator' not in filter_def:
                raise serializers.ValidationError("Each filter must have 'field' and 'operator'")
        
        # Validate columns
        columns = value.get('columns', [])
        if not isinstance(columns, list):
            raise serializers.ValidationError("Columns must be a list")
        
        # Validate sort
        sort = value.get('sort', [])
        if not isinstance(sort, list):
            raise serializers.ValidationError("Sort must be a list")
        
        for sort_def in sort:
            if not isinstance(sort_def, dict):
                raise serializers.ValidationError("Each sort must be a dictionary")
            if 'field' not in sort_def or 'direction' not in sort_def:
                raise serializers.ValidationError("Each sort must have 'field' and 'direction'")
            if sort_def['direction'] not in ['asc', 'desc']:
                raise serializers.ValidationError("Sort direction must be 'asc' or 'desc'")
        
        return value
    
    def create(self, validated_data):
        """
        Create a saved view.
        Set owner to current user if is_private is True.
        """
        request = self.context.get('request')
        if validated_data.get('is_private', True) and request:
            validated_data['owner'] = request.user
        else:
            validated_data['owner'] = None
        
        # Set company from request
        if request and hasattr(request, 'company'):
            validated_data['company'] = request.company
        
        return super().create(validated_data)


class SavedListViewCreateSerializer(SavedListViewSerializer):
    """Serializer for creating saved views."""
    
    class Meta(SavedListViewSerializer.Meta):
        fields = [
            'name', 'description', 'entity_type', 'definition',
            'is_private', 'is_default'
        ]


class SavedListViewUpdateSerializer(SavedListViewSerializer):
    """Serializer for updating saved views."""
    
    class Meta(SavedListViewSerializer.Meta):
        fields = [
            'name', 'description', 'definition', 'is_private', 'is_default'
        ]
        read_only_fields = ['entity_type']  # Can't change entity type after creation
