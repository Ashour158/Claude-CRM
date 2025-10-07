# ai_assistant/models.py
# AI Assistant and Predictive Analytics Models

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import CompanyIsolatedModel, User
import uuid
import json

class AIAssistant(CompanyIsolatedModel):
    """AI Assistant configuration and capabilities"""
    
    ASSISTANT_TYPES = [
        ('sales', 'Sales Assistant'),
        ('marketing', 'Marketing Assistant'),
        ('support', 'Support Assistant'),
        ('analytics', 'Analytics Assistant'),
        ('general', 'General Assistant'),
    ]
    
    name = models.CharField(max_length=255)
    assistant_type = models.CharField(
        max_length=20,
        choices=ASSISTANT_TYPES,
        default='general'
    )
    description = models.TextField(blank=True)
    
    # AI Configuration
    model_name = models.CharField(
        max_length=100,
        default='gpt-3.5-turbo',
        help_text="AI model to use"
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="AI response creativity (0.0-1.0)"
    )
    max_tokens = models.IntegerField(
        default=1000,
        help_text="Maximum response length"
    )
    
    # Capabilities
    capabilities = models.JSONField(
        default=list,
        help_text="List of AI capabilities"
    )
    context_data = models.JSONField(
        default=dict,
        help_text="Context data for AI responses"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(
        default=False,
        help_text="Available to all users"
    )
    
    # Statistics
    total_interactions = models.IntegerField(default=0)
    successful_interactions = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    
    class Meta:
        db_table = 'ai_assistant'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def success_rate(self):
        """Calculate success rate of AI interactions"""
        if self.total_interactions == 0:
            return 0.0
        return (self.successful_interactions / self.total_interactions) * 100

class AIInteraction(CompanyIsolatedModel):
    """AI Assistant interactions and conversations"""
    
    INTERACTION_TYPES = [
        ('chat', 'Chat'),
        ('query', 'Query'),
        ('analysis', 'Analysis'),
        ('prediction', 'Prediction'),
        ('recommendation', 'Recommendation'),
    ]
    
    # Basic Information
    assistant = models.ForeignKey(
        AIAssistant,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_interactions'
    )
    interaction_type = models.CharField(
        max_length=20,
        choices=INTERACTION_TYPES,
        default='chat'
    )
    
    # Conversation
    user_input = models.TextField(help_text="User's input/question")
    ai_response = models.TextField(help_text="AI's response")
    context = models.JSONField(
        default=dict,
        help_text="Context data used for response"
    )
    
    # Related Entity (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Type of related entity"
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of the related entity"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Quality Metrics
    user_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text="User rating (1-5)"
    )
    is_helpful = models.BooleanField(
        null=True,
        blank=True,
        help_text="Was the response helpful?"
    )
    feedback = models.TextField(blank=True, help_text="User feedback")
    
    # Performance Metrics
    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Response time in milliseconds"
    )
    tokens_used = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of tokens used"
    )
    
    # Metadata
    session_id = models.UUIDField(
        default=uuid.uuid4,
        help_text="Session identifier"
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'ai_interaction'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'assistant']),
            models.Index(fields=['company', 'user']),
            models.Index(fields=['company', 'interaction_type']),
            models.Index(fields=['company', 'session_id']),
        ]
    
    def __str__(self):
        return f"{self.assistant.name} - {self.user_input[:50]}"

class PredictiveModel(CompanyIsolatedModel):
    """Predictive analytics models"""
    
    MODEL_TYPES = [
        ('lead_scoring', 'Lead Scoring'),
        ('deal_forecasting', 'Deal Forecasting'),
        ('churn_prediction', 'Churn Prediction'),
        ('revenue_prediction', 'Revenue Prediction'),
        ('customer_lifetime_value', 'Customer Lifetime Value'),
        ('next_best_action', 'Next Best Action'),
    ]
    
    STATUS_CHOICES = [
        ('training', 'Training'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    model_type = models.CharField(
        max_length=30,
        choices=MODEL_TYPES
    )
    description = models.TextField(blank=True)
    
    # Model Configuration
    algorithm = models.CharField(
        max_length=50,
        default='random_forest',
        help_text="Machine learning algorithm"
    )
    parameters = models.JSONField(
        default=dict,
        help_text="Model parameters"
    )
    training_data = models.JSONField(
        default=dict,
        help_text="Training data configuration"
    )
    
    # Model Performance
    accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="Model accuracy score"
    )
    precision = models.FloatField(
        null=True,
        blank=True,
        help_text="Model precision score"
    )
    recall = models.FloatField(
        null=True,
        blank=True,
        help_text="Model recall score"
    )
    f1_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Model F1 score"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='training'
    )
    is_active = models.BooleanField(default=True)
    
    # Training Information
    last_trained = models.DateTimeField(null=True, blank=True)
    training_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Training duration in seconds"
    )
    training_samples = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of training samples"
    )
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_models'
    )
    
    class Meta:
        db_table = 'predictive_model'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.model_type})"

class Prediction(CompanyIsolatedModel):
    """Individual predictions made by models"""
    
    # Basic Information
    model = models.ForeignKey(
        PredictiveModel,
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    
    # Related Entity (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="Type of entity being predicted"
    )
    object_id = models.UUIDField(help_text="ID of the entity")
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Prediction Results
    prediction_value = models.FloatField(help_text="Predicted value")
    confidence_score = models.FloatField(
        help_text="Confidence in prediction (0.0-1.0)"
    )
    prediction_details = models.JSONField(
        default=dict,
        help_text="Detailed prediction information"
    )
    
    # Actual Results (for validation)
    actual_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Actual value (if available)"
    )
    prediction_accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="Accuracy of this prediction"
    )
    
    # Metadata
    input_features = models.JSONField(
        default=dict,
        help_text="Input features used for prediction"
    )
    model_version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Model version used"
    )
    
    class Meta:
        db_table = 'prediction'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'model']),
            models.Index(fields=['company', 'content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.model.name} - {self.prediction_value}"

class AnomalyDetection(CompanyIsolatedModel):
    """Anomaly detection results"""
    
    ANOMALY_TYPES = [
        ('sales_spike', 'Sales Spike'),
        ('revenue_drop', 'Revenue Drop'),
        ('lead_quality_change', 'Lead Quality Change'),
        ('customer_behavior', 'Customer Behavior'),
        ('system_performance', 'System Performance'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Basic Information
    anomaly_type = models.CharField(
        max_length=30,
        choices=ANOMALY_TYPES
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_LEVELS,
        default='medium'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Detection Details
    detected_at = models.DateTimeField()
    confidence_score = models.FloatField(
        help_text="Confidence in anomaly detection (0.0-1.0)"
    )
    anomaly_score = models.FloatField(
        help_text="Anomaly score (higher = more anomalous)"
    )
    
    # Related Data
    related_data = models.JSONField(
        default=dict,
        help_text="Related data that triggered the anomaly"
    )
    baseline_data = models.JSONField(
        default=dict,
        help_text="Baseline data for comparison"
    )
    
    # Status
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_anomalies'
    )
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'anomaly_detection'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['company', 'anomaly_type']),
            models.Index(fields=['company', 'severity']),
            models.Index(fields=['company', 'is_resolved']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.severity}"
