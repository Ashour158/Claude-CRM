# ai_assistant/serializers.py
# AI Assistant and Predictive Analytics Serializers

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import AIAssistant, AIInteraction, PredictiveModel, Prediction, AnomalyDetection

class AIAssistantSerializer(serializers.ModelSerializer):
    """AI Assistant serializer"""
    
    success_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = AIAssistant
        fields = [
            'id', 'name', 'assistant_type', 'description',
            'model_name', 'temperature', 'max_tokens',
            'capabilities', 'context_data', 'is_active',
            'is_public', 'total_interactions', 'successful_interactions',
            'average_rating', 'success_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AIInteractionSerializer(serializers.ModelSerializer):
    """AI Interaction serializer"""
    
    assistant_name = serializers.CharField(source='assistant.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = AIInteraction
        fields = [
            'id', 'assistant', 'assistant_name', 'user', 'user_name',
            'interaction_type', 'user_input', 'ai_response', 'context',
            'content_type', 'object_id', 'user_rating', 'is_helpful',
            'feedback', 'response_time_ms', 'tokens_used', 'session_id',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ChatRequestSerializer(serializers.Serializer):
    """Chat request serializer"""
    
    user_input = serializers.CharField(max_length=5000)
    context = serializers.JSONField(required=False, default=dict)
    related_entity = serializers.JSONField(required=False, default=dict)

class PredictionRequestSerializer(serializers.Serializer):
    """Prediction request serializer"""
    
    entity_type = serializers.CharField(max_length=50)
    entity_id = serializers.UUIDField()
    input_features = serializers.JSONField()

class PredictiveModelSerializer(serializers.ModelSerializer):
    """Predictive Model serializer"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = PredictiveModel
        fields = [
            'id', 'name', 'model_type', 'description', 'algorithm',
            'parameters', 'training_data', 'accuracy', 'precision',
            'recall', 'f1_score', 'status', 'is_active', 'last_trained',
            'training_duration', 'training_samples', 'owner', 'owner_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PredictionSerializer(serializers.ModelSerializer):
    """Prediction serializer"""
    
    model_name = serializers.CharField(source='model.name', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = Prediction
        fields = [
            'id', 'model', 'model_name', 'content_type', 'content_type_name',
            'object_id', 'prediction_value', 'confidence_score',
            'prediction_details', 'actual_value', 'prediction_accuracy',
            'input_features', 'model_version', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AnomalyDetectionSerializer(serializers.ModelSerializer):
    """Anomaly Detection serializer"""
    
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True)
    
    class Meta:
        model = AnomalyDetection
        fields = [
            'id', 'anomaly_type', 'severity', 'title', 'description',
            'detected_at', 'confidence_score', 'anomaly_score',
            'related_data', 'baseline_data', 'is_resolved',
            'resolved_at', 'resolved_by', 'resolved_by_name',
            'resolution_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
