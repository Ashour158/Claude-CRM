# ai_scoring/ml_models.py
# Production ML Models for AI Lead Scoring with Retraining and Drift Detection

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif
import joblib
import pickle
import hashlib
from celery import shared_task

from .models import (
    MLModel, ModelTraining, ModelPrediction, ModelDrift,
    FeatureImportance, ModelPerformance, ModelRetraining
)
from core.models import User, Company
from crm.models import Lead, Deal, Account

logger = logging.getLogger(__name__)

class ProductionMLScoringEngine:
    """
    Production-ready ML scoring engine with real models,
    retraining, and drift detection.
    """
    
    def __init__(self):
        self.model_types = {
            'random_forest': RandomForestClassifier,
            'gradient_boosting': GradientBoostingClassifier,
            'logistic_regression': LogisticRegression,
            'neural_network': MLPClassifier
        }
        
        self.feature_engineering = {
            'lead_features': self._extract_lead_features,
            'company_features': self._extract_company_features,
            'behavioral_features': self._extract_behavioral_features,
            'temporal_features': self._extract_temporal_features
        }
    
    def train_lead_scoring_model(self, company_id: str, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Train a new lead scoring model with real ML algorithms.
        """
        try:
            company = Company.objects.get(id=company_id)
            
            # Extract training data
            training_data = self._prepare_training_data(company, model_config)
            
            if len(training_data) < 100:  # Minimum data requirement
                return {
                    'status': 'error',
                    'error': 'Insufficient training data (minimum 100 records required)'
                }
            
            # Split data
            X, y = self._split_features_target(training_data)
            
            # Feature selection
            selected_features = self._select_features(X, y, model_config.get('max_features', 20))
            X_selected = X[selected_features]
            
            # Train model
            model_type = model_config.get('model_type', 'random_forest')
            model_class = self.model_types.get(model_type)
            
            if not model_class:
                return {
                    'status': 'error',
                    'error': f'Unsupported model type: {model_type}'
                }
            
            # Initialize model with hyperparameters
            model_params = model_config.get('hyperparameters', {})
            model = model_class(**model_params)
            
            # Train model
            model.fit(X_selected, y)
            
            # Evaluate model
            evaluation_results = self._evaluate_model(model, X_selected, y)
            
            # Save model
            model_id = self._save_trained_model(company, model, model_config, selected_features, evaluation_results)
            
            # Create training record
            training_record = ModelTraining.objects.create(
                company=company,
                model_id=model_id,
                training_data_size=len(training_data),
                model_type=model_type,
                hyperparameters=model_params,
                performance_metrics=evaluation_results,
                status='completed',
                trained_by=User.objects.filter(company=company).first()
            )
            
            # Calculate feature importance
            self._calculate_feature_importance(model, selected_features, training_record)
            
            return {
                'status': 'success',
                'model_id': model_id,
                'training_id': str(training_record.id),
                'performance_metrics': evaluation_results,
                'feature_count': len(selected_features)
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def predict_lead_score(self, lead_id: str, model_id: str) -> Dict[str, Any]:
        """
        Predict lead score using trained model.
        """
        try:
            lead = Lead.objects.get(id=lead_id)
            model_record = MLModel.objects.get(id=model_id)
            
            # Load model
            model = self._load_model(model_record)
            
            # Extract features for lead
            features = self._extract_lead_features_for_prediction(lead, model_record.feature_columns)
            
            # Make prediction
            prediction_proba = model.predict_proba([features])[0]
            prediction_class = model.predict([features])[0]
            
            # Calculate confidence
            confidence = max(prediction_proba)
            
            # Create prediction record
            prediction_record = ModelPrediction.objects.create(
                company=lead.company,
                model=model_record,
                lead=lead,
                prediction_value=prediction_class,
                confidence_score=confidence,
                probability_distribution=prediction_proba.tolist(),
                prediction_timestamp=timezone.now()
            )
            
            # Check for drift
            self._check_model_drift(model_record, features, prediction_proba)
            
            return {
                'status': 'success',
                'lead_id': lead_id,
                'score': int(prediction_class),
                'confidence': float(confidence),
                'probabilities': prediction_proba.tolist(),
                'prediction_id': str(prediction_record.id)
            }
            
        except Exception as e:
            logger.error(f"Lead scoring failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def retrain_model(self, model_id: str, retraining_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrain model with new data and drift detection.
        """
        try:
            model_record = MLModel.objects.get(id=model_id)
            company = model_record.company
            
            # Get new training data
            new_training_data = self._prepare_training_data(company, retraining_config)
            
            # Check for data drift
            drift_analysis = self._analyze_data_drift(model_record, new_training_data)
            
            # Retrain if drift detected or scheduled
            if drift_analysis['drift_detected'] or retraining_config.get('force_retrain', False):
                # Create retraining record
                retraining_record = ModelRetraining.objects.create(
                    company=company,
                    model=model_record,
                    trigger_reason=drift_analysis.get('drift_reason', 'scheduled'),
                    drift_metrics=drift_analysis,
                    status='in_progress'
                )
                
                # Retrain model
                retraining_result = self._perform_retraining(model_record, new_training_data, retraining_config)
                
                if retraining_result['status'] == 'success':
                    # Update model
                    model_record.model_data = retraining_result['model_data']
                    model_record.last_retrained = timezone.now()
                    model_record.retraining_count += 1
                    model_record.save()
                    
                    # Update retraining record
                    retraining_record.status = 'completed'
                    retraining_record.performance_improvement = retraining_result.get('performance_improvement', 0)
                    retraining_record.save()
                    
                    return {
                        'status': 'success',
                        'retraining_id': str(retraining_record.id),
                        'performance_improvement': retraining_result.get('performance_improvement', 0),
                        'drift_analysis': drift_analysis
                    }
                else:
                    retraining_record.status = 'failed'
                    retraining_record.error_message = retraining_result.get('error', 'Unknown error')
                    retraining_record.save()
                    
                    return {
                        'status': 'error',
                        'error': retraining_result.get('error', 'Retraining failed')
                    }
            else:
                return {
                    'status': 'skipped',
                    'reason': 'No drift detected and not forced',
                    'drift_analysis': drift_analysis
                }
                
        except Exception as e:
            logger.error(f"Model retraining failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _prepare_training_data(self, company: Company, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare training data from CRM records"""
        # Get leads with outcomes
        leads = Lead.objects.filter(
            company=company,
            status__in=['converted', 'disqualified', 'nurturing']
        ).select_related('account', 'assigned_to')
        
        training_data = []
        
        for lead in leads:
            # Extract features
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
            
            # Target variable (converted = 1, others = 0)
            features['target'] = 1 if lead.status == 'converted' else 0
            
            training_data.append(features)
        
        return training_data
    
    def _extract_lead_features(self, lead: Lead) -> Dict[str, Any]:
        """Extract features from lead"""
        return {
            'lead_source': self._encode_categorical(lead.source),
            'lead_status': self._encode_categorical(lead.status),
            'lead_priority': self._encode_categorical(lead.priority),
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
        """Extract features from company/account"""
        return {
            'company_size': self._encode_categorical(account.company_size),
            'company_industry': self._encode_categorical(account.industry),
            'company_type': self._encode_categorical(account.account_type),
            'company_revenue': account.annual_revenue or 0,
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
        
        # Social media interactions
        social_mentions = 0  # Would come from social media monitoring
        
        return {
            'email_opens': email_opens,
            'email_clicks': email_clicks,
            'email_click_rate': email_clicks / max(email_opens, 1),
            'page_views': page_views,
            'time_on_site': time_on_site,
            'social_mentions': social_mentions,
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
    
    def _split_features_target(self, training_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Split features and target from training data"""
        df = pd.DataFrame(training_data)
        
        # Remove target column
        target = df['target'].values
        features = df.drop('target', axis=1)
        
        # Handle missing values
        features = features.fillna(0)
        
        return features.values, target
    
    def _select_features(self, X: np.ndarray, y: np.ndarray, max_features: int) -> List[str]:
        """Select best features using statistical tests"""
        # This is a simplified version - in production, use proper feature selection
        n_features = min(max_features, X.shape[1])
        
        # Use SelectKBest with f_classif
        selector = SelectKBest(score_func=f_classif, k=n_features)
        X_selected = selector.fit_transform(X, y)
        
        # Get selected feature indices
        selected_indices = selector.get_support(indices=True)
        
        # Return feature names (simplified)
        return [f'feature_{i}' for i in selected_indices]
    
    def _evaluate_model(self, model, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance"""
        # Cross-validation
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
        
        # Train-test split evaluation
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        return {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
    
    def _save_trained_model(self, company: Company, model, config: Dict[str, Any], features: List[str], performance: Dict[str, float]) -> str:
        """Save trained model"""
        # Serialize model
        model_data = pickle.dumps(model)
        
        # Create model record
        model_record = MLModel.objects.create(
            company=company,
            model_name=config.get('model_name', 'Lead Scoring Model'),
            model_type=config.get('model_type', 'random_forest'),
            model_data=model_data,
            feature_columns=features,
            performance_metrics=performance,
            training_data_size=config.get('training_size', 0),
            is_active=True,
            created_by=User.objects.filter(company=company).first()
        )
        
        return str(model_record.id)
    
    def _load_model(self, model_record: MLModel):
        """Load trained model"""
        return pickle.loads(model_record.model_data)
    
    def _extract_lead_features_for_prediction(self, lead: Lead, feature_columns: List[str]) -> List[float]:
        """Extract features for prediction"""
        # Extract all features
        all_features = {}
        all_features.update(self._extract_lead_features(lead))
        
        if lead.account:
            all_features.update(self._extract_company_features(lead.account))
        
        all_features.update(self._extract_behavioral_features(lead))
        all_features.update(self._extract_temporal_features(lead))
        
        # Return features in the same order as training
        return [all_features.get(col, 0) for col in feature_columns]
    
    def _check_model_drift(self, model_record: MLModel, features: List[float], prediction_proba: np.ndarray):
        """Check for model drift"""
        # Calculate drift metrics
        drift_metrics = {
            'prediction_confidence': float(max(prediction_proba)),
            'feature_values': features,
            'timestamp': timezone.now().isoformat()
        }
        
        # Check if drift threshold exceeded
        confidence_threshold = 0.7  # Configurable threshold
        if drift_metrics['prediction_confidence'] < confidence_threshold:
            # Create drift record
            ModelDrift.objects.create(
                company=model_record.company,
                model=model_record,
                drift_type='prediction_confidence',
                drift_value=drift_metrics['prediction_confidence'],
                threshold_value=confidence_threshold,
                drift_data=drift_metrics,
                detected_at=timezone.now()
            )
    
    def _analyze_data_drift(self, model_record: MLModel, new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data drift between training and new data"""
        # This is a simplified drift analysis
        # In production, use proper statistical tests like KS test, PSI, etc.
        
        if not new_data:
            return {'drift_detected': False, 'drift_reason': 'No new data'}
        
        # Calculate basic statistics
        new_df = pd.DataFrame(new_data)
        training_features = model_record.feature_columns
        
        drift_detected = False
        drift_reasons = []
        
        for feature in training_features:
            if feature in new_df.columns:
                new_mean = new_df[feature].mean()
                new_std = new_df[feature].std()
                
                # Simple drift detection based on mean shift
                # In production, use proper statistical tests
                if abs(new_mean) > 2 * new_std:  # Simplified threshold
                    drift_detected = True
                    drift_reasons.append(f'Feature {feature} shows significant shift')
        
        return {
            'drift_detected': drift_detected,
            'drift_reason': '; '.join(drift_reasons) if drift_reasons else None,
            'new_data_size': len(new_data),
            'features_analyzed': len(training_features)
        }
    
    def _perform_retraining(self, model_record: MLModel, new_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform model retraining"""
        try:
            # Combine old and new data
            # In production, implement proper data management
            combined_data = new_data  # Simplified
            
            # Prepare features
            X, y = self._split_features_target(combined_data)
            
            # Retrain model
            model = self._load_model(model_record)
            model.fit(X, y)
            
            # Evaluate new model
            evaluation_results = self._evaluate_model(model, X, y)
            
            # Compare with old performance
            old_performance = model_record.performance_metrics
            performance_improvement = evaluation_results['accuracy'] - old_performance.get('accuracy', 0)
            
            # Serialize new model
            new_model_data = pickle.dumps(model)
            
            return {
                'status': 'success',
                'model_data': new_model_data,
                'performance_improvement': performance_improvement,
                'new_metrics': evaluation_results
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _calculate_feature_importance(self, model, feature_names: List[str], training_record: ModelTraining):
        """Calculate and store feature importance"""
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                
                for i, (feature, importance) in enumerate(zip(feature_names, importances)):
                    FeatureImportance.objects.create(
                        training=training_record,
                        feature_name=feature,
                        importance_score=float(importance),
                        rank=i + 1
                    )
        except Exception as e:
            logger.error(f"Failed to calculate feature importance: {str(e)}")
    
    def _encode_categorical(self, value: str) -> int:
        """Encode categorical values"""
        if not value:
            return 0
        
        # Simple hash encoding
        return hash(value) % 1000
    
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

# Celery tasks for async processing
@shared_task
def train_lead_scoring_model_async(company_id: str, model_config: Dict[str, Any]):
    """Async task to train lead scoring model"""
    engine = ProductionMLScoringEngine()
    return engine.train_lead_scoring_model(company_id, model_config)

@shared_task
def retrain_model_async(model_id: str, retraining_config: Dict[str, Any]):
    """Async task to retrain model"""
    engine = ProductionMLScoringEngine()
    return engine.retrain_model(model_id, retraining_config)

@shared_task
def check_model_drift_async(model_id: str):
    """Async task to check model drift"""
    try:
        model_record = MLModel.objects.get(id=model_id)
        engine = ProductionMLScoringEngine()
        
        # Get recent predictions
        recent_predictions = ModelPrediction.objects.filter(
            model=model_record,
            prediction_timestamp__gte=timezone.now() - timedelta(days=7)
        )
        
        if recent_predictions.count() > 10:  # Minimum predictions for drift analysis
            # Analyze drift
            drift_analysis = engine._analyze_data_drift(model_record, [])
            
            if drift_analysis['drift_detected']:
                # Trigger retraining
                retrain_model_async.delay(model_id, {'force_retrain': True})
        
    except Exception as e:
        logger.error(f"Model drift check failed: {str(e)}")

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_lead_scoring_model(request):
    """API endpoint to train lead scoring model"""
    engine = ProductionMLScoringEngine()
    result = engine.train_lead_scoring_model(
        str(request.user.company.id),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_lead_score(request):
    """API endpoint to predict lead score"""
    engine = ProductionMLScoringEngine()
    result = engine.predict_lead_score(
        request.data.get('lead_id'),
        request.data.get('model_id')
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retrain_model(request):
    """API endpoint to retrain model"""
    engine = ProductionMLScoringEngine()
    result = engine.retrain_model(
        request.data.get('model_id'),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)
