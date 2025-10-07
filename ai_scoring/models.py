# ai_scoring/models.py
# AI Lead Scoring and Model Training Models

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import CompanyIsolatedModel, User
import uuid
import json
from datetime import datetime, timedelta

class ScoringModel(CompanyIsolatedModel):
    """AI scoring models for leads and other entities"""
    
    MODEL_TYPES = [
        ('lead_scoring', 'Lead Scoring'),
        ('deal_scoring', 'Deal Scoring'),
        ('customer_scoring', 'Customer Scoring'),
        ('churn_scoring', 'Churn Scoring'),
        ('upsell_scoring', 'Upsell Scoring'),
        ('custom', 'Custom'),
    ]
    
    ALGORITHMS = [
        ('random_forest', 'Random Forest'),
        ('gradient_boosting', 'Gradient Boosting'),
        ('neural_network', 'Neural Network'),
        ('logistic_regression', 'Logistic Regression'),
        ('svm', 'Support Vector Machine'),
        ('naive_bayes', 'Naive Bayes'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('training', 'Training'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('deprecated', 'Deprecated'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    model_type = models.CharField(
        max_length=30,
        choices=MODEL_TYPES
    )
    algorithm = models.CharField(
        max_length=30,
        choices=ALGORITHMS,
        default='random_forest'
    )
    
    # Model Configuration
    configuration = models.JSONField(
        default=dict,
        help_text="Model configuration parameters"
    )
    features = models.JSONField(
        default=list,
        help_text="Model features and their configurations"
    )
    target_variable = models.CharField(
        max_length=255,
        help_text="Target variable for prediction"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_active = models.BooleanField(default=True)
    
    # Performance Metrics
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
    auc_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Model AUC score"
    )
    
    # Training Information
    training_data_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="Size of training dataset"
    )
    validation_data_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="Size of validation dataset"
    )
    last_trained = models.DateTimeField(null=True, blank=True)
    training_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Training duration in seconds"
    )
    
    # Model Versioning
    version = models.CharField(max_length=50, default='1.0.0')
    is_latest = models.BooleanField(default=True)
    parent_model = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_models'
    )
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_scoring_models'
    )
    
    class Meta:
        db_table = 'scoring_model'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'model_type']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.model_type})"

class ModelTraining(CompanyIsolatedModel):
    """Model training sessions and results"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    model = models.ForeignKey(
        ScoringModel,
        on_delete=models.CASCADE,
        related_name='trainings'
    )
    training_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Training Configuration
    training_config = models.JSONField(
        default=dict,
        help_text="Training configuration"
    )
    hyperparameters = models.JSONField(
        default=dict,
        help_text="Model hyperparameters"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Training Data
    training_data_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="Size of training dataset"
    )
    validation_data_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="Size of validation dataset"
    )
    test_data_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="Size of test dataset"
    )
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Training duration in seconds"
    )
    
    # Results
    training_accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="Training accuracy"
    )
    validation_accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="Validation accuracy"
    )
    test_accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="Test accuracy"
    )
    
    # Performance Metrics
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    auc_score = models.FloatField(null=True, blank=True)
    
    # Error Handling
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)
    
    # Resource Usage
    memory_usage_mb = models.IntegerField(
        null=True,
        blank=True,
        help_text="Peak memory usage in MB"
    )
    cpu_usage_percent = models.FloatField(
        null=True,
        blank=True,
        help_text="Average CPU usage percentage"
    )
    
    class Meta:
        db_table = 'model_training'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'model']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.model.name} - {self.training_name}"

class ModelPrediction(CompanyIsolatedModel):
    """Model predictions and scores"""
    
    PREDICTION_TYPES = [
        ('lead_score', 'Lead Score'),
        ('deal_score', 'Deal Score'),
        ('churn_probability', 'Churn Probability'),
        ('conversion_probability', 'Conversion Probability'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    model = models.ForeignKey(
        ScoringModel,
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    prediction_type = models.CharField(
        max_length=30,
        choices=PREDICTION_TYPES
    )
    
    # Related Entity (Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="Type of entity being scored"
    )
    object_id = models.UUIDField(help_text="ID of the entity")
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Prediction Results
    score = models.FloatField(
        help_text="Prediction score (0.0-1.0)"
    )
    confidence = models.FloatField(
        help_text="Prediction confidence (0.0-1.0)"
    )
    probability = models.FloatField(
        null=True,
        blank=True,
        help_text="Prediction probability"
    )
    
    # Input Features
    input_features = models.JSONField(
        default=dict,
        help_text="Input features used for prediction"
    )
    feature_importance = models.JSONField(
        default=dict,
        help_text="Feature importance scores"
    )
    
    # Explanation
    explanation = models.JSONField(
        default=dict,
        help_text="Prediction explanation (SHAP values, etc.)"
    )
    reasoning = models.TextField(
        blank=True,
        help_text="Human-readable explanation"
    )
    
    # Validation
    actual_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Actual value for validation"
    )
    prediction_accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="Prediction accuracy"
    )
    
    # Metadata
    model_version = models.CharField(
        max_length=50,
        help_text="Model version used"
    )
    prediction_metadata = models.JSONField(
        default=dict,
        help_text="Additional prediction metadata"
    )
    
    class Meta:
        db_table = 'model_prediction'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'model']),
            models.Index(fields=['company', 'content_type', 'object_id']),
            models.Index(fields=['company', 'prediction_type']),
        ]
    
    def __str__(self):
        return f"{self.model.name} - {self.score:.3f}"

class ModelDrift(CompanyIsolatedModel):
    """Model drift detection and monitoring"""
    
    DRIFT_TYPES = [
        ('data_drift', 'Data Drift'),
        ('concept_drift', 'Concept Drift'),
        ('feature_drift', 'Feature Drift'),
        ('target_drift', 'Target Drift'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Basic Information
    model = models.ForeignKey(
        ScoringModel,
        on_delete=models.CASCADE,
        related_name='drift_detections'
    )
    drift_type = models.CharField(
        max_length=20,
        choices=DRIFT_TYPES
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_LEVELS,
        default='medium'
    )
    
    # Drift Detection
    drift_score = models.FloatField(
        help_text="Drift score (0.0-1.0)"
    )
    threshold = models.FloatField(
        help_text="Drift threshold"
    )
    is_drift_detected = models.BooleanField(default=False)
    
    # Data Comparison
    baseline_data = models.JSONField(
        default=dict,
        help_text="Baseline data statistics"
    )
    current_data = models.JSONField(
        default=dict,
        help_text="Current data statistics"
    )
    comparison_metrics = models.JSONField(
        default=dict,
        help_text="Statistical comparison metrics"
    )
    
    # Detection Details
    detection_method = models.CharField(
        max_length=100,
        help_text="Method used for drift detection"
    )
    detection_parameters = models.JSONField(
        default=dict,
        help_text="Detection method parameters"
    )
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    baseline_period_start = models.DateTimeField()
    baseline_period_end = models.DateTimeField()
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    
    # Status
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'model_drift'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['company', 'model']),
            models.Index(fields=['company', 'drift_type']),
            models.Index(fields=['company', 'severity']),
            models.Index(fields=['company', 'is_drift_detected']),
        ]
    
    def __str__(self):
        return f"{self.model.name} - {self.drift_type} ({self.severity})"

class ModelValidation(CompanyIsolatedModel):
    """Model validation and testing"""
    
    VALIDATION_TYPES = [
        ('cross_validation', 'Cross Validation'),
        ('holdout_validation', 'Holdout Validation'),
        ('time_series_validation', 'Time Series Validation'),
        ('bootstrap_validation', 'Bootstrap Validation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Basic Information
    model = models.ForeignKey(
        ScoringModel,
        on_delete=models.CASCADE,
        related_name='validations'
    )
    validation_name = models.CharField(max_length=255)
    validation_type = models.CharField(
        max_length=30,
        choices=VALIDATION_TYPES
    )
    description = models.TextField(blank=True)
    
    # Validation Configuration
    validation_config = models.JSONField(
        default=dict,
        help_text="Validation configuration"
    )
    test_data_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="Size of test dataset"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Validation duration in seconds"
    )
    
    # Results
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    auc_score = models.FloatField(null=True, blank=True)
    
    # Validation Metrics
    validation_metrics = models.JSONField(
        default=dict,
        help_text="Detailed validation metrics"
    )
    confusion_matrix = models.JSONField(
        default=dict,
        help_text="Confusion matrix results"
    )
    roc_curve = models.JSONField(
        default=dict,
        help_text="ROC curve data"
    )
    
    # Error Handling
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)
    
    class Meta:
        db_table = 'model_validation'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'model']),
            models.Index(fields=['company', 'status']),
        ]
    
    def __str__(self):
        return f"{self.model.name} - {self.validation_name}"

class ModelFeature(CompanyIsolatedModel):
    """Model features and their configurations"""
    
    FEATURE_TYPES = [
        ('numerical', 'Numerical'),
        ('categorical', 'Categorical'),
        ('text', 'Text'),
        ('datetime', 'DateTime'),
        ('boolean', 'Boolean'),
    ]
    
    # Basic Information
    model = models.ForeignKey(
        ScoringModel,
        on_delete=models.CASCADE,
        related_name='model_features'
    )
    feature_name = models.CharField(max_length=255)
    feature_type = models.CharField(
        max_length=20,
        choices=FEATURE_TYPES
    )
    description = models.TextField(blank=True)
    
    # Feature Configuration
    feature_config = models.JSONField(
        default=dict,
        help_text="Feature configuration"
    )
    preprocessing_steps = models.JSONField(
        default=list,
        help_text="Preprocessing steps for the feature"
    )
    
    # Statistics
    importance_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Feature importance score"
    )
    correlation_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Correlation with target variable"
    )
    
    # Data Quality
    missing_value_percentage = models.FloatField(
        null=True,
        blank=True,
        help_text="Percentage of missing values"
    )
    outlier_percentage = models.FloatField(
        null=True,
        blank=True,
        help_text="Percentage of outliers"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_required = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'model_feature'
        ordering = ['-importance_score', 'feature_name']
        indexes = [
            models.Index(fields=['company', 'model']),
            models.Index(fields=['company', 'feature_type']),
        ]
        unique_together = ['company', 'model', 'feature_name']
    
    def __str__(self):
        return f"{self.model.name} - {self.feature_name}"

class ModelInsight(CompanyIsolatedModel):
    """Model insights and explanations"""
    
    INSIGHT_TYPES = [
        ('feature_importance', 'Feature Importance'),
        ('prediction_explanation', 'Prediction Explanation'),
        ('model_performance', 'Model Performance'),
        ('data_quality', 'Data Quality'),
        ('bias_detection', 'Bias Detection'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    model = models.ForeignKey(
        ScoringModel,
        on_delete=models.CASCADE,
        related_name='insights'
    )
    insight_type = models.CharField(
        max_length=30,
        choices=INSIGHT_TYPES
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Insight Data
    insight_data = models.JSONField(
        default=dict,
        help_text="Insight data and metrics"
    )
    visualizations = models.JSONField(
        default=list,
        help_text="Visualization configurations"
    )
    
    # Recommendations
    recommendations = models.TextField(
        blank=True,
        help_text="Recommendations based on insight"
    )
    action_items = models.JSONField(
        default=list,
        help_text="Action items from insight"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )
    
    class Meta:
        db_table = 'model_insight'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'model']),
            models.Index(fields=['company', 'insight_type']),
            models.Index(fields=['company', 'priority']),
        ]
    
    def __str__(self):
        return f"{self.model.name} - {self.title}"
