# compliance/admin.py
# Compliance Admin Interface

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import CompliancePolicy, DataRetentionRule, AccessReview, DataSubjectRequest, ComplianceViolation

@admin.register(CompliancePolicy)
class CompliancePolicyAdmin(admin.ModelAdmin):
    """Compliance policy admin interface"""
    
    list_display = [
        'name', 'policy_type', 'compliance_standard', 'is_active', 
        'priority', 'enforcement_level', 'created_by', 'created_at'
    ]
    list_filter = [
        'policy_type', 'compliance_standard', 'is_active', 'enforcement_level',
        'requires_consent', 'requires_approval', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('name', 'description', 'policy_type', 'compliance_standard')
        }),
        ('Configuration', {
            'fields': ('is_active', 'priority', 'rules', 'enforcement_level')
        }),
        ('Scope', {
            'fields': ('target_models', 'target_users', 'target_roles')
        }),
        ('Requirements', {
            'fields': ('requires_consent', 'requires_approval', 'requires_documentation')
        }),
        ('Review', {
            'fields': ('review_frequency', 'next_review_date')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(DataRetentionRule)
class DataRetentionRuleAdmin(admin.ModelAdmin):
    """Data retention rule admin interface"""
    
    list_display = [
        'name', 'policy', 'target_model', 'retention_period', 
        'retention_type', 'action_on_expiry', 'is_active', 'last_executed'
    ]
    list_filter = [
        'policy', 'retention_type', 'action_on_expiry', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description', 'target_model']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Rule Information', {
            'fields': ('policy', 'name', 'description', 'retention_period', 'retention_type')
        }),
        ('Scope', {
            'fields': ('target_model', 'conditions')
        }),
        ('Actions', {
            'fields': ('action_on_expiry',)
        }),
        ('Notifications', {
            'fields': ('notify_before_expiry', 'notification_days', 'notification_recipients')
        }),
        ('Status', {
            'fields': ('is_active', 'last_executed', 'next_execution')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(AccessReview)
class AccessReviewAdmin(admin.ModelAdmin):
    """Access review admin interface"""
    
    list_display = [
        'name', 'review_type', 'status', 'progress_display', 
        'due_date', 'compliance_policy', 'created_by', 'created_at'
    ]
    list_filter = [
        'review_type', 'status', 'compliance_policy', 'start_date', 'due_date'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('name', 'description', 'review_type', 'status')
        }),
        ('Scope', {
            'fields': ('target_users', 'target_roles', 'target_permissions')
        }),
        ('Timeline', {
            'fields': ('start_date', 'due_date', 'completion_date')
        }),
        ('Reviewers', {
            'fields': ('reviewers', 'approvers')
        }),
        ('Progress', {
            'fields': ('progress_percentage', 'total_items', 'reviewed_items', 'approved_items', 'rejected_items')
        }),
        ('Compliance', {
            'fields': ('compliance_policy', 'compliance_score')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def progress_display(self, obj):
        """Display progress as progress bar"""
        color = 'green' if obj.progress_percentage >= 80 else 'orange' if obj.progress_percentage >= 50 else 'red'
        
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; '
            'display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">'
            '{}%</div></div>',
            obj.progress_percentage, color, obj.progress_percentage
        )
    progress_display.short_description = 'Progress'

@admin.register(DataSubjectRequest)
class DataSubjectRequestAdmin(admin.ModelAdmin):
    """Data subject request admin interface"""
    
    list_display = [
        'request_type', 'subject_name', 'subject_email', 'status', 
        'priority', 'assigned_to', 'received_date', 'due_date'
    ]
    list_filter = [
        'request_type', 'status', 'priority', 'assigned_to', 'received_date'
    ]
    search_fields = ['subject_name', 'subject_email', 'description']
    readonly_fields = ['received_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('request_type', 'subject_name', 'subject_email', 'subject_phone')
        }),
        ('Request Details', {
            'fields': ('description', 'specific_data', 'justification')
        }),
        ('Status and Priority', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Timeline', {
            'fields': ('received_date', 'due_date', 'completed_date')
        }),
        ('Processing', {
            'fields': ('processing_notes', 'legal_basis', 'verification_method', 'verification_completed')
        }),
        ('Response', {
            'fields': ('response_data', 'response_method', 'response_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ComplianceViolation)
class ComplianceViolationAdmin(admin.ModelAdmin):
    """Compliance violation admin interface"""
    
    list_display = [
        'title', 'violation_type', 'severity', 'is_resolved', 
        'incident_date', 'discovered_date', 'reported_by'
    ]
    list_filter = [
        'violation_type', 'severity', 'is_resolved', 'regulatory_notification',
        'incident_date', 'discovered_date'
    ]
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['discovered_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Violation Information', {
            'fields': ('violation_type', 'title', 'description', 'severity')
        }),
        ('Related Entities', {
            'fields': ('policy', 'user', 'reported_by')
        }),
        ('Incident Details', {
            'fields': ('incident_date', 'discovered_date', 'affected_users', 'affected_data', 'potential_impact')
        }),
        ('Response', {
            'fields': ('response_actions', 'mitigation_measures', 'prevention_measures')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolution_date', 'resolution_notes')
        }),
        ('Regulatory Notification', {
            'fields': ('regulatory_notification', 'notification_date', 'notification_authority'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
