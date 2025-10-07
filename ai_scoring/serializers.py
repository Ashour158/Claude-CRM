# ai_scoring/serializers.py
# AI Lead Scoring and Model Training Serializers

from rest_framework import serializers
from .models import (
    ScoringModel, ModelTraining, ModelPrediction, ModelDrift,
    ModelValidation, ModelFeature, ModelInsight
)

class ScoringModelSerializer(serializers.ModelSerializer):
    """Scoring model serializer"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = ScoringModel
        fields = [
            'id', 'name', 'description', 'model_type', 'algorithm',
            'configuration', 'features', 'target_variable', 'accuracy',
            'precision', 'recall', 'f1_score', 'auc_score', 'status',
            'is_active', 'is_trained', 'training_data_size', 'validation_data_size',
            'last_trained', 'training_duration', 'version', 'is_latest',
            'parent_model', 'owner', 'owner_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ModelTrainingSerializer(serializers.ModelSerializer):
    """Model training serializer"""
    
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = ModelTraining
        fields = [
            'id', 'model', 'model_name', 'training_name', 'description',
            'training_config', 'hyperparameters', 'status', 'training_data_size',
            'validation_data_size', 'test_data_size', 'started_at', 'completed_at',
            'duration_seconds', 'training_accuracy', 'validation_accuracy',
            'test_accuracy', 'precision', 'recall', 'f1_score', 'auc_score',
            'error_message', 'error_traceback', 'memory_usage_mb', 'cpu_usage_percent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ModelPredictionSerializer(serializers.ModelSerializer):
    """Model prediction serializer"""
    
    model_name = serializers.CharField(source='model.name', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = ModelPrediction
        fields = [
            'id', 'model', 'model_name', 'prediction_type', 'content_type',
            'content_type_name', 'object_id', 'score', 'confidence', 'probability',
            'input_features', 'feature_importance', 'explanation', 'reasoning',
            'actual_value', 'prediction_accuracy', 'model_version', 'prediction_metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ModelDriftSerializer(serializers.ModelSerializer):
    """Model drift serializer"""
    
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = ModelDrift
        fields = [
            'id', 'model', 'model_name', 'drift_type', 'severity', 'drift_score',
            'threshold', 'is_drift_detected', 'baseline_data', 'current_data',
            'comparison_metrics', 'detection_method', 'detection_parameters',
            'detected_at', 'baseline_period_start', 'baseline_period_end',
            'current_period_start', 'current_period_end', 'is_resolved',
            'resolved_at', 'resolution_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ModelValidationSerializer(serializers.ModelSerializer):
    """Model validation serializer"""
    
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = ModelValidation
        fields = [
            'id', 'model', 'model_name', 'validation_name', 'validation_type',
            'description', 'validation_config', 'test_data_size', 'status',
            'started_at', 'completed_at', 'duration_seconds', 'accuracy',
            'precision', 'recall', 'f1_score', 'auc_score', 'validation_metrics',
            'confusion_matrix', 'roc_curve', 'error_message', 'error_traceback',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ModelFeatureSerializer(serializers.ModelSerializer):
    """Model feature serializer"""
    
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = ModelFeature
        fields = [
            'id', 'model', 'model_name', 'feature_name', 'feature_type',
            'description', 'feature_config', 'preprocessing_steps',
            'importance_score', 'correlation_score', 'missing_value_percentage',
            'outlier_percentage', 'is_active', 'is_required', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ModelInsightSerializer(serializers.ModelSerializer):
    """Model insight serializer"""
    
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = ModelInsight
        fields = [
            'id', 'model', 'model_name', 'insight_type', 'title', 'description',
            'insight_data', 'visualizations', 'recommendations', 'action_items',
            'is_active', 'priority', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
