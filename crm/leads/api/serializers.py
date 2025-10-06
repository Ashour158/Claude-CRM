# crm/leads/api/serializers.py
"""DRF serializers for lead-related operations."""

from rest_framework import serializers


class LeadConversionResultSerializer(serializers.Serializer):
    """Serializer for lead conversion response."""
    
    lead_id = serializers.IntegerField()
    contact_id = serializers.IntegerField()
    account_id = serializers.IntegerField(allow_null=True)
    created_account = serializers.BooleanField()
    status = serializers.CharField()
    message = serializers.CharField(required=False)


class SavedViewSerializer(serializers.Serializer):
    """Stub serializer for saved views feature (future implementation)."""
    
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    filters = serializers.JSONField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
