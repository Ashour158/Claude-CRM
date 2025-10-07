# ai_scoring/admin.py
# AI Lead Scoring and Model Training Admin Configuration

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    ScoringModel, ModelTraining, ModelPrediction, ModelDrift,
    ModelValidation, ModelFeature, ModelInsight
)

@admin.register(ScoringModel)
class ScoringModelAdmin(admin.ModelAdmin):
    """Scoring model admin interface"""
    list_display = [
        'name', 'model_type', 'algorithm', 'status', 'is_active',
        'is_trained', 'accuracy', 'owner', 'last_trained'
    ]
    list_filter = [
        'model_type', 'algorithm', 'status', 'is_active', 'is_trained',
        'owner', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'last_trained', 'training_duration', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['owner', 'parent_model']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'model_type', 'algorithm')
        }),
        ('Configuration', {
            'fields': ('configuration', 'features', 'target_variable')
        }),
        ('Performance Metrics', {
            'fields': ('accuracy', 'precision', 'recall', 'f1_score', 'auc_score')
        }),
        ('Status', {
            'fields': ('status', 'is_active', 'is_trained')
        }),
        ('Training Information', {
            'fields': ('training_data_size', 'validation_data_size', 'last_trained', 'training_duration'),
            'classes': ('collapse',)
        }),
        ('Versioning', {
            'fields': ('version', 'is_latest', 'parent_model'),
            'classes': ('collapse',)
        }),
        ('Owner', {
            'fields': ('owner',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ModelTraining)
class ModelTrainingAdmin(admin.ModelAdmin):
    """Model training admin interface"""
    list_display = [
        'training_name', 'model', 'status', 'started_at',
        'completed_at', 'training_accuracy', 'created_at'
    ]
    list_filter = [
        'status', 'model', 'started_at', 'completed_at', 'created_at'
    ]
    search_fields = ['training_name', 'description', 'model__name']
    readonly_fields = [
        'started_at', 'completed_at', 'duration_seconds', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['model']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('model', 'training_name', 'description', 'validation_type')
        }),
        ('Configuration', {
            'fields': ('training_config', 'hyperparameters')
        }),
        ('Data Sizes', {
            'fields': ('training_data_size', 'validation_data_size', 'test_data_size')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
        ('Results', {
            'fields': ('training_accuracy', 'validation_accuracy', 'test_accuracy'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('precision', 'recall', 'f1_score', 'auc_score'),
            'classes': ('collapse',)
        }),
        ('Error Handling', {
            'fields': ('error_message', 'error_traceback'),
            'classes': ('collapse',)
        }),
        ('Resource Usage', {
            'fields': ('memory_usage_mb', 'cpu_usage_percent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ModelPrediction)
class ModelPredictionAdmin(admin.ModelAdmin):
    """Model prediction admin interface"""
    list_display = [
        'model', 'prediction_type', 'score', 'confidence',
        'content_type', 'object_id', 'created_at'
    ]
    list_filter = [
        'prediction_type', 'model', 'content_type', 'created_at'
    ]
    search_fields = ['reasoning', 'model__name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['model']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('model', 'prediction_type', 'content_type', 'object_id')
        }),
        ('Prediction Results', {
            'fields': ('score', 'confidence', 'probability')
        }),
        ('Input and Features', {
            'fields': ('input_features', 'feature_importance'),
            'classes': ('collapse',)
        }),
        ('Explanation', {
            'fields': ('explanation', 'reasoning'),
            'classes': ('collapse',)
        }),
        ('Validation', {
            'fields': ('actual_value', 'prediction_accuracy'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('model_version', 'prediction_metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ModelDrift)
class ModelDriftAdmin(admin.ModelAdmin):
    """Model drift admin interface"""
    list_display = [
        'model', 'drift_type', 'severity', 'drift_score',
        'is_drift_detected', 'detected_at', 'is_resolved'
    ]
    list_filter = [
        'drift_type', 'severity', 'is_drift_detected', 'is_resolved',
        'model', 'detected_at'
    ]
    search_fields = ['model__name']
    readonly_fields = [
        'detected_at', 'resolved_at', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['model']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('model', 'drift_type', 'severity')
        }),
        ('Drift Detection', {
            'fields': ('drift_score', 'threshold', 'is_drift_detected')
        }),
        ('Data Comparison', {
            'fields': ('baseline_data', 'current_data', 'comparison_metrics'),
            'classes': ('collapse',)
        }),
        ('Detection Details', {
            'fields': ('detection_method', 'detection_parameters'),
            'classes': ('collapse',)
        }),
        ('Time Periods', {
            'fields': ('detected_at', 'baseline_period_start', 'baseline_period_end',
                      'current_period_start', 'current_period_end'),
            'classes': ('collapse',)
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_at', 'resolution_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ModelValidation)
class ModelValidationAdmin(admin.ModelAdmin):
    """Model validation admin interface"""
    list_display = [
        'validation_name', 'model', 'validation_type', 'status',
        'started_at', 'completed_at', 'accuracy'
    ]
    list_filter = [
        'validation_type', 'status', 'model', 'started_at', 'completed_at'
    ]
    search_fields = ['validation_name', 'description', 'model__name']
    readonly_fields = [
        'started_at', 'completed_at', 'duration_seconds', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['model']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('model', 'validation_name', 'validation_type', 'description')
        }),
        ('Configuration', {
            'fields': ('validation_config', 'test_data_size')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
        ('Results', {
            'fields': ('accuracy', 'precision', 'recall', 'f1_score', 'auc_score')
        }),
        ('Validation Metrics', {
            'fields': ('validation_metrics', 'confusion_matrix', 'roc_curve'),
            'classes': ('collapse',)
        }),
        ('Error Handling', {
            'fields': ('error_message', 'error_traceback'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ModelFeature)
class ModelFeatureAdmin(admin.ModelAdmin):
    """Model feature admin interface"""
    list_display = [
        'feature_name', 'model', 'feature_type', 'importance_score',
        'correlation_score', 'is_active', 'is_required'
    ]
    list_filter = [
        'feature_type', 'is_active', 'is_required', 'model', 'created_at'
    ]
    search_fields = ['feature_name', 'description', 'model__name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['model']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('model', 'feature_name', 'feature_type', 'description')
        }),
        ('Configuration', {
            'fields': ('feature_config', 'preprocessing_steps')
        }),
        ('Statistics', {
            'fields': ('importance_score', 'correlation_score')
        }),
        ('Data Quality', {
            'fields': ('missing_value_percentage', 'outlier_percentage'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_required')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ModelInsight)
class ModelInsightAdmin(admin.ModelAdmin):
    """Model insight admin interface"""
    list_display = [
        'title', 'model', 'insight_type', 'priority', 'is_active', 'created_at'
    ]
    list_filter = [
        'insight_type', 'priority', 'is_active', 'model', 'created_at'
    ]
    search_fields = ['title', 'description', 'model__name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['model']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('model', 'insight_type', 'title', 'description')
        }),
        ('Insight Data', {
            'fields': ('insight_data', 'visualizations'),
            'classes': ('collapse',)
        }),
        ('Recommendations', {
            'fields': ('recommendations', 'action_items'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'priority')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
