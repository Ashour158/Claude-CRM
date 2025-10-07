# data_import/admin.py
# Admin configuration for data import module

from django.contrib import admin
from .models import ImportTemplate, ImportJob, ImportStagingRecord, DuplicateRule

@admin.register(ImportTemplate)
class ImportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'entity_type', 'dedupe_enabled', 'is_active', 'usage_count', 'owner']
    list_filter = ['entity_type', 'is_active', 'dedupe_enabled', 'dedupe_strategy']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'last_used', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'entity_type')
        }),
        ('Field Mapping', {
            'fields': ('field_mapping', 'default_values', 'transformation_rules')
        }),
        ('Validation', {
            'fields': ('validation_rules', 'required_fields')
        }),
        ('Deduplication', {
            'fields': ('dedupe_enabled', 'dedupe_fields', 'dedupe_strategy')
        }),
        ('Status & Sharing', {
            'fields': ('is_active', 'is_public', 'owner')
        }),
        ('Statistics', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ['name', 'import_template', 'file_type', 'status', 'total_rows', 'imported_rows', 'created_by', 'created_at']
    list_filter = ['status', 'file_type', 'created_at']
    search_fields = ['name', 'file_name']
    readonly_fields = ['total_rows', 'valid_rows', 'invalid_rows', 'duplicate_rows', 'imported_rows', 'failed_rows', 
                       'started_at', 'completed_at', 'progress_percentage', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'import_template')
        }),
        ('File Information', {
            'fields': ('source_file', 'file_name', 'file_size', 'file_type')
        }),
        ('Status & Progress', {
            'fields': ('status', 'progress_percentage', 'current_row')
        }),
        ('Statistics', {
            'fields': ('total_rows', 'valid_rows', 'invalid_rows', 'duplicate_rows', 'imported_rows', 'failed_rows')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Errors', {
            'fields': ('error_summary', 'error_log'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ImportStagingRecord)
class ImportStagingRecordAdmin(admin.ModelAdmin):
    list_display = ['import_job', 'row_number', 'status', 'is_valid', 'is_duplicate', 'import_action']
    list_filter = ['status', 'is_valid', 'is_duplicate', 'import_action']
    search_fields = ['row_number', 'entity_id']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(DuplicateRule)
class DuplicateRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'entity_type', 'match_type', 'match_threshold', 'is_active', 'priority', 'owner']
    list_filter = ['entity_type', 'match_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['match_count', 'last_used', 'created_at', 'updated_at']
