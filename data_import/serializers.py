# data_import/serializers.py
# Serializers for data import module

from rest_framework import serializers
from .models import ImportTemplate, ImportJob, ImportStagingRecord, DuplicateRule

class ImportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportTemplate
        fields = '__all__'
        read_only_fields = ['usage_count', 'last_used', 'created_at', 'updated_at']

class ImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportJob
        fields = '__all__'
        read_only_fields = ['total_rows', 'valid_rows', 'invalid_rows', 'duplicate_rows', 
                           'imported_rows', 'failed_rows', 'started_at', 'completed_at', 
                           'progress_percentage', 'created_at', 'updated_at']

class ImportStagingRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportStagingRecord
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class DuplicateRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DuplicateRule
        fields = '__all__'
        read_only_fields = ['match_count', 'last_used', 'created_at', 'updated_at']
