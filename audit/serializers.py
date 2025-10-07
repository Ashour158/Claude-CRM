# audit/serializers.py
# Audit Serializers

from rest_framework import serializers
from .models import AuditLog, AuditPolicy, AuditReview, ComplianceReport, AuditExport

class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    impersonated_by_name = serializers.CharField(source='impersonated_by.get_full_name', read_only=True)
    content_object_str = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'content_type', 'object_id', 'content_object', 'content_object_str',
            'action', 'description', 'user', 'user_name', 'session_key', 'ip_address',
            'user_agent', 'request_path', 'request_method', 'old_values', 'new_values',
            'changed_fields', 'is_sensitive', 'requires_review', 'compliance_flags',
            'impersonated_by', 'impersonated_by_name', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_content_object_str(self, obj):
        """Get string representation of content object"""
        if obj.content_object:
            return str(obj.content_object)
        return None

class AuditPolicySerializer(serializers.ModelSerializer):
    """Audit policy serializer"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = AuditPolicy
        fields = [
            'id', 'name', 'description', 'policy_type', 'is_active', 'priority',
            'target_models', 'target_actions', 'conditions', 'retention_period',
            'auto_archive', 'auto_delete', 'alert_enabled', 'alert_recipients',
            'alert_threshold', 'compliance_standard', 'review_required',
            'review_frequency', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AuditReviewSerializer(serializers.ModelSerializer):
    """Audit review serializer"""
    
    audit_log_str = serializers.SerializerMethodField()
    policy_name = serializers.CharField(source='policy.name', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    
    class Meta:
        model = AuditReview
        fields = [
            'id', 'audit_log', 'audit_log_str', 'policy', 'policy_name', 'status',
            'reviewer', 'reviewer_name', 'review_notes', 'compliance_notes',
            'risk_assessment', 'action_taken', 'follow_up_required', 'follow_up_date',
            'assigned_at', 'reviewed_at', 'completed_at'
        ]
        read_only_fields = ['id', 'assigned_at']
    
    def get_audit_log_str(self, obj):
        """Get string representation of audit log"""
        return str(obj.audit_log)

class ComplianceReportSerializer(serializers.ModelSerializer):
    """Compliance report serializer"""
    
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    
    class Meta:
        model = ComplianceReport
        fields = [
            'id', 'name', 'description', 'report_type', 'date_range_start',
            'date_range_end', 'filters', 'summary', 'findings', 'recommendations',
            'compliance_standard', 'compliance_score', 'violations_count',
            'critical_issues', 'status', 'export_format', 'export_path',
            'generated_by_name', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at']

class AuditExportSerializer(serializers.ModelSerializer):
    """Audit export serializer"""
    
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    
    class Meta:
        model = AuditExport
        fields = [
            'id', 'name', 'description', 'date_range_start', 'date_range_end',
            'filters', 'format', 'include_sensitive', 'anonymize_data',
            'compression_enabled', 'status', 'file_path', 'file_size',
            'record_count', 'error_message', 'retry_count', 'requested_by_name',
            'requested_at', 'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'requested_at']
