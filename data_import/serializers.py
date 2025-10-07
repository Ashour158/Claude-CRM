# data_import/serializers.py
# Data Import Serializers

from rest_framework import serializers
from .models import ImportTemplate, ImportJob, StagedRecord, ImportLog, DuplicateMatch

class ImportTemplateSerializer(serializers.ModelSerializer):
    """Import template serializer"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = ImportTemplate
        fields = [
            'id', 'name', 'description', 'template_type', 'target_model',
            'field_mappings', 'transformations', 'validation_rules',
            'duplicate_detection_enabled', 'duplicate_fields', 'duplicate_algorithm',
            'duplicate_threshold', 'batch_size', 'skip_errors', 'create_missing',
            'update_existing', 'is_active', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ImportJobSerializer(serializers.ModelSerializer):
    """Import job serializer"""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ImportJob
        fields = [
            'id', 'template', 'template_name', 'file_name', 'file_path', 'file_size',
            'file_type', 'status', 'progress', 'total_rows', 'processed_rows',
            'valid_rows', 'invalid_rows', 'duplicate_rows', 'imported_rows',
            'skipped_rows', 'error_count', 'error_log', 'started_at', 'completed_at',
            'duration', 'duration_display', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_duration_display(self, obj):
        """Get human-readable duration"""
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return None

class StagedRecordSerializer(serializers.ModelSerializer):
    """Staged record serializer"""
    
    job_name = serializers.CharField(source='job.file_name', read_only=True)
    
    class Meta:
        model = StagedRecord
        fields = [
            'id', 'job', 'job_name', 'row_number', 'raw_data', 'processed_data',
            'is_valid', 'validation_errors', 'is_duplicate', 'duplicate_matches',
            'duplicate_strategy', 'import_status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ImportLogSerializer(serializers.ModelSerializer):
    """Import log serializer"""
    
    job_name = serializers.CharField(source='job.file_name', read_only=True)
    
    class Meta:
        model = ImportLog
        fields = [
            'id', 'job', 'job_name', 'log_type', 'message', 'details',
            'row_number', 'field_name', 'field_value', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class DuplicateMatchSerializer(serializers.ModelSerializer):
    """Duplicate match serializer"""
    
    job_name = serializers.CharField(source='job.file_name', read_only=True)
    matched_object_str = serializers.SerializerMethodField()
    
    class Meta:
        model = DuplicateMatch
        fields = [
            'id', 'job', 'job_name', 'staged_record', 'content_type', 'object_id',
            'matched_object', 'matched_object_str', 'similarity_score', 'match_fields',
            'match_algorithm', 'resolution', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_matched_object_str(self, obj):
        """Get string representation of matched object"""
        if obj.matched_object:
            return str(obj.matched_object)
        return None
