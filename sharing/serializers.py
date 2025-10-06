# sharing/serializers.py
# Serializers for sharing models

from rest_framework import serializers
from .models import SharingRule, RecordShare


class SharingRuleSerializer(serializers.ModelSerializer):
    """Serializer for SharingRule model"""
    
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = SharingRule
        fields = [
            'id',
            'company',
            'name',
            'description',
            'object_type',
            'predicate',
            'access_level',
            'is_active',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_email',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def validate_predicate(self, value):
        """Validate predicate structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Predicate must be a dictionary")
        
        required_keys = ['field', 'operator', 'value']
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(f"Predicate must have '{key}' key")
        
        supported_operators = ['eq', 'ne', 'in', 'nin', 'contains', 'icontains', 'gt', 'gte', 'lt', 'lte']
        if value['operator'] not in supported_operators:
            raise serializers.ValidationError(
                f"Operator must be one of: {', '.join(supported_operators)}"
            )
        
        return value


class RecordShareSerializer(serializers.ModelSerializer):
    """Serializer for RecordShare model"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = RecordShare
        fields = [
            'id',
            'company',
            'object_type',
            'object_id',
            'user',
            'user_email',
            'access_level',
            'reason',
            'created_at',
            'created_by',
            'created_by_email',
        ]
        read_only_fields = ['id', 'created_at', 'created_by']
