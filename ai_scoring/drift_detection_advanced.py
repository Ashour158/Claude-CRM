# ai_scoring/drift_detection_advanced.py
"""
Advanced Drift Detection & Retrain Trigger
P0 Priority: Retrain <24h from drift

This module implements:
- Real-time drift detection using PSI/KL divergence
- Automated retrain triggers
- Model performance monitoring
- Drift severity classification
- Retrain scheduling and execution
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from core.models import Company, User
from events.event_bus import event_bus
import uuid
import json
from scipy import stats
from sklearn.metrics import roc_auc_score

logger = logging.getLogger(__name__)

@dataclass
class DriftDetectionResult:
    """Drift detection result"""
    id: str
    timestamp: timezone.datetime
    model_name: str
    drift_detected: bool
    drift_score: float
    drift_severity: str
    affected_features: List[str]
    confidence_level: float
    recommended_action: str
    retrain_required: bool
    estimated_retrain_time: int  # minutes

@dataclass
class RetrainTrigger:
    """Retrain trigger configuration"""
    model_name: str
    trigger_type: str
    threshold: float
    cooldown_hours: int
    last_triggered: Optional[timezone.datetime]
    is_active: bool

class AdvancedDriftDetection:
    """
    Advanced drift detection with automated retrain triggers
    """
    
    def __init__(self):
        self.drift_results: List[DriftDetectionResult] = []
        self.retrain_triggers: Dict[str, RetrainTrigger] = {}
        self.model_baselines: Dict[str, Dict[str, Any]] = {}
        self.drift_thresholds = {
            "low": 0.1,
            "medium": 0.2,
            "high": 0.3,
            "critical": 0.5
        }
        
    def setup_retrain_trigger(self, model_name: str, trigger_type: str,
                            threshold: float, cooldown_hours: int = 24) -> RetrainTrigger:
        """Setup automated retrain trigger for a model"""
        trigger = RetrainTrigger(
            model_name=model_name,
            trigger_type=trigger_type,
            threshold=threshold,
            cooldown_hours=cooldown_hours,
            last_triggered=None,
            is_active=True
        )
        
        self.retrain_triggers[model_name] = trigger
        
        logger.info(f"Retrain trigger setup for {model_name}: {trigger_type} > {threshold}")
        return trigger
    
    def detect_drift(self, model_name: str, current_data: pd.DataFrame,
                    reference_data: pd.DataFrame, company: Company) -> DriftDetectionResult:
        """Detect drift between current and reference data"""
        
        # Calculate PSI (Population Stability Index)
        psi_scores = self._calculate_psi_scores(current_data, reference_data)
        
        # Calculate KL divergence
        kl_scores = self._calculate_kl_divergence(current_data, reference_data)
        
        # Calculate feature drift scores
        feature_drifts = self._calculate_feature_drift(current_data, reference_data)
        
        # Determine overall drift score
        max_psi = max(psi_scores.values()) if psi_scores else 0
        max_kl = max(kl_scores.values()) if kl_scores else 0
        max_feature_drift = max(feature_drifts.values()) if feature_drifts else 0
        
        overall_drift_score = max(max_psi, max_kl, max_feature_drift)
        
        # Determine drift severity
        drift_severity = self._classify_drift_severity(overall_drift_score)
        
        # Identify affected features
        affected_features = self._identify_affected_features(psi_scores, kl_scores, feature_drifts)
        
        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(overall_drift_score, len(current_data))
        
        # Determine if retrain is required
        retrain_required = overall_drift_score > self.drift_thresholds["medium"]
        
        # Estimate retrain time
        estimated_retrain_time = self._estimate_retrain_time(model_name, len(current_data))
        
        # Create drift detection result
        result = DriftDetectionResult(
            id=str(uuid.uuid4()),
            timestamp=timezone.now(),
            model_name=model_name,
            drift_detected=overall_drift_score > self.drift_thresholds["low"],
            drift_score=overall_drift_score,
            drift_severity=drift_severity,
            affected_features=affected_features,
            confidence_level=confidence_level,
            recommended_action=self._get_recommended_action(drift_severity),
            retrain_required=retrain_required,
            estimated_retrain_time=estimated_retrain_time
        )
        
        self.drift_results.append(result)
        
        # Publish drift detection event
        event_bus.publish(
            event_type='DRIFT_DETECTED',
            data={
                'drift_id': result.id,
                'model_name': model_name,
                'drift_score': overall_drift_score,
                'drift_severity': drift_severity,
                'retrain_required': retrain_required,
                'affected_features': affected_features
            },
            company_id=company.id
        )
        
        # Check if retrain trigger should be activated
        if retrain_required:
            self._check_retrain_trigger(model_name, result)
        
        logger.info(f"Drift detection completed for {model_name}: {drift_severity} (score: {overall_drift_score:.3f})")
        return result
    
    def _calculate_psi_scores(self, current_data: pd.DataFrame, 
                             reference_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate PSI scores for each feature"""
        psi_scores = {}
        
        for column in current_data.columns:
            if column in reference_data.columns:
                try:
                    # Create bins for PSI calculation
                    combined_data = pd.concat([reference_data[column], current_data[column]])
                    bins = pd.qcut(combined_data, q=10, duplicates='drop')
                    
                    # Calculate PSI
                    psi_score = self._calculate_psi(
                        reference_data[column], current_data[column], bins
                    )
                    psi_scores[column] = psi_score
                except Exception as e:
                    logger.warning(f"Failed to calculate PSI for {column}: {e}")
                    psi_scores[column] = 0
        
        return psi_scores
    
    def _calculate_psi(self, reference: pd.Series, current: pd.Series, bins) -> float:
        """Calculate Population Stability Index"""
        try:
            # Bin the data
            ref_binned = pd.cut(reference, bins=bins.cat.categories, include_lowest=True)
            curr_binned = pd.cut(current, bins=bins.cat.categories, include_lowest=True)
            
            # Calculate distributions
            ref_dist = ref_binned.value_counts(normalize=True)
            curr_dist = curr_binned.value_counts(normalize=True)
            
            # Align distributions
            all_categories = set(ref_dist.index) | set(curr_dist.index)
            ref_dist = ref_dist.reindex(all_categories, fill_value=0)
            curr_dist = curr_dist.reindex(all_categories, fill_value=0)
            
            # Calculate PSI
            psi = 0
            for cat in all_categories:
                if ref_dist[cat] > 0 and curr_dist[cat] > 0:
                    psi += (curr_dist[cat] - ref_dist[cat]) * np.log(curr_dist[cat] / ref_dist[cat])
            
            return psi
        except Exception as e:
            logger.warning(f"PSI calculation failed: {e}")
            return 0
    
    def _calculate_kl_divergence(self, current_data: pd.DataFrame, 
                                reference_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate KL divergence for each feature"""
        kl_scores = {}
        
        for column in current_data.columns:
            if column in reference_data.columns:
                try:
                    # Get distributions
                    ref_values = reference_data[column].dropna()
                    curr_values = current_data[column].dropna()
                    
                    if len(ref_values) > 0 and len(curr_values) > 0:
                        # Calculate KL divergence
                        kl_score = self._calculate_kl_divergence_single(ref_values, curr_values)
                        kl_scores[column] = kl_score
                except Exception as e:
                    logger.warning(f"Failed to calculate KL divergence for {column}: {e}")
                    kl_scores[column] = 0
        
        return kl_scores
    
    def _calculate_kl_divergence_single(self, ref_values: pd.Series, 
                                      curr_values: pd.Series) -> float:
        """Calculate KL divergence between two distributions"""
        try:
            # Create histograms
            combined = pd.concat([ref_values, curr_values])
            bins = np.histogram_bin_edges(combined, bins=20)
            
            ref_hist, _ = np.histogram(ref_values, bins=bins, density=True)
            curr_hist, _ = np.histogram(curr_values, bins=bins, density=True)
            
            # Add small epsilon to avoid log(0)
            epsilon = 1e-10
            ref_hist = ref_hist + epsilon
            curr_hist = curr_hist + epsilon
            
            # Normalize
            ref_hist = ref_hist / np.sum(ref_hist)
            curr_hist = curr_hist / np.sum(curr_hist)
            
            # Calculate KL divergence
            kl_div = np.sum(curr_hist * np.log(curr_hist / ref_hist))
            return kl_div
        except Exception as e:
            logger.warning(f"KL divergence calculation failed: {e}")
            return 0
    
    def _calculate_feature_drift(self, current_data: pd.DataFrame, 
                                reference_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate feature-level drift scores"""
        drift_scores = {}
        
        for column in current_data.columns:
            if column in reference_data.columns:
                try:
                    ref_values = reference_data[column].dropna()
                    curr_values = current_data[column].dropna()
                    
                    if len(ref_values) > 10 and len(curr_values) > 10:
                        # Statistical tests for drift
                        if ref_values.dtype in ['int64', 'float64']:
                            # Kolmogorov-Smirnov test
                            ks_stat, ks_pvalue = stats.ks_2samp(ref_values, curr_values)
                            drift_scores[column] = ks_stat
                        else:
                            # Chi-square test for categorical
                            ref_counts = ref_values.value_counts()
                            curr_counts = curr_values.value_counts()
                            
                            # Align categories
                            all_categories = set(ref_counts.index) | set(curr_counts.index)
                            ref_counts = ref_counts.reindex(all_categories, fill_value=0)
                            curr_counts = curr_counts.reindex(all_categories, fill_value=0)
                            
                            chi2_stat, chi2_pvalue = stats.chisquare(curr_counts, ref_counts)
                            drift_scores[column] = chi2_stat / len(curr_values) if len(curr_values) > 0 else 0
                except Exception as e:
                    logger.warning(f"Feature drift calculation failed for {column}: {e}")
                    drift_scores[column] = 0
        
        return drift_scores
    
    def _classify_drift_severity(self, drift_score: float) -> str:
        """Classify drift severity based on score"""
        if drift_score >= self.drift_thresholds["critical"]:
            return "critical"
        elif drift_score >= self.drift_thresholds["high"]:
            return "high"
        elif drift_score >= self.drift_thresholds["medium"]:
            return "medium"
        elif drift_score >= self.drift_thresholds["low"]:
            return "low"
        else:
            return "none"
    
    def _identify_affected_features(self, psi_scores: Dict[str, float],
                                  kl_scores: Dict[str, float],
                                  feature_drifts: Dict[str, float]) -> List[str]:
        """Identify features most affected by drift"""
        all_features = set(psi_scores.keys()) | set(kl_scores.keys()) | set(feature_drifts.keys())
        
        feature_scores = {}
        for feature in all_features:
            scores = []
            if feature in psi_scores:
                scores.append(psi_scores[feature])
            if feature in kl_scores:
                scores.append(kl_scores[feature])
            if feature in feature_drifts:
                scores.append(feature_drifts[feature])
            
            if scores:
                feature_scores[feature] = max(scores)
        
        # Sort by drift score and return top affected features
        sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
        return [feature for feature, score in sorted_features[:5]]  # Top 5 affected features
    
    def _calculate_confidence_level(self, drift_score: float, sample_size: int) -> float:
        """Calculate confidence level for drift detection"""
        # Base confidence on drift score and sample size
        base_confidence = min(0.95, 0.5 + (drift_score * 0.5))
        sample_confidence = min(0.1, sample_size / 10000)  # Sample size bonus
        
        return min(0.99, base_confidence + sample_confidence)
    
    def _get_recommended_action(self, drift_severity: str) -> str:
        """Get recommended action based on drift severity"""
        actions = {
            "none": "No action required",
            "low": "Monitor closely, consider data quality checks",
            "medium": "Retrain model with recent data",
            "high": "Immediate retrain required, investigate data sources",
            "critical": "Emergency retrain, full model audit required"
        }
        return actions.get(drift_severity, "Unknown severity")
    
    def _estimate_retrain_time(self, model_name: str, data_size: int) -> int:
        """Estimate retrain time in minutes"""
        # Base time estimates (in minutes)
        base_times = {
            "lightgbm": 30,
            "xgboost": 45,
            "neural_network": 120,
            "ensemble": 90
        }
        
        base_time = base_times.get(model_name.lower(), 60)
        
        # Scale by data size
        size_factor = min(3.0, max(0.5, data_size / 10000))
        
        return int(base_time * size_factor)
    
    def _check_retrain_trigger(self, model_name: str, drift_result: DriftDetectionResult):
        """Check if retrain trigger should be activated"""
        if model_name not in self.retrain_triggers:
            return
        
        trigger = self.retrain_triggers[model_name]
        
        # Check cooldown period
        if trigger.last_triggered:
            time_since_last = timezone.now() - trigger.last_triggered
            if time_since_last.total_seconds() < trigger.cooldown_hours * 3600:
                logger.info(f"Retrain trigger for {model_name} in cooldown period")
                return
        
        # Check if threshold is met
        if drift_result.drift_score > trigger.threshold:
            self._activate_retrain_trigger(model_name, drift_result)
    
    def _activate_retrain_trigger(self, model_name: str, drift_result: DriftDetectionResult):
        """Activate retrain trigger"""
        trigger = self.retrain_triggers[model_name]
        trigger.last_triggered = timezone.now()
        
        # Publish retrain trigger event
        event_bus.publish(
            event_type='RETRAIN_TRIGGER_ACTIVATED',
            data={
                'model_name': model_name,
                'trigger_type': trigger.trigger_type,
                'drift_score': drift_result.drift_score,
                'drift_severity': drift_result.drift_severity,
                'estimated_retrain_time': drift_result.estimated_retrain_time,
                'affected_features': drift_result.affected_features
            }
        )
        
        # Schedule retrain
        self._schedule_retrain(model_name, drift_result)
        
        logger.warning(f"Retrain trigger activated for {model_name}: {drift_result.drift_severity} drift detected")
    
    def _schedule_retrain(self, model_name: str, drift_result: DriftDetectionResult):
        """Schedule model retraining"""
        # This would typically integrate with a task queue (Celery)
        # For now, we'll log the retrain request
        
        retrain_data = {
            "model_name": model_name,
            "drift_score": drift_result.drift_score,
            "drift_severity": drift_result.drift_severity,
            "affected_features": drift_result.affected_features,
            "estimated_time": drift_result.estimated_retrain_time,
            "scheduled_at": timezone.now().isoformat(),
            "priority": "high" if drift_result.drift_severity in ["high", "critical"] else "medium"
        }
        
        logger.info(f"Retrain scheduled for {model_name}: {retrain_data}")
        
        # In a real implementation, this would:
        # 1. Add retrain task to Celery queue
        # 2. Set up monitoring for retrain progress
        # 3. Configure retrain parameters based on drift severity
        # 4. Set up validation after retrain completion
    
    def get_drift_summary(self, model_name: str, 
                         lookback_days: int = 7) -> Dict[str, Any]:
        """Get drift detection summary for a model"""
        cutoff_date = timezone.now() - timedelta(days=lookback_days)
        model_drifts = [
            drift for drift in self.drift_results
            if drift.model_name == model_name and drift.timestamp >= cutoff_date
        ]
        
        if not model_drifts:
            return {"status": "no_data", "message": "No drift data available"}
        
        # Calculate summary statistics
        drift_scores = [drift.drift_score for drift in model_drifts]
        severity_counts = {}
        for drift in model_drifts:
            severity_counts[drift.severity] = severity_counts.get(drift.severity, 0) + 1
        
        return {
            "model_name": model_name,
            "period_days": lookback_days,
            "total_detections": len(model_drifts),
            "average_drift_score": np.mean(drift_scores),
            "max_drift_score": np.max(drift_scores),
            "severity_distribution": severity_counts,
            "retrain_triggers": sum(1 for drift in model_drifts if drift.retrain_required),
            "last_drift": model_drifts[-1].timestamp.isoformat() if model_drifts else None,
            "drift_trend": "increasing" if len(drift_scores) > 1 and drift_scores[-1] > drift_scores[0] else "stable"
        }
    
    def get_retrain_status(self, model_name: str) -> Dict[str, Any]:
        """Get retrain status for a model"""
        if model_name not in self.retrain_triggers:
            return {"status": "no_trigger", "message": "No retrain trigger configured"}
        
        trigger = self.retrain_triggers[model_name]
        
        # Get recent drift results
        recent_drifts = [
            drift for drift in self.drift_results
            if drift.model_name == model_name and drift.timestamp >= timezone.now() - timedelta(hours=24)
        ]
        
        return {
            "model_name": model_name,
            "trigger_active": trigger.is_active,
            "trigger_type": trigger.trigger_type,
            "threshold": trigger.threshold,
            "last_triggered": trigger.last_triggered.isoformat() if trigger.last_triggered else None,
            "cooldown_hours": trigger.cooldown_hours,
            "recent_drifts_24h": len(recent_drifts),
            "max_drift_score_24h": max([d.drift_score for d in recent_drifts]) if recent_drifts else 0,
            "next_available": (trigger.last_triggered + timedelta(hours=trigger.cooldown_hours)).isoformat() if trigger.last_triggered else None
        }

# Global instance
advanced_drift_detection = AdvancedDriftDetection()
