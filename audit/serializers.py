# audit/serializers.py
# Serializers for audit module

from rest_framework import serializers
from .models import AuditLog, AuditLogExport, ComplianceReport, AuditPolicy

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['audit_id', 'timestamp']

class AuditLogExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLogExport
        fields = '__all__'
        read_only_fields = ['export_id', 'requested_at', 'started_at', 'completed_at', 
                           'file_size', 'record_count']

class ComplianceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceReport
        fields = '__all__'
        read_only_fields = ['report_id', 'created_at', 'updated_at', 'published_at']

class AuditPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditPolicy
        fields = '__all__'
        read_only_fields = ['violation_count', 'last_violation', 'created_at', 'updated_at']
