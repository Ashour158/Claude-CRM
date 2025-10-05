# master_data/serializers.py
# Master data serializers

from rest_framework import serializers
from .models import (
    DataCategory, MasterDataField, DataQualityRule, DataQualityViolation,
    DataImport, DataExport, DataSynchronization
)
from core.serializers import UserSerializer

class DataCategorySerializer(serializers.ModelSerializer):
    """Data category serializer"""
    
    class Meta:
        model = DataCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class MasterDataFieldSerializer(serializers.ModelSerializer):
    """Master data field serializer"""
    
    class Meta:
        model = MasterDataField
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class DataQualityRuleSerializer(serializers.ModelSerializer):
    """Data quality rule serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = DataQualityRule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class DataQualityViolationSerializer(serializers.ModelSerializer):
    """Data quality violation serializer"""
    resolved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = DataQualityViolation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class DataImportSerializer(serializers.ModelSerializer):
    """Data import serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = DataImport
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class DataExportSerializer(serializers.ModelSerializer):
    """Data export serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = DataExport
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class DataSynchronizationSerializer(serializers.ModelSerializer):
    """Data synchronization serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = DataSynchronization
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
