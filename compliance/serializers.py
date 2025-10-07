# compliance/serializers.py
# Serializers for compliance models

from rest_framework import serializers
from .models import (
    CompliancePolicy, PolicyAuditLog, DataResidency,
    DataSubjectRequest, SecretVault, SecretAccessLog,
    AccessReview, StaleAccess, RetentionPolicy, RetentionLog
)


class CompliancePolicySerializer(serializers.ModelSerializer):
    """Serializer for compliance policies"""
    
    applied_by_email = serializers.EmailField(source='applied_by.email', read_only=True)
    
    class Meta:
        model = CompliancePolicy
        fields = [
            'id', 'name', 'description', 'policy_type', 'policy_config',
            'version', 'previous_version_id', 'status', 'is_enforced',
            'enforcement_level', 'applied_at', 'applied_by', 'applied_by_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PolicyAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for policy audit logs"""
    
    policy_name = serializers.CharField(source='policy.name', read_only=True)
    performed_by_email = serializers.EmailField(source='performed_by.email', read_only=True)
    
    class Meta:
        model = PolicyAuditLog
        fields = [
            'id', 'policy', 'policy_name', 'action', 'action_details',
            'entities_affected', 'records_affected', 'performed_by',
            'performed_by_email', 'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DataResidencySerializer(serializers.ModelSerializer):
    """Serializer for data residency configuration"""
    
    class Meta:
        model = DataResidency
        fields = [
            'id', 'primary_region', 'allowed_regions', 'storage_prefix',
            'bucket_name', 'enforce_region', 'block_cross_region',
            'compliance_frameworks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DataSubjectRequestSerializer(serializers.ModelSerializer):
    """Serializer for data subject requests"""
    
    processed_by_email = serializers.EmailField(source='processed_by.email', read_only=True)
    
    class Meta:
        model = DataSubjectRequest
        fields = [
            'id', 'request_type', 'request_id', 'subject_email', 'subject_name',
            'subject_phone', 'description', 'entities_affected', 'status',
            'processed_at', 'processed_by', 'processed_by_email', 'audit_data',
            'can_rollback', 'rollback_data', 'due_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'request_id', 'created_at', 'updated_at']


class SecretVaultSerializer(serializers.ModelSerializer):
    """Serializer for secret vault (redacted)"""
    
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    
    class Meta:
        model = SecretVault
        fields = [
            'id', 'name', 'description', 'secret_type', 'kms_key_id',
            'encryption_algorithm', 'rotation_enabled', 'rotation_days',
            'last_rotated', 'next_rotation', 'allowed_services',
            'is_active', 'expires_at', 'owner', 'owner_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Redact secret value from output"""
        data = super().to_representation(instance)
        # Never expose secret_value in API responses
        return data


class SecretVaultDetailSerializer(SecretVaultSerializer):
    """Serializer with decrypted secret (restricted access)"""
    
    secret_value = serializers.CharField(write_only=True, required=False)
    
    class Meta(SecretVaultSerializer.Meta):
        fields = SecretVaultSerializer.Meta.fields + ['secret_value']


class SecretAccessLogSerializer(serializers.ModelSerializer):
    """Serializer for secret access logs"""
    
    secret_name = serializers.CharField(source='secret.name', read_only=True)
    accessed_by_email = serializers.EmailField(source='accessed_by.email', read_only=True)
    
    class Meta:
        model = SecretAccessLog
        fields = [
            'id', 'secret', 'secret_name', 'accessed_by', 'accessed_by_email',
            'service_name', 'ip_address', 'user_agent', 'success',
            'failure_reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AccessReviewSerializer(serializers.ModelSerializer):
    """Serializer for access reviews"""
    
    reviewed_by_email = serializers.EmailField(source='reviewed_by.email', read_only=True)
    
    class Meta:
        model = AccessReview
        fields = [
            'id', 'review_id', 'review_period_start', 'review_period_end',
            'status', 'total_users_reviewed', 'stale_access_found',
            'access_revoked', 'review_data', 'completed_at', 'reviewed_by',
            'reviewed_by_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'review_id', 'created_at', 'updated_at']


class StaleAccessSerializer(serializers.ModelSerializer):
    """Serializer for stale access records"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    resolved_by_email = serializers.EmailField(source='resolved_by.email', read_only=True)
    
    class Meta:
        model = StaleAccess
        fields = [
            'id', 'access_review', 'user', 'user_email', 'resource_type',
            'resource_id', 'last_accessed', 'days_inactive', 'is_resolved',
            'resolution', 'resolved_at', 'resolved_by', 'resolved_by_email',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RetentionPolicySerializer(serializers.ModelSerializer):
    """Serializer for retention policies"""
    
    class Meta:
        model = RetentionPolicy
        fields = [
            'id', 'name', 'description', 'entity_type', 'retention_days',
            'deletion_method', 'filter_conditions', 'is_active',
            'last_executed', 'next_execution', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RetentionLogSerializer(serializers.ModelSerializer):
    """Serializer for retention logs"""
    
    policy_name = serializers.CharField(source='policy.name', read_only=True)
    
    class Meta:
        model = RetentionLog
        fields = [
            'id', 'policy', 'policy_name', 'execution_started',
            'execution_completed', 'records_processed', 'records_deleted',
            'records_archived', 'errors_encountered', 'execution_details',
            'compliance_log'
        ]
        read_only_fields = ['id', 'execution_started']
