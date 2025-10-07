# compliance/admin.py
# Admin interface for compliance models

from django.contrib import admin
from .models import (
    CompliancePolicy, PolicyAuditLog, DataResidency,
    DataSubjectRequest, SecretVault, SecretAccessLog,
    AccessReview, StaleAccess, RetentionPolicy, RetentionLog
)


@admin.register(CompliancePolicy)
class CompliancePolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'policy_type', 'version', 'status', 'is_enforced', 'company', 'created_at']
    list_filter = ['policy_type', 'status', 'is_enforced', 'enforcement_level']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'name', 'description', 'policy_type')
        }),
        ('Policy Configuration', {
            'fields': ('policy_config', 'version', 'previous_version_id')
        }),
        ('Status', {
            'fields': ('status', 'is_enforced', 'enforcement_level')
        }),
        ('Metadata', {
            'fields': ('applied_at', 'applied_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(PolicyAuditLog)
class PolicyAuditLogAdmin(admin.ModelAdmin):
    list_display = ['policy', 'action', 'performed_by', 'records_affected', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['policy__name']
    readonly_fields = ['created_at']


@admin.register(DataResidency)
class DataResidencyAdmin(admin.ModelAdmin):
    list_display = ['company', 'primary_region', 'enforce_region', 'block_cross_region', 'created_at']
    list_filter = ['primary_region', 'enforce_region', 'block_cross_region']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DataSubjectRequest)
class DataSubjectRequestAdmin(admin.ModelAdmin):
    list_display = ['request_id', 'request_type', 'subject_email', 'status', 'due_date', 'created_at']
    list_filter = ['request_type', 'status', 'created_at']
    search_fields = ['request_id', 'subject_email', 'subject_name']
    readonly_fields = ['request_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('company', 'request_type', 'request_id', 'description')
        }),
        ('Subject Information', {
            'fields': ('subject_email', 'subject_name', 'subject_phone')
        }),
        ('Processing', {
            'fields': ('status', 'entities_affected', 'due_date')
        }),
        ('Execution', {
            'fields': ('processed_at', 'processed_by', 'audit_data')
        }),
        ('Rollback', {
            'fields': ('can_rollback', 'rollback_data')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(SecretVault)
class SecretVaultAdmin(admin.ModelAdmin):
    list_display = ['name', 'secret_type', 'is_active', 'rotation_enabled', 'last_rotated', 'expires_at']
    list_filter = ['secret_type', 'is_active', 'rotation_enabled']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    exclude = ['secret_value']  # Never show secret in admin


@admin.register(SecretAccessLog)
class SecretAccessLogAdmin(admin.ModelAdmin):
    list_display = ['secret', 'accessed_by', 'service_name', 'success', 'created_at']
    list_filter = ['success', 'created_at']
    search_fields = ['secret__name', 'service_name']
    readonly_fields = ['created_at']


@admin.register(AccessReview)
class AccessReviewAdmin(admin.ModelAdmin):
    list_display = ['review_id', 'status', 'review_period_start', 'review_period_end', 
                    'total_users_reviewed', 'stale_access_found', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['review_id']
    readonly_fields = ['review_id', 'created_at', 'updated_at']


@admin.register(StaleAccess)
class StaleAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource_type', 'days_inactive', 'resolution', 'is_resolved', 'created_at']
    list_filter = ['resource_type', 'resolution', 'is_resolved']
    search_fields = ['user__email', 'resource_type']
    readonly_fields = ['created_at']


@admin.register(RetentionPolicy)
class RetentionPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'entity_type', 'retention_days', 'deletion_method', 
                    'is_active', 'last_executed', 'next_execution']
    list_filter = ['entity_type', 'deletion_method', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RetentionLog)
class RetentionLogAdmin(admin.ModelAdmin):
    list_display = ['policy', 'execution_started', 'records_processed', 
                    'records_deleted', 'records_archived', 'errors_encountered']
    list_filter = ['execution_started']
    search_fields = ['policy__name']
    readonly_fields = ['execution_started']
