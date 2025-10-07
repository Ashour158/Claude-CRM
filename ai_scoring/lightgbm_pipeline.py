# ai_scoring/lightgbm_pipeline.py
# Production LightGBM Pipeline with AUC Gating and Metrics Validation

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
import lightgbm as lgb
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import roc_auc_score, precision_recall_curve, roc_curve
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib
import pickle
from celery import shared_task

from .models import (
    MLModel, ModelTraining, ModelPrediction, ModelDrift,
    FeatureImportance, ModelPerformance, ModelRetraining,
    LightGBMModel, AUCValidation, ModelMetrics
)
from core.models import User, Company
from crm.models import Lead, Deal, Account

logger = logging.getLogger(__name__)

class LightGBMPipeline:
    """
    Production LightGBM pipeline with AUC gating, metrics validation,
    and advanced model management.
    """
    
    def __init__(self):
        self.lightgbm_params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': 0,
            'random_state': 42
        }
        
        self.validation_metrics = {
            'auc': roc_auc_score,
            'precision_recall': precision_recall_curve,
            'roc_curve': roc_curve
        }
        
        self.auc_thresholds = {
            'minimum': 0.65,
            'good': 0.75,
            'excellent': 0.85
        }
    
    def train_lightgbm_model(self, company_id: str, training_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Train LightGBM model with comprehensive validation and AUC gating.
        """
        try:
            company = Company.objects.get(id=company_id)
            
            # Prepare training data
            training_data = self._prepare_training_data(company, training_config)
            
            if len(training_data) < 1000:  # Minimum data requirement for LightGBM
                return {
                    'status': 'error',
                    'error': 'Insufficient training data (minimum 1000 records required for LightGBM)'
                }
            
            # Feature engineering
            X, y, feature_names = self._engineer_features(training_data, training_config)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Cross-validation setup
            cv_scores = self._perform_cross_validation(X_train, y_train, training_config)
            
            # Train final model
            model = self._train_final_model(X_train, y_train, X_test, y_test, training_config)
            
            # Comprehensive validation
            validation_results = self._comprehensive_validation(model, X_test, y_test)
            
            # AUC gating
            auc_gate_result = self._apply_auc_gating(validation_results['auc'])
            
            if not auc_gate_result['passed']:
                return {
                    'status': 'rejected',
                    'reason': 'AUC gating failed',
                    'auc_score': validation_results['auc'],
                    'threshold': auc_gate_result['threshold'],
                    'recommendations': auc_gate_result['recommendations']
                }
            
            # Save model
            model_id = self._save_lightgbm_model(company, model, feature_names, validation_results, training_config)
            
            # Create training record
            training_record = ModelTraining.objects.create(
                company=company,
                model_id=model_id,
                training_data_size=len(training_data),
                model_type='lightgbm',
                hyperparameters=self.lightgbm_params,
                performance_metrics=validation_results,
                auc_score=validation_results['auc'],
                cv_scores=cv_scores,
                status='completed',
                trained_by=User.objects.filter(company=company).first()
            )
            
            # Calculate and save feature importance
            self._save_feature_importance(model, feature_names, training_record)
            
            # Create AUC validation record
            AUCValidation.objects.create(
                training=training_record,
                auc_score=validation_results['auc'],
                threshold_used=auc_gate_result['threshold'],
                passed_gating=auc_gate_result['passed'],
                validation_timestamp=timezone.now()
            )
            
            return {
                'status': 'success',
                'model_id': model_id,
                'training_id': str(training_record.id),
                'auc_score': validation_results['auc'],
                'cv_scores': cv_scores,
                'feature_count': len(feature_names),
                'gating_result': auc_gate_result
            }
            
        except Exception as e:
            logger.error(f"LightGBM training failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def predict_with_lightgbm(self, model_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make prediction using trained LightGBM model.
        """
        try:
            model_record = LightGBMModel.objects.get(id=model_id)
            
            # Load model
            model = pickle.loads(model_record.model_data)
            
            # Prepare features
            feature_vector = self._prepare_prediction_features(features, model_record.feature_columns)
            
            # Make prediction
            prediction_proba = model.predict_proba([feature_vector])[0]
            prediction_class = model.predict([feature_vector])[0]
            
            # Calculate confidence
            confidence = max(prediction_proba)
            
            # Get feature importance for this prediction
            feature_importance = self._get_prediction_feature_importance(model, feature_vector, model_record.feature_columns)
            
            return {
                'status': 'success',
                'prediction': int(prediction_class),
                'probability': float(prediction_proba[1]),  # Probability of positive class
                'confidence': float(confidence),
                'feature_importance': feature_importance,
                'model_version': model_record.version
            }
            
        except Exception as e:
            logger.error(f"LightGBM prediction failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate_model_performance(self, model_id: str, validation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate model performance on new data with AUC gating.
        """
        try:
            model_record = LightGBMModel.objects.get(id=model_id)
            model = pickle.loads(model_record.model_data)
            
            # Prepare validation data
            X_val, y_val = self._prepare_validation_data(validation_data, model_record.feature_columns)
            
            # Make predictions
            y_pred_proba = model.predict_proba(X_val)[:, 1]
            y_pred = model.predict(X_val)
            
            # Calculate metrics
            auc_score = roc_auc_score(y_val, y_pred_proba)
            precision, recall, pr_thresholds = precision_recall_curve(y_val, y_pred_proba)
            fpr, tpr, roc_thresholds = roc_curve(y_val, y_pred_proba)
            
            # Apply AUC gating
            auc_gate_result = self._apply_auc_gating(auc_score)
            
            # Create validation record
            validation_record = ModelMetrics.objects.create(
                model=model_record,
                auc_score=auc_score,
                precision_scores=precision.tolist(),
                recall_scores=recall.tolist(),
                fpr_scores=fpr.tolist(),
                tpr_scores=tpr.tolist(),
                validation_timestamp=timezone.now(),
                passed_auc_gating=auc_gate_result['passed']
            )
            
            return {
                'status': 'success',
                'auc_score': auc_score,
                'auc_gating': auc_gate_result,
                'validation_id': str(validation_record.id),
                'metrics': {
                    'auc': auc_score,
                    'precision': precision.tolist(),
                    'recall': recall.tolist(),
                    'fpr': fpr.tolist(),
                    'tpr': tpr.tolist()
                }
            }
            
        except Exception as e:
            logger.error(f"Model validation failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _prepare_training_data(self, company: Company, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare comprehensive training data for LightGBM"""
        # Get leads with outcomes
        leads = Lead.objects.filter(
            company=company,
            status__in=['converted', 'disqualified', 'nurturing', 'qualified']
        ).select_related('account', 'assigned_to')
        
        training_data = []
        
        for lead in leads:
            features = {}
            
            # Lead features
            features.update(self._extract_lead_features(lead))
            
            # Company features
            if lead.account:
                features.update(self._extract_company_features(lead.account))
            
            # Behavioral features
            features.update(self._extract_behavioral_features(lead))
            
            # Temporal features
            features.update(self._extract_temporal_features(lead))
            
            # Interaction features
            features.update(self._extract_interaction_features(lead))
            
            # Target variable
            features['target'] = 1 if lead.status == 'converted' else 0
            
            training_data.append(features)
        
        return training_data
    
    def _engineer_features(self, training_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Engineer features for LightGBM"""
        df = pd.DataFrame(training_data)
        
        # Separate target
        y = df['target'].values
        X = df.drop('target', axis=1)
        
        # Handle missing values
        X = X.fillna(0)
        
        # Encode categorical variables
        categorical_columns = X.select_dtypes(include=['object']).columns
        label_encoders = {}
        
        for col in categorical_columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le
        
        # Feature selection (optional)
        if config.get('feature_selection', False):
            X = self._select_features(X, y, config.get('max_features', 50))
        
        return X.values, y, list(X.columns)
    
    def _perform_cross_validation(self, X: np.ndarray, y: np.ndarray, config: Dict[str, Any]) -> Dict[str, float]:
        """Perform cross-validation"""
        cv_scores = []
        kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        for train_idx, val_idx in kfold.split(X, y):
            X_train_fold, X_val_fold = X[train_idx], X[val_idx]
            y_train_fold, y_val_fold = y[train_idx], y[val_idx]
            
            # Train model
            train_data = lgb.Dataset(X_train_fold, label=y_train_fold)
            val_data = lgb.Dataset(X_val_fold, label=y_val_fold, reference=train_data)
            
            model = lgb.train(
                self.lightgbm_params,
                train_data,
                valid_sets=[val_data],
                num_boost_round=1000,
                callbacks=[lgb.early_stopping(100), lgb.log_evaluation(0)]
            )
            
            # Predict and score
            y_pred_proba = model.predict(X_val_fold)
            auc_score = roc_auc_score(y_val_fold, y_pred_proba)
            cv_scores.append(auc_score)
        
        return {
            'mean_auc': np.mean(cv_scores),
            'std_auc': np.std(cv_scores),
            'cv_scores': cv_scores
        }
    
    def _train_final_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                         X_test: np.ndarray, y_test: np.ndarray, config: Dict[str, Any]) -> lgb.Booster:
        """Train final LightGBM model"""
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        model = lgb.train(
            self.lightgbm_params,
            train_data,
            valid_sets=[test_data],
            num_boost_round=config.get('num_boost_round', 1000),
            callbacks=[lgb.early_stopping(100), lgb.log_evaluation(0)]
        )
        
        return model
    
    def _comprehensive_validation(self, model: lgb.Booster, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Comprehensive model validation"""
        # Predictions
        y_pred_proba = model.predict(X_test)
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # Calculate metrics
        auc_score = roc_auc_score(y_test, y_pred_proba)
        precision, recall, pr_thresholds = precision_recall_curve(y_test, y_pred_proba)
        fpr, tpr, roc_thresholds = roc_curve(y_test, y_pred_proba)
        
        # Feature importance
        feature_importance = model.feature_importance(importance_type='gain')
        
        return {
            'auc': auc_score,
            'precision': precision,
            'recall': recall,
            'fpr': fpr,
            'tpr': tpr,
            'feature_importance': feature_importance.tolist(),
            'predictions': y_pred.tolist(),
            'probabilities': y_pred_proba.tolist()
        }
    
    def _apply_auc_gating(self, auc_score: float) -> Dict[str, Any]:
        """Apply AUC gating with recommendations"""
        if auc_score >= self.auc_thresholds['excellent']:
            return {
                'passed': True,
                'threshold': self.auc_thresholds['excellent'],
                'level': 'excellent',
                'recommendations': ['Model ready for production deployment']
            }
        elif auc_score >= self.auc_thresholds['good']:
            return {
                'passed': True,
                'threshold': self.auc_thresholds['good'],
                'level': 'good',
                'recommendations': ['Model acceptable for production', 'Consider additional feature engineering']
            }
        elif auc_score >= self.auc_thresholds['minimum']:
            return {
                'passed': True,
                'threshold': self.auc_thresholds['minimum'],
                'level': 'minimum',
                'recommendations': ['Model meets minimum requirements', 'Strongly recommend feature engineering', 'Consider data quality improvements']
            }
        else:
            return {
                'passed': False,
                'threshold': self.auc_thresholds['minimum'],
                'level': 'insufficient',
                'recommendations': [
                    'Model does not meet minimum AUC requirements',
                    'Review feature engineering pipeline',
                    'Check data quality and completeness',
                    'Consider different algorithms or hyperparameters',
                    'Increase training data size'
                ]
            }
    
    def _save_lightgbm_model(self, company: Company, model: lgb.Booster, 
                           feature_names: List[str], validation_results: Dict[str, Any], 
                           config: Dict[str, Any]) -> str:
        """Save LightGBM model with metadata"""
        # Serialize model
        model_data = pickle.dumps(model)
        
        # Create model record
        model_record = LightGBMModel.objects.create(
            company=company,
            model_name=config.get('model_name', 'LightGBM Lead Scoring'),
            model_data=model_data,
            feature_columns=feature_names,
            hyperparameters=self.lightgbm_params,
            performance_metrics=validation_results,
            auc_score=validation_results['auc'],
            training_data_size=config.get('training_size', 0),
            is_active=True,
            version=1,
            created_by=User.objects.filter(company=company).first()
        )
        
        return str(model_record.id)
    
    def _save_feature_importance(self, model: lgb.Booster, feature_names: List[str], training_record: ModelTraining):
        """Save feature importance"""
        importance_scores = model.feature_importance(importance_type='gain')
        
        for i, (feature_name, importance) in enumerate(zip(feature_names, importance_scores)):
            FeatureImportance.objects.create(
                training=training_record,
                feature_name=feature_name,
                importance_score=float(importance),
                rank=i + 1
            )
    
    def _prepare_prediction_features(self, features: Dict[str, Any], feature_columns: List[str]) -> List[float]:
        """Prepare features for prediction"""
        feature_vector = []
        
        for col in feature_columns:
            value = features.get(col, 0)
            
            # Handle different data types
            if isinstance(value, str):
                # Simple hash encoding for categorical
                value = hash(value) % 1000
            
            feature_vector.append(float(value))
        
        return feature_vector
    
    def _get_prediction_feature_importance(self, model: lgb.Booster, feature_vector: List[float], 
                                         feature_columns: List[str]) -> Dict[str, float]:
        """Get feature importance for specific prediction"""
        importance_scores = model.feature_importance(importance_type='gain')
        
        feature_importance = {}
        for i, (feature_name, importance) in enumerate(zip(feature_columns, importance_scores)):
            feature_importance[feature_name] = float(importance)
        
        # Sort by importance
        sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        
        return sorted_importance
    
    def _prepare_validation_data(self, validation_data: List[Dict[str, Any]], feature_columns: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare validation data"""
        X_val = []
        y_val = []
        
        for record in validation_data:
            features = self._prepare_prediction_features(record, feature_columns)
            X_val.append(features)
            y_val.append(record.get('target', 0))
        
        return np.array(X_val), np.array(y_val)
    
    def _extract_lead_features(self, lead: Lead) -> Dict[str, Any]:
        """Extract lead features"""
        return {
            'lead_source': lead.source or 'unknown',
            'lead_status': lead.status or 'new',
            'lead_priority': lead.priority or 'medium',
            'lead_score': lead.score or 0,
            'lead_age_days': (timezone.now() - lead.created_at).days,
            'has_email': 1 if lead.email else 0,
            'has_phone': 1 if lead.phone else 0,
            'has_company': 1 if lead.company_name else 0,
            'email_domain_type': self._get_email_domain_type(lead.email),
            'phone_country_code': self._get_phone_country_code(lead.phone),
            'lead_notes_length': len(lead.notes) if lead.notes else 0,
            'lead_tags_count': len(lead.tags) if lead.tags else 0
        }
    
    def _extract_company_features(self, account: Account) -> Dict[str, Any]:
        """Extract company features"""
        return {
            'company_size': account.company_size or 'unknown',
            'company_industry': account.industry or 'unknown',
            'company_type': account.account_type or 'unknown',
            'company_revenue': float(account.annual_revenue) if account.annual_revenue else 0,
            'company_employees': account.employee_count or 0,
            'company_website': 1 if account.website else 0,
            'company_linkedin': 1 if account.linkedin_url else 0,
            'company_created_days': (timezone.now() - account.created_at).days,
            'company_has_deals': 1 if account.deals.exists() else 0,
            'company_deals_count': account.deals.count(),
            'company_deals_value': sum(deal.amount for deal in account.deals.all() if deal.amount)
        }
    
    def _extract_behavioral_features(self, lead: Lead) -> Dict[str, Any]:
        """Extract behavioral features"""
        # Email interactions
        email_opens = 0  # Would come from email tracking
        email_clicks = 0  # Would come from email tracking
        
        # Website interactions
        page_views = 0  # Would come from website analytics
        time_on_site = 0  # Would come from website analytics
        
        return {
            'email_opens': email_opens,
            'email_clicks': email_clicks,
            'email_click_rate': email_clicks / max(email_opens, 1),
            'page_views': page_views,
            'time_on_site': time_on_site,
            'engagement_score': (email_opens + email_clicks + page_views) / 3
        }
    
    def _extract_temporal_features(self, lead: Lead) -> Dict[str, Any]:
        """Extract temporal features"""
        now = timezone.now()
        created_at = lead.created_at
        
        return {
            'created_hour': created_at.hour,
            'created_day_of_week': created_at.weekday(),
            'created_month': created_at.month,
            'created_quarter': (created_at.month - 1) // 3 + 1,
            'is_weekend': 1 if created_at.weekday() >= 5 else 0,
            'is_business_hours': 1 if 9 <= created_at.hour <= 17 else 0,
            'days_since_created': (now - created_at).days,
            'weeks_since_created': (now - created_at).days // 7,
            'months_since_created': (now - created_at).days // 30
        }
    
    def _extract_interaction_features(self, lead: Lead) -> Dict[str, Any]:
        """Extract interaction features"""
        # Count interactions
        activities_count = 0  # Would count activities
        emails_sent = 0  # Would count emails
        calls_made = 0  # Would count calls
        
        return {
            'activities_count': activities_count,
            'emails_sent': emails_sent,
            'calls_made': calls_made,
            'total_interactions': activities_count + emails_sent + calls_made
        }
    
    def _get_email_domain_type(self, email: str) -> int:
        """Get email domain type"""
        if not email or '@' not in email:
            return 0
        
        domain = email.split('@')[1].lower()
        
        # Business domains
        business_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        if domain in business_domains:
            return 1  # Personal email
        else:
            return 2  # Business email
    
    def _get_phone_country_code(self, phone: str) -> int:
        """Get phone country code"""
        if not phone:
            return 0
        
        # Extract country code (simplified)
        if phone.startswith('+1'):
            return 1  # US
        elif phone.startswith('+44'):
            return 44  # UK
        elif phone.startswith('+49'):
            return 49  # Germany
        else:
            return 999  # Other
    
    def _select_features(self, X: pd.DataFrame, y: np.ndarray, max_features: int) -> pd.DataFrame:
        """Select best features"""
        from sklearn.feature_selection import SelectKBest, f_classif
        
        selector = SelectKBest(score_func=f_classif, k=min(max_features, X.shape[1]))
        X_selected = selector.fit_transform(X, y)
        
        # Get selected feature names
        selected_features = X.columns[selector.get_support()].tolist()
        
        return X[selected_features]

# Celery tasks
@shared_task
def train_lightgbm_model_async(company_id: str, training_config: Dict[str, Any]):
    """Async task to train LightGBM model"""
    pipeline = LightGBMPipeline()
    return pipeline.train_lightgbm_model(company_id, training_config)

@shared_task
def validate_model_performance_async(model_id: str, validation_data: List[Dict[str, Any]]):
    """Async task to validate model performance"""
    pipeline = LightGBMPipeline()
    return pipeline.validate_model_performance(model_id, validation_data)

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_lightgbm_model(request):
    """API endpoint to train LightGBM model"""
    pipeline = LightGBMPipeline()
    result = pipeline.train_lightgbm_model(
        str(request.user.company.id),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_with_lightgbm(request):
    """API endpoint to make LightGBM prediction"""
    pipeline = LightGBMPipeline()
    result = pipeline.predict_with_lightgbm(
        request.data.get('model_id'),
        request.data.get('features', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_model_performance(request):
    """API endpoint to validate model performance"""
    pipeline = LightGBMPipeline()
    result = pipeline.validate_model_performance(
        request.data.get('model_id'),
        request.data.get('validation_data', [])
    )
    return Response(result, status=status.HTTP_200_OK)
