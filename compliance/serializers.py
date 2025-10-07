# compliance/serializers.py
# Compliance Serializers

from rest_framework import serializers
from .models import CompliancePolicy, DataRetentionRule, AccessReview, DataSubjectRequest, ComplianceViolation

class CompliancePolicySerializer(serializers.ModelSerializer):
    """Compliance policy serializer"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    target_users_list = serializers.SerializerMethodField()
    
    class Meta:
        model = CompliancePolicy
        fields = [
            'id', 'name', 'description', 'policy_type', 'compliance_standard',
            'is_active', 'priority', 'rules', 'enforcement_level', 'target_models',
            'target_users', 'target_users_list', 'target_roles', 'requires_consent',
            'requires_approval', 'requires_documentation', 'review_frequency',
            'next_review_date', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_target_users_list(self, obj):
        """Get list of target user names"""
        return [user.get_full_name() for user in obj.target_users.all()]

class DataRetentionRuleSerializer(serializers.ModelSerializer):
    """Data retention rule serializer"""
    
    policy_name = serializers.CharField(source='policy.name', read_only=True)
    
    class Meta:
        model = DataRetentionRule
        fields = [
            'id', 'policy', 'policy_name', 'name', 'description', 'retention_period',
            'retention_type', 'target_model', 'conditions', 'action_on_expiry',
            'notify_before_expiry', 'notification_days', 'notification_recipients',
            'is_active', 'last_executed', 'next_execution', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AccessReviewSerializer(serializers.ModelSerializer):
    """Access review serializer"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    reviewers_list = serializers.SerializerMethodField()
    approvers_list = serializers.SerializerMethodField()
    target_users_list = serializers.SerializerMethodField()
    compliance_policy_name = serializers.CharField(source='compliance_policy.name', read_only=True)
    
    class Meta:
        model = AccessReview
        fields = [
            'id', 'name', 'description', 'review_type', 'target_users', 'target_users_list',
            'target_roles', 'target_permissions', 'start_date', 'due_date', 'completion_date',
            'reviewers', 'reviewers_list', 'approvers', 'approvers_list', 'status',
            'progress_percentage', 'total_items', 'reviewed_items', 'approved_items',
            'rejected_items', 'compliance_policy', 'compliance_policy_name', 'compliance_score',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_reviewers_list(self, obj):
        """Get list of reviewer names"""
        return [user.get_full_name() for user in obj.reviewers.all()]
    
    def get_approvers_list(self, obj):
        """Get list of approver names"""
        return [user.get_full_name() for user in obj.approvers.all()]
    
    def get_target_users_list(self, obj):
        """Get list of target user names"""
        return [user.get_full_name() for user in obj.target_users.all()]

class DataSubjectRequestSerializer(serializers.ModelSerializer):
    """Data subject request serializer"""
    
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = DataSubjectRequest
        fields = [
            'id', 'request_type', 'subject_name', 'subject_email', 'subject_phone',
            'description', 'specific_data', 'justification', 'status', 'priority',
            'received_date', 'due_date', 'completed_date', 'assigned_to', 'assigned_to_name',
            'processing_notes', 'legal_basis', 'verification_method', 'verification_completed',
            'response_data', 'response_method', 'response_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'received_date', 'created_at', 'updated_at']

class ComplianceViolationSerializer(serializers.ModelSerializer):
    """Compliance violation serializer"""
    
    policy_name = serializers.CharField(source='policy.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True)
    
    class Meta:
        model = ComplianceViolation
        fields = [
            'id', 'violation_type', 'title', 'description', 'severity', 'policy',
            'policy_name', 'user', 'user_name', 'incident_date', 'discovered_date',
            'reported_by', 'reported_by_name', 'affected_users', 'affected_data',
            'potential_impact', 'response_actions', 'mitigation_measures',
            'prevention_measures', 'is_resolved', 'resolution_date', 'resolution_notes',
            'regulatory_notification', 'notification_date', 'notification_authority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'discovered_date', 'created_at', 'updated_at']
