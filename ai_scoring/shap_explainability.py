# ai_scoring/shap_explainability.py
# SHAP Explainability with TreeExplainer and Feature Mapping

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
import shap
import pickle
from celery import shared_task

from .models import (
    MLModel, ModelTraining, ModelPrediction, SHAPExplanation,
    FeatureImportance, SHAPCache, SHAPFeatureMapping
)
from core.models import User, Company
from crm.models import Lead, Deal, Account

logger = logging.getLogger(__name__)

class SHAPExplainabilityEngine:
    """
    Advanced SHAP explainability engine with TreeExplainer,
    feature mapping, and intelligent caching.
    """
    
    def __init__(self):
        self.explainer_types = {
            'tree': shap.TreeExplainer,
            'linear': shap.LinearExplainer,
            'kernel': shap.KernelExplainer,
            'deep': shap.DeepExplainer
        }
        
        self.shap_cache_config = {
            'cache_duration': 3600,  # 1 hour
            'max_cache_size': 1000,
            'warm_cache_strategy': True
        }
    
    def explain_prediction(self, model_id: str, features: Dict[str, Any], 
                          explanation_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SHAP explanation for a prediction.
        """
        try:
            model_record = MLModel.objects.get(id=model_id)
            
            # Check cache first
            cache_key = self._generate_cache_key(model_id, features, explanation_config)
            cached_explanation = cache.get(cache_key)
            
            if cached_explanation and not explanation_config.get('force_refresh', False):
                return {
                    'status': 'success',
                    'explanation': cached_explanation,
                    'cached': True,
                    'timestamp': cached_explanation.get('timestamp')
                }
            
            # Load model and explainer
            model = pickle.loads(model_record.model_data)
            explainer = self._get_or_create_explainer(model, model_record, explanation_config)
            
            # Prepare features
            feature_vector = self._prepare_features_for_explanation(features, model_record.feature_columns)
            
            # Generate SHAP values
            shap_values = self._calculate_shap_values(explainer, feature_vector, explanation_config)
            
            # Map features to human-readable names
            feature_mapping = self._get_feature_mapping(model_record)
            mapped_explanation = self._map_shap_to_features(shap_values, feature_mapping, model_record.feature_columns)
            
            # Generate explanation text
            explanation_text = self._generate_explanation_text(mapped_explanation, explanation_config)
            
            # Create comprehensive explanation
            explanation = {
                'shap_values': shap_values.tolist(),
                'feature_contributions': mapped_explanation,
                'explanation_text': explanation_text,
                'model_id': model_id,
                'timestamp': timezone.now().isoformat(),
                'explainer_type': explanation_config.get('explainer_type', 'tree')
            }
            
            # Cache explanation
            cache.set(cache_key, explanation, self.shap_cache_config['cache_duration'])
            
            # Save to database
            explanation_record = self._save_explanation(model_record, explanation, features)
            
            return {
                'status': 'success',
                'explanation': explanation,
                'explanation_id': str(explanation_record.id),
                'cached': False
            }
            
        except Exception as e:
            logger.error(f"SHAP explanation failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def explain_model_global(self, model_id: str, explanation_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate global SHAP explanation for the entire model.
        """
        try:
            model_record = MLModel.objects.get(id=model_id)
            
            # Check cache
            cache_key = f"shap_global_{model_id}_{hashlib.md5(str(explanation_config).encode()).hexdigest()[:8]}"
            cached_explanation = cache.get(cache_key)
            
            if cached_explanation and not explanation_config.get('force_refresh', False):
                return {
                    'status': 'success',
                    'explanation': cached_explanation,
                    'cached': True
                }
            
            # Load model and explainer
            model = pickle.loads(model_record.model_data)
            explainer = self._get_or_create_explainer(model, model_record, explanation_config)
            
            # Get sample data for global explanation
            sample_data = self._get_sample_data_for_global_explanation(model_record, explanation_config)
            
            # Calculate global SHAP values
            global_shap_values = self._calculate_global_shap_values(explainer, sample_data, explanation_config)
            
            # Generate global feature importance
            global_importance = self._calculate_global_feature_importance(global_shap_values, model_record.feature_columns)
            
            # Create global explanation
            global_explanation = {
                'global_shap_values': global_shap_values.tolist(),
                'global_importance': global_importance,
                'feature_names': model_record.feature_columns,
                'model_id': model_id,
                'timestamp': timezone.now().isoformat(),
                'explainer_type': explanation_config.get('explainer_type', 'tree')
            }
            
            # Cache global explanation
            cache.set(cache_key, global_explanation, self.shap_cache_config['cache_duration'])
            
            return {
                'status': 'success',
                'explanation': global_explanation,
                'cached': False
            }
            
        except Exception as e:
            logger.error(f"Global SHAP explanation failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def batch_explain_predictions(self, model_id: str, predictions_data: List[Dict[str, Any]], 
                                 explanation_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SHAP explanations for multiple predictions in batch.
        """
        try:
            model_record = MLModel.objects.get(id=model_id)
            
            # Load model and explainer
            model = pickle.loads(model_record.model_data)
            explainer = self._get_or_create_explainer(model, model_record, explanation_config)
            
            # Prepare batch data
            batch_features = []
            for pred_data in predictions_data:
                feature_vector = self._prepare_features_for_explanation(
                    pred_data['features'], model_record.feature_columns
                )
                batch_features.append(feature_vector)
            
            batch_features = np.array(batch_features)
            
            # Calculate batch SHAP values
            batch_shap_values = self._calculate_batch_shap_values(explainer, batch_features, explanation_config)
            
            # Generate explanations for each prediction
            explanations = []
            for i, (pred_data, shap_values) in enumerate(zip(predictions_data, batch_shap_values)):
                feature_mapping = self._get_feature_mapping(model_record)
                mapped_explanation = self._map_shap_to_features(
                    shap_values, feature_mapping, model_record.feature_columns
                )
                
                explanation_text = self._generate_explanation_text(mapped_explanation, explanation_config)
                
                explanations.append({
                    'prediction_id': pred_data.get('prediction_id'),
                    'shap_values': shap_values.tolist(),
                    'feature_contributions': mapped_explanation,
                    'explanation_text': explanation_text
                })
            
            return {
                'status': 'success',
                'explanations': explanations,
                'batch_size': len(predictions_data),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch SHAP explanation failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_or_create_explainer(self, model, model_record: MLModel, config: Dict[str, Any]):
        """Get or create SHAP explainer"""
        explainer_type = config.get('explainer_type', 'tree')
        
        # Check if explainer is cached
        cache_key = f"shap_explainer_{model_record.id}_{explainer_type}"
        cached_explainer = cache.get(cache_key)
        
        if cached_explainer:
            return cached_explainer
        
        # Create new explainer
        explainer_class = self.explainer_types.get(explainer_type)
        if not explainer_class:
            raise ValueError(f"Unsupported explainer type: {explainer_type}")
        
        try:
            if explainer_type == 'tree':
                explainer = explainer_class(model)
            elif explainer_type == 'linear':
                explainer = explainer_class(model)
            elif explainer_type == 'kernel':
                # For kernel explainer, we need background data
                background_data = self._get_background_data(model_record)
                explainer = explainer_class(model.predict, background_data)
            elif explainer_type == 'deep':
                explainer = explainer_class(model)
            
            # Cache explainer
            cache.set(cache_key, explainer, 7200)  # Cache for 2 hours
            
            return explainer
            
        except Exception as e:
            logger.error(f"Failed to create SHAP explainer: {str(e)}")
            raise
    
    def _calculate_shap_values(self, explainer, feature_vector: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """Calculate SHAP values for a single prediction"""
        try:
            # Calculate SHAP values
            shap_values = explainer.shap_values(feature_vector.reshape(1, -1))
            
            # Handle different explainer outputs
            if isinstance(shap_values, list):
                # Multi-class case, take the positive class
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            
            return shap_values[0]  # Return first (and only) prediction
            
        except Exception as e:
            logger.error(f"SHAP calculation failed: {str(e)}")
            raise
    
    def _calculate_global_shap_values(self, explainer, sample_data: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """Calculate global SHAP values"""
        try:
            # Calculate SHAP values for sample data
            shap_values = explainer.shap_values(sample_data)
            
            # Handle multi-class case
            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            
            return shap_values
            
        except Exception as e:
            logger.error(f"Global SHAP calculation failed: {str(e)}")
            raise
    
    def _calculate_batch_shap_values(self, explainer, batch_features: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
        """Calculate SHAP values for batch predictions"""
        try:
            # Calculate SHAP values for batch
            shap_values = explainer.shap_values(batch_features)
            
            # Handle multi-class case
            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            
            return shap_values
            
        except Exception as e:
            logger.error(f"Batch SHAP calculation failed: {str(e)}")
            raise
    
    def _map_shap_to_features(self, shap_values: np.ndarray, feature_mapping: Dict[str, str], 
                            feature_columns: List[str]) -> List[Dict[str, Any]]:
        """Map SHAP values to human-readable feature names"""
        mapped_features = []
        
        for i, (feature_name, shap_value) in enumerate(zip(feature_columns, shap_values)):
            mapped_features.append({
                'feature_name': feature_name,
                'display_name': feature_mapping.get(feature_name, feature_name),
                'shap_value': float(shap_value),
                'contribution': 'positive' if shap_value > 0 else 'negative',
                'magnitude': abs(shap_value)
            })
        
        # Sort by absolute SHAP value
        mapped_features.sort(key=lambda x: x['magnitude'], reverse=True)
        
        return mapped_features
    
    def _generate_explanation_text(self, mapped_explanation: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Generate human-readable explanation text"""
        top_features = mapped_explanation[:config.get('top_k', 5)]
        
        explanation_parts = []
        
        # Positive contributions
        positive_features = [f for f in top_features if f['contribution'] == 'positive']
        if positive_features:
            pos_text = "Factors that increase the score: "
            pos_factors = [f"{f['display_name']} (+{f['shap_value']:.3f})" for f in positive_features]
            explanation_parts.append(pos_text + ", ".join(pos_factors))
        
        # Negative contributions
        negative_features = [f for f in top_features if f['contribution'] == 'negative']
        if negative_features:
            neg_text = "Factors that decrease the score: "
            neg_factors = [f"{f['display_name']} ({f['shap_value']:.3f})" for f in negative_features]
            explanation_parts.append(neg_text + ", ".join(neg_factors))
        
        return ". ".join(explanation_parts) + "."
    
    def _get_feature_mapping(self, model_record: MLModel) -> Dict[str, str]:
        """Get feature mapping for human-readable names"""
        try:
            # Get cached feature mapping
            cache_key = f"feature_mapping_{model_record.id}"
            cached_mapping = cache.get(cache_key)
            
            if cached_mapping:
                return cached_mapping
            
            # Create feature mapping
            feature_mapping = {}
            
            for feature_name in model_record.feature_columns:
                # Get mapping from database or create default
                mapping_record = SHAPFeatureMapping.objects.filter(
                    model=model_record,
                    feature_name=feature_name
                ).first()
                
                if mapping_record:
                    feature_mapping[feature_name] = mapping_record.display_name
                else:
                    # Create default mapping
                    display_name = self._create_default_display_name(feature_name)
                    feature_mapping[feature_name] = display_name
                    
                    # Save to database
                    SHAPFeatureMapping.objects.create(
                        model=model_record,
                        feature_name=feature_name,
                        display_name=display_name
                    )
            
            # Cache mapping
            cache.set(cache_key, feature_mapping, 3600)
            
            return feature_mapping
            
        except Exception as e:
            logger.error(f"Failed to get feature mapping: {str(e)}")
            return {}
    
    def _create_default_display_name(self, feature_name: str) -> str:
        """Create default display name for feature"""
        # Convert snake_case to Title Case
        display_name = feature_name.replace('_', ' ').title()
        
        # Apply common mappings
        mappings = {
            'Lead Source': 'Lead Source',
            'Lead Status': 'Lead Status',
            'Lead Priority': 'Lead Priority',
            'Lead Score': 'Lead Score',
            'Lead Age Days': 'Days Since Created',
            'Has Email': 'Has Email Address',
            'Has Phone': 'Has Phone Number',
            'Has Company': 'Has Company Name',
            'Email Domain Type': 'Email Type',
            'Phone Country Code': 'Phone Country',
            'Lead Notes Length': 'Notes Length',
            'Lead Tags Count': 'Number of Tags',
            'Company Size': 'Company Size',
            'Company Industry': 'Industry',
            'Company Type': 'Company Type',
            'Company Revenue': 'Annual Revenue',
            'Company Employees': 'Employee Count',
            'Company Website': 'Has Website',
            'Company Linkedin': 'Has LinkedIn',
            'Company Created Days': 'Company Age (Days)',
            'Company Has Deals': 'Has Existing Deals',
            'Company Deals Count': 'Number of Deals',
            'Company Deals Value': 'Total Deal Value',
            'Email Opens': 'Email Opens',
            'Email Clicks': 'Email Clicks',
            'Email Click Rate': 'Email Click Rate',
            'Page Views': 'Website Page Views',
            'Time On Site': 'Time on Website',
            'Engagement Score': 'Engagement Score',
            'Created Hour': 'Creation Hour',
            'Created Day Of Week': 'Creation Day',
            'Created Month': 'Creation Month',
            'Created Quarter': 'Creation Quarter',
            'Is Weekend': 'Created on Weekend',
            'Is Business Hours': 'Created During Business Hours',
            'Days Since Created': 'Days Since Created',
            'Weeks Since Created': 'Weeks Since Created',
            'Months Since Created': 'Months Since Created',
            'Activities Count': 'Number of Activities',
            'Emails Sent': 'Emails Sent',
            'Calls Made': 'Calls Made',
            'Total Interactions': 'Total Interactions'
        }
        
        return mappings.get(display_name, display_name)
    
    def _prepare_features_for_explanation(self, features: Dict[str, Any], feature_columns: List[str]) -> np.ndarray:
        """Prepare features for SHAP explanation"""
        feature_vector = []
        
        for col in feature_columns:
            value = features.get(col, 0)
            
            # Handle different data types
            if isinstance(value, str):
                # Simple hash encoding for categorical
                value = hash(value) % 1000
            
            feature_vector.append(float(value))
        
        return np.array(feature_vector)
    
    def _get_sample_data_for_global_explanation(self, model_record: MLModel, config: Dict[str, Any]) -> np.ndarray:
        """Get sample data for global explanation"""
        # This would get actual sample data from the training set
        # For now, return a placeholder
        sample_size = config.get('sample_size', 100)
        feature_count = len(model_record.feature_columns)
        
        # Generate random sample data (in production, use actual training data)
        sample_data = np.random.randn(sample_size, feature_count)
        
        return sample_data
    
    def _get_background_data(self, model_record: MLModel) -> np.ndarray:
        """Get background data for kernel explainer"""
        # This would get actual background data from the training set
        # For now, return a placeholder
        background_size = 50
        feature_count = len(model_record.feature_columns)
        
        # Generate random background data (in production, use actual training data)
        background_data = np.random.randn(background_size, feature_count)
        
        return background_data
    
    def _calculate_global_feature_importance(self, global_shap_values: np.ndarray, feature_columns: List[str]) -> List[Dict[str, Any]]:
        """Calculate global feature importance from SHAP values"""
        # Calculate mean absolute SHAP values
        mean_abs_shap = np.mean(np.abs(global_shap_values), axis=0)
        
        # Create importance ranking
        importance_ranking = []
        for i, (feature_name, importance) in enumerate(zip(feature_columns, mean_abs_shap)):
            importance_ranking.append({
                'feature_name': feature_name,
                'importance_score': float(importance),
                'rank': i + 1
            })
        
        # Sort by importance
        importance_ranking.sort(key=lambda x: x['importance_score'], reverse=True)
        
        return importance_ranking
    
    def _save_explanation(self, model_record: MLModel, explanation: Dict[str, Any], features: Dict[str, Any]) -> SHAPExplanation:
        """Save SHAP explanation to database"""
        return SHAPExplanation.objects.create(
            model=model_record,
            shap_values=explanation['shap_values'],
            feature_contributions=explanation['feature_contributions'],
            explanation_text=explanation['explanation_text'],
            input_features=features,
            explainer_type=explanation['explainer_type'],
            created_at=timezone.now()
        )
    
    def _generate_cache_key(self, model_id: str, features: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate cache key for SHAP explanation"""
        import hashlib
        
        # Create hash of features and config
        features_str = json.dumps(features, sort_keys=True)
        config_str = json.dumps(config, sort_keys=True)
        combined_str = f"{model_id}_{features_str}_{config_str}"
        
        return f"shap_explanation_{hashlib.md5(combined_str.encode()).hexdigest()[:16]}"
    
    def warm_shap_cache(self, model_id: str, warm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Warm SHAP cache with common predictions"""
        try:
            model_record = MLModel.objects.get(id=model_id)
            
            # Get common prediction patterns
            common_patterns = self._get_common_prediction_patterns(model_record, warm_config)
            
            warmed_count = 0
            for pattern in common_patterns:
                try:
                    # Generate explanation to warm cache
                    explanation_result = self.explain_prediction(
                        model_id, pattern['features'], warm_config
                    )
                    
                    if explanation_result['status'] == 'success':
                        warmed_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to warm cache for pattern: {str(e)}")
                    continue
            
            return {
                'status': 'success',
                'warmed_count': warmed_count,
                'total_patterns': len(common_patterns)
            }
            
        except Exception as e:
            logger.error(f"SHAP cache warming failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_common_prediction_patterns(self, model_record: MLModel, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get common prediction patterns for cache warming"""
        # This would analyze historical predictions to find common patterns
        # For now, return some example patterns
        patterns = [
            {
                'features': {
                    'lead_source': 'website',
                    'lead_status': 'new',
                    'lead_priority': 'high',
                    'has_email': 1,
                    'has_phone': 1,
                    'company_size': 'medium'
                }
            },
            {
                'features': {
                    'lead_source': 'referral',
                    'lead_status': 'qualified',
                    'lead_priority': 'medium',
                    'has_email': 1,
                    'has_phone': 0,
                    'company_size': 'large'
                }
            }
        ]
        
        return patterns

# Celery tasks
@shared_task
def explain_prediction_async(model_id: str, features: Dict[str, Any], explanation_config: Dict[str, Any]):
    """Async task to generate SHAP explanation"""
    engine = SHAPExplainabilityEngine()
    return engine.explain_prediction(model_id, features, explanation_config)

@shared_task
def warm_shap_cache_async(model_id: str, warm_config: Dict[str, Any]):
    """Async task to warm SHAP cache"""
    engine = SHAPExplainabilityEngine()
    return engine.warm_shap_cache(model_id, warm_config)

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain_prediction(request):
    """API endpoint to explain prediction"""
    engine = SHAPExplainabilityEngine()
    result = engine.explain_prediction(
        request.data.get('model_id'),
        request.data.get('features', {}),
        request.data.get('explanation_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain_model_global(request):
    """API endpoint to explain model globally"""
    engine = SHAPExplainabilityEngine()
    result = engine.explain_model_global(
        request.data.get('model_id'),
        request.data.get('explanation_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_explain_predictions(request):
    """API endpoint to batch explain predictions"""
    engine = SHAPExplainabilityEngine()
    result = engine.batch_explain_predictions(
        request.data.get('model_id'),
        request.data.get('predictions_data', []),
        request.data.get('explanation_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def warm_shap_cache(request):
    """API endpoint to warm SHAP cache"""
    engine = SHAPExplainabilityEngine()
    result = engine.warm_shap_cache(
        request.data.get('model_id'),
        request.data.get('warm_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)
