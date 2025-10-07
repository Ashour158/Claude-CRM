# ai_scoring/drift_detection.py
# Drift Detection with PSI/KL and Performance Counters

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
from scipy import stats
from scipy.stats import entropy
import joblib
import pickle
from celery import shared_task

from .models import (
    MLModel, ModelDrift, DriftAlert, DriftMetrics, 
    PerformanceCounter, DriftThreshold, DriftJob
)
from core.models import User, Company
from crm.models import Lead, Deal, Account

logger = logging.getLogger(__name__)

class DriftDetectionEngine:
    """
    Advanced drift detection engine with PSI/KL divergence,
    performance counters, and automated retraining triggers.
    """
    
    def __init__(self):
        self.drift_metrics = {
            'psi': self._calculate_psi,
            'kl_divergence': self._calculate_kl_divergence,
            'wasserstein': self._calculate_wasserstein_distance,
            'ks_test': self._calculate_ks_test,
            'chi_square': self._calculate_chi_square_test
        }
        
        self.drift_thresholds = {
            'psi': {'low': 0.1, 'medium': 0.2, 'high': 0.25},
            'kl_divergence': {'low': 0.1, 'medium': 0.3, 'high': 0.5},
            'wasserstein': {'low': 0.1, 'medium': 0.2, 'high': 0.3},
            'ks_test': {'low': 0.05, 'medium': 0.1, 'high': 0.2}
        }
        
        self.performance_counters = {
            'prediction_accuracy': self._calculate_prediction_accuracy,
            'prediction_confidence': self._calculate_prediction_confidence,
            'feature_distribution': self._calculate_feature_distribution_drift,
            'target_distribution': self._calculate_target_distribution_drift
        }
    
    def detect_drift(self, model_id: str, current_data: List[Dict[str, Any]], 
                     drift_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect drift in model performance and data distribution.
        """
        try:
            model_record = MLModel.objects.get(id=model_id)
            
            # Get reference data
            reference_data = self._get_reference_data(model_record, drift_config)
            
            if not reference_data:
                return {
                    'status': 'error',
                    'error': 'No reference data available for drift detection'
                }
            
            # Prepare data for drift detection
            ref_features, ref_targets = self._prepare_data_for_drift(reference_data, model_record.feature_columns)
            curr_features, curr_targets = self._prepare_data_for_drift(current_data, model_record.feature_columns)
            
            # Calculate drift metrics
            drift_results = {}
            for metric_name, metric_func in self.drift_metrics.items():
                try:
                    if metric_name in ['psi', 'kl_divergence']:
                        # These metrics work on distributions
                        drift_score = self._calculate_distribution_drift(
                            ref_features, curr_features, metric_func
                        )
                    else:
                        # These metrics work on individual features
                        drift_score = self._calculate_feature_drift(
                            ref_features, curr_features, metric_func
                        )
                    
                    drift_results[metric_name] = {
                        'score': drift_score,
                        'severity': self._classify_drift_severity(metric_name, drift_score)
                    }
                except Exception as e:
                    logger.error(f"Drift calculation failed for {metric_name}: {str(e)}")
                    drift_results[metric_name] = {
                        'score': None,
                        'severity': 'error',
                        'error': str(e)
                    }
            
            # Calculate performance drift
            performance_drift = self._calculate_performance_drift(model_record, current_data, drift_config)
            
            # Determine overall drift status
            overall_drift = self._determine_overall_drift(drift_results, performance_drift)
            
            # Create drift record
            drift_record = self._save_drift_detection(
                model_record, drift_results, performance_drift, overall_drift
            )
            
            # Check if retraining is needed
            retraining_needed = self._check_retraining_trigger(drift_record, drift_config)
            
            if retraining_needed:
                # Trigger retraining
                self._trigger_model_retraining(model_record, drift_record)
            
            return {
                'status': 'success',
                'drift_detected': overall_drift['drift_detected'],
                'drift_severity': overall_drift['severity'],
                'drift_metrics': drift_results,
                'performance_drift': performance_drift,
                'retraining_triggered': retraining_needed,
                'drift_id': str(drift_record.id),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Drift detection failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def run_daily_drift_job(self, company_id: str, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run daily drift detection job for all active models.
        """
        try:
            company = Company.objects.get(id=company_id)
            
            # Get active models
            active_models = MLModel.objects.filter(
                company=company,
                is_active=True
            )
            
            if not active_models.exists():
                return {
                    'status': 'success',
                    'message': 'No active models found for drift detection',
                    'models_checked': 0
                }
            
            # Create drift job record
            drift_job = DriftJob.objects.create(
                company=company,
                job_type='daily_drift_detection',
                status='running',
                started_at=timezone.now(),
                configuration=job_config
            )
            
            drift_results = []
            models_checked = 0
            
            for model in active_models:
                try:
                    # Get recent data for drift detection
                    recent_data = self._get_recent_data_for_model(model, job_config)
                    
                    if not recent_data:
                        logger.warning(f"No recent data available for model {model.id}")
                        continue
                    
                    # Run drift detection
                    drift_result = self.detect_drift(
                        str(model.id), recent_data, job_config
                    )
                    
                    drift_results.append({
                        'model_id': str(model.id),
                        'model_name': model.model_name,
                        'drift_result': drift_result
                    })
                    
                    models_checked += 1
                    
                except Exception as e:
                    logger.error(f"Drift detection failed for model {model.id}: {str(e)}")
                    drift_results.append({
                        'model_id': str(model.id),
                        'model_name': model.model_name,
                        'error': str(e)
                    })
            
            # Update job status
            drift_job.status = 'completed'
            drift_job.completed_at = timezone.now()
            drift_job.results = drift_results
            drift_job.models_checked = models_checked
            drift_job.save()
            
            return {
                'status': 'success',
                'job_id': str(drift_job.id),
                'models_checked': models_checked,
                'drift_results': drift_results,
                'completed_at': drift_job.completed_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Daily drift job failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _calculate_psi(self, ref_dist: np.ndarray, curr_dist: np.ndarray) -> float:
        """Calculate Population Stability Index (PSI)"""
        try:
            # Ensure distributions are normalized
            ref_dist = ref_dist / np.sum(ref_dist)
            curr_dist = curr_dist / np.sum(curr_dist)
            
            # Add small epsilon to avoid division by zero
            epsilon = 1e-6
            ref_dist = ref_dist + epsilon
            curr_dist = curr_dist + epsilon
            
            # Calculate PSI
            psi = np.sum((curr_dist - ref_dist) * np.log(curr_dist / ref_dist))
            
            return float(psi)
            
        except Exception as e:
            logger.error(f"PSI calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_kl_divergence(self, ref_dist: np.ndarray, curr_dist: np.ndarray) -> float:
        """Calculate Kullback-Leibler divergence"""
        try:
            # Ensure distributions are normalized
            ref_dist = ref_dist / np.sum(ref_dist)
            curr_dist = curr_dist / np.sum(curr_dist)
            
            # Add small epsilon to avoid division by zero
            epsilon = 1e-6
            ref_dist = ref_dist + epsilon
            curr_dist = curr_dist + epsilon
            
            # Calculate KL divergence
            kl_div = entropy(curr_dist, ref_dist)
            
            return float(kl_div)
            
        except Exception as e:
            logger.error(f"KL divergence calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_wasserstein_distance(self, ref_dist: np.ndarray, curr_dist: np.ndarray) -> float:
        """Calculate Wasserstein distance"""
        try:
            from scipy.stats import wasserstein_distance
            
            # Calculate Wasserstein distance
            wasserstein_dist = wasserstein_distance(ref_dist, curr_dist)
            
            return float(wasserstein_dist)
            
        except Exception as e:
            logger.error(f"Wasserstein distance calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_ks_test(self, ref_dist: np.ndarray, curr_dist: np.ndarray) -> float:
        """Calculate Kolmogorov-Smirnov test statistic"""
        try:
            # Perform KS test
            ks_statistic, p_value = stats.ks_2samp(ref_dist, curr_dist)
            
            return float(ks_statistic)
            
        except Exception as e:
            logger.error(f"KS test calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_chi_square_test(self, ref_dist: np.ndarray, curr_dist: np.ndarray) -> float:
        """Calculate Chi-square test statistic"""
        try:
            # Perform Chi-square test
            chi2_statistic, p_value = stats.chisquare(curr_dist, ref_dist)
            
            return float(chi2_statistic)
            
        except Exception as e:
            logger.error(f"Chi-square test calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_distribution_drift(self, ref_features: np.ndarray, curr_features: np.ndarray, 
                                    metric_func) -> float:
        """Calculate distribution drift using specified metric"""
        try:
            # Calculate drift for each feature
            drift_scores = []
            
            for i in range(ref_features.shape[1]):
                ref_feature = ref_features[:, i]
                curr_feature = curr_features[:, i]
                
                # Create histograms for comparison
                ref_hist, ref_bins = np.histogram(ref_feature, bins=10, density=True)
                curr_hist, curr_bins = np.histogram(curr_feature, bins=ref_bins, density=True)
                
                # Calculate drift metric
                drift_score = metric_func(ref_hist, curr_hist)
                drift_scores.append(drift_score)
            
            # Return average drift score
            return float(np.mean(drift_scores))
            
        except Exception as e:
            logger.error(f"Distribution drift calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_feature_drift(self, ref_features: np.ndarray, curr_features: np.ndarray, 
                               metric_func) -> float:
        """Calculate feature drift using specified metric"""
        try:
            # Calculate drift for each feature
            drift_scores = []
            
            for i in range(ref_features.shape[1]):
                ref_feature = ref_features[:, i]
                curr_feature = curr_features[:, i]
                
                # Calculate drift metric
                drift_score = metric_func(ref_feature, curr_feature)
                drift_scores.append(drift_score)
            
            # Return average drift score
            return float(np.mean(drift_scores))
            
        except Exception as e:
            logger.error(f"Feature drift calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_performance_drift(self, model_record: MLModel, current_data: List[Dict[str, Any]], 
                                   config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance drift metrics"""
        try:
            # Load model
            model = pickle.loads(model_record.model_data)
            
            # Prepare current data
            X_current, y_current = self._prepare_data_for_drift(current_data, model_record.feature_columns)
            
            # Make predictions
            y_pred = model.predict(X_current)
            y_pred_proba = model.predict_proba(X_current)[:, 1] if hasattr(model, 'predict_proba') else y_pred
            
            # Calculate performance metrics
            accuracy = self._calculate_prediction_accuracy(y_current, y_pred)
            confidence = self._calculate_prediction_confidence(y_pred_proba)
            
            # Get reference performance
            reference_performance = self._get_reference_performance(model_record)
            
            # Calculate performance drift
            accuracy_drift = abs(accuracy - reference_performance.get('accuracy', 0.5))
            confidence_drift = abs(confidence - reference_performance.get('confidence', 0.5))
            
            return {
                'current_accuracy': accuracy,
                'current_confidence': confidence,
                'accuracy_drift': accuracy_drift,
                'confidence_drift': confidence_drift,
                'performance_drift_detected': accuracy_drift > 0.1 or confidence_drift > 0.1
            }
            
        except Exception as e:
            logger.error(f"Performance drift calculation failed: {str(e)}")
            return {
                'current_accuracy': 0.0,
                'current_confidence': 0.0,
                'accuracy_drift': 0.0,
                'confidence_drift': 0.0,
                'performance_drift_detected': False,
                'error': str(e)
            }
    
    def _calculate_prediction_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate prediction accuracy"""
        try:
            from sklearn.metrics import accuracy_score
            return float(accuracy_score(y_true, y_pred))
        except Exception as e:
            logger.error(f"Accuracy calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_prediction_confidence(self, y_pred_proba: np.ndarray) -> float:
        """Calculate average prediction confidence"""
        try:
            # Calculate confidence as the maximum probability for each prediction
            confidence_scores = np.maximum(y_pred_proba, 1 - y_pred_proba)
            return float(np.mean(confidence_scores))
        except Exception as e:
            logger.error(f"Confidence calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_feature_distribution_drift(self, ref_features: np.ndarray, curr_features: np.ndarray) -> float:
        """Calculate feature distribution drift"""
        try:
            # Calculate drift for each feature
            drift_scores = []
            
            for i in range(ref_features.shape[1]):
                ref_feature = ref_features[:, i]
                curr_feature = curr_features[:, i]
                
                # Calculate distribution drift using KS test
                ks_statistic, p_value = stats.ks_2samp(ref_feature, curr_feature)
                drift_scores.append(ks_statistic)
            
            return float(np.mean(drift_scores))
            
        except Exception as e:
            logger.error(f"Feature distribution drift calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_target_distribution_drift(self, ref_targets: np.ndarray, curr_targets: np.ndarray) -> float:
        """Calculate target distribution drift"""
        try:
            # Calculate target distribution drift
            ks_statistic, p_value = stats.ks_2samp(ref_targets, curr_targets)
            return float(ks_statistic)
            
        except Exception as e:
            logger.error(f"Target distribution drift calculation failed: {str(e)}")
            return 0.0
    
    def _classify_drift_severity(self, metric_name: str, drift_score: float) -> str:
        """Classify drift severity based on thresholds"""
        if drift_score is None:
            return 'error'
        
        thresholds = self.drift_thresholds.get(metric_name, {})
        
        if drift_score >= thresholds.get('high', 1.0):
            return 'high'
        elif drift_score >= thresholds.get('medium', 0.5):
            return 'medium'
        elif drift_score >= thresholds.get('low', 0.1):
            return 'low'
        else:
            return 'none'
    
    def _determine_overall_drift(self, drift_results: Dict[str, Any], performance_drift: Dict[str, Any]) -> Dict[str, Any]:
        """Determine overall drift status"""
        # Check if any metric shows high drift
        high_drift_metrics = [metric for metric, result in drift_results.items() 
                            if result.get('severity') == 'high']
        
        # Check performance drift
        performance_drift_detected = performance_drift.get('performance_drift_detected', False)
        
        # Determine overall severity
        if high_drift_metrics or performance_drift_detected:
            severity = 'high'
        elif any(result.get('severity') == 'medium' for result in drift_results.values()):
            severity = 'medium'
        elif any(result.get('severity') == 'low' for result in drift_results.values()):
            severity = 'low'
        else:
            severity = 'none'
        
        return {
            'drift_detected': severity != 'none',
            'severity': severity,
            'high_drift_metrics': high_drift_metrics,
            'performance_drift_detected': performance_drift_detected
        }
    
    def _save_drift_detection(self, model_record: MLModel, drift_results: Dict[str, Any], 
                           performance_drift: Dict[str, Any], overall_drift: Dict[str, Any]) -> ModelDrift:
        """Save drift detection results"""
        return ModelDrift.objects.create(
            model=model_record,
            drift_metrics=drift_results,
            performance_drift=performance_drift,
            overall_drift_status=overall_drift['drift_detected'],
            drift_severity=overall_drift['severity'],
            detected_at=timezone.now()
        )
    
    def _check_retraining_trigger(self, drift_record: ModelDrift, config: Dict[str, Any]) -> bool:
        """Check if model retraining should be triggered"""
        # Check drift severity
        if drift_record.drift_severity == 'high':
            return True
        
        # Check performance drift
        performance_drift = drift_record.performance_drift
        if performance_drift.get('performance_drift_detected', False):
            return True
        
        # Check if drift has been detected multiple times
        recent_drifts = ModelDrift.objects.filter(
            model=drift_record.model,
            detected_at__gte=timezone.now() - timedelta(days=7),
            overall_drift_status=True
        ).count()
        
        if recent_drifts >= config.get('max_drift_occurrences', 3):
            return True
        
        return False
    
    def _trigger_model_retraining(self, model_record: MLModel, drift_record: ModelDrift):
        """Trigger model retraining due to drift"""
        try:
            # Create drift alert
            DriftAlert.objects.create(
                model=model_record,
                drift_record=drift_record,
                alert_type='retraining_triggered',
                severity=drift_record.drift_severity,
                message=f"Model retraining triggered due to {drift_record.drift_severity} drift",
                created_at=timezone.now()
            )
            
            # Trigger retraining task
            from .ml_models import retrain_model_async
            retrain_model_async.delay(str(model_record.id), {
                'trigger_reason': 'drift_detection',
                'drift_record_id': str(drift_record.id)
            })
            
            logger.info(f"Model retraining triggered for model {model_record.id} due to drift")
            
        except Exception as e:
            logger.error(f"Failed to trigger model retraining: {str(e)}")
    
    def _get_reference_data(self, model_record: MLModel, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get reference data for drift detection"""
        # This would get historical training data
        # For now, return empty list as placeholder
        return []
    
    def _get_recent_data_for_model(self, model_record: MLModel, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recent data for drift detection"""
        # This would get recent prediction data
        # For now, return empty list as placeholder
        return []
    
    def _get_reference_performance(self, model_record: MLModel) -> Dict[str, float]:
        """Get reference performance metrics"""
        # This would get historical performance metrics
        # For now, return default values
        return {
            'accuracy': 0.8,
            'confidence': 0.7
        }
    
    def _prepare_data_for_drift(self, data: List[Dict[str, Any]], feature_columns: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for drift detection"""
        if not data:
            return np.array([]), np.array([])
        
        features = []
        targets = []
        
        for record in data:
            feature_vector = []
            for col in feature_columns:
                value = record.get(col, 0)
                if isinstance(value, str):
                    value = hash(value) % 1000
                feature_vector.append(float(value))
            
            features.append(feature_vector)
            targets.append(record.get('target', 0))
        
        return np.array(features), np.array(targets)

# Celery tasks
@shared_task
def run_daily_drift_detection(company_id: str, job_config: Dict[str, Any]):
    """Daily drift detection job"""
    engine = DriftDetectionEngine()
    return engine.run_daily_drift_job(company_id, job_config)

@shared_task
def detect_model_drift_async(model_id: str, current_data: List[Dict[str, Any]], drift_config: Dict[str, Any]):
    """Async drift detection for specific model"""
    engine = DriftDetectionEngine()
    return engine.detect_drift(model_id, current_data, drift_config)

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detect_drift(request):
    """API endpoint to detect drift"""
    engine = DriftDetectionEngine()
    result = engine.detect_drift(
        request.data.get('model_id'),
        request.data.get('current_data', []),
        request.data.get('drift_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_daily_drift_job(request):
    """API endpoint to run daily drift job"""
    engine = DriftDetectionEngine()
    result = engine.run_daily_drift_job(
        str(request.user.company.id),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)
