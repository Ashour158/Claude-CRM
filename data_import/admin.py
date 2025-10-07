# data_import/admin.py
# Data Import Admin Interface

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import ImportTemplate, ImportJob, StagedRecord, ImportLog, DuplicateMatch

@admin.register(ImportTemplate)
class ImportTemplateAdmin(admin.ModelAdmin):
    """Import template admin interface"""
    
    list_display = [
        'name', 'template_type', 'target_model', 'is_active', 
        'created_by', 'created_at'
    ]
    list_filter = [
        'template_type', 'is_active', 'duplicate_detection_enabled',
        'created_at', 'updated_at'
    ]
    search_fields = ['name', 'description', 'target_model']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'template_type', 'target_model')
        }),
        ('Field Mapping', {
            'fields': ('field_mappings', 'transformations', 'validation_rules')
        }),
        ('Duplicate Detection', {
            'fields': (
                'duplicate_detection_enabled', 'duplicate_fields', 
                'duplicate_algorithm', 'duplicate_threshold'
            )
        }),
        ('Import Settings', {
            'fields': (
                'batch_size', 'skip_errors', 'create_missing', 'update_existing'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    """Import job admin interface"""
    
    list_display = [
        'file_name', 'template', 'status', 'progress_display', 
        'total_rows', 'imported_rows', 'error_count', 'created_by', 'created_at'
    ]
    list_filter = [
        'status', 'template', 'file_type', 'created_at'
    ]
    search_fields = ['file_name', 'template__name']
    readonly_fields = [
        'file_size', 'total_rows', 'processed_rows', 'valid_rows', 
        'invalid_rows', 'duplicate_rows', 'imported_rows', 'skipped_rows',
        'error_count', 'started_at', 'completed_at', 'duration', 'created_at'
    ]
    
    fieldsets = (
        ('Job Information', {
            'fields': ('template', 'file_name', 'file_path', 'file_size', 'file_type')
        }),
        ('Status', {
            'fields': ('status', 'progress')
        }),
        ('Statistics', {
            'fields': (
                'total_rows', 'processed_rows', 'valid_rows', 'invalid_rows',
                'duplicate_rows', 'imported_rows', 'skipped_rows', 'error_count'
            )
        }),
        ('Execution', {
            'fields': ('started_at', 'completed_at', 'duration')
        }),
        ('Error Details', {
            'fields': ('error_log',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def progress_display(self, obj):
        """Display progress as progress bar"""
        if obj.status == 'running':
            color = 'orange'
        elif obj.status == 'completed':
            color = 'green'
        elif obj.status == 'failed':
            color = 'red'
        else:
            color = 'gray'
        
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; '
            'display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">'
            '{}%</div></div>',
            obj.progress, color, obj.progress
        )
    progress_display.short_description = 'Progress'

@admin.register(StagedRecord)
class StagedRecordAdmin(admin.ModelAdmin):
    """Staged record admin interface"""
    
    list_display = [
        'row_number', 'job', 'is_valid', 'is_duplicate', 
        'import_status', 'created_at'
    ]
    list_filter = [
        'is_valid', 'is_duplicate', 'import_status', 'duplicate_strategy'
    ]
    search_fields = ['job__file_name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Record Information', {
            'fields': ('job', 'row_number', 'raw_data', 'processed_data')
        }),
        ('Validation', {
            'fields': ('is_valid', 'validation_errors')
        }),
        ('Duplicate Detection', {
            'fields': ('is_duplicate', 'duplicate_matches', 'duplicate_strategy')
        }),
        ('Import Status', {
            'fields': ('import_status',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    """Import log admin interface"""
    
    list_display = [
        'job', 'log_type', 'message_short', 'row_number', 'created_at'
    ]
    list_filter = [
        'log_type', 'job', 'created_at'
    ]
    search_fields = ['message', 'job__file_name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Log Information', {
            'fields': ('job', 'log_type', 'message', 'details')
        }),
        ('Context', {
            'fields': ('row_number', 'field_name', 'field_value')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def message_short(self, obj):
        """Short message display"""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Message'

@admin.register(DuplicateMatch)
class DuplicateMatchAdmin(admin.ModelAdmin):
    """Duplicate match admin interface"""
    
    list_display = [
        'job', 'staged_record', 'matched_object_str', 'similarity_score',
        'match_algorithm', 'resolution', 'created_at'
    ]
    list_filter = [
        'match_algorithm', 'resolution', 'job', 'created_at'
    ]
    search_fields = ['job__file_name', 'match_fields']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Match Information', {
            'fields': ('job', 'staged_record', 'content_type', 'object_id', 'matched_object')
        }),
        ('Match Details', {
            'fields': ('similarity_score', 'match_fields', 'match_algorithm')
        }),
        ('Resolution', {
            'fields': ('resolution',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def matched_object_str(self, obj):
        """String representation of matched object"""
        if obj.matched_object:
            return str(obj.matched_object)
        return 'N/A'
    matched_object_str.short_description = 'Matched Object'
