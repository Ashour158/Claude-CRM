# ai_scoring/assignment_model.py
# Assignment Model with Capacity + Probability Scoring

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
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import pickle
from celery import shared_task

from .models import (
    AssignmentModel, AssignmentScore, CapacityProfile, 
    AssignmentFeature, AssignmentResult, AssignmentMetrics
)
from core.models import User, Company
from crm.models import Lead, Deal, Account, Activity

logger = logging.getLogger(__name__)

class AssignmentModelEngine:
    """
    Advanced assignment model with capacity analysis and probability scoring
    for intelligent lead/opportunity assignment.
    """
    
    def __init__(self):
        self.assignment_factors = {
            'capacity': self._calculate_capacity_score,
            'probability': self._calculate_probability_score,
            'territory': self._calculate_territory_score,
            'workload': self._calculate_workload_score,
            'performance': self._calculate_performance_score,
            'preference': self._calculate_preference_score
        }
        
        self.capacity_metrics = {
            'current_workload': self._get_current_workload,
            'max_capacity': self._get_max_capacity,
            'utilization_rate': self._get_utilization_rate,
            'skill_match': self._get_skill_match,
            'availability': self._get_availability
        }
        
        self.probability_factors = {
            'lead_quality': self._get_lead_quality_score,
            'company_fit': self._get_company_fit_score,
            'timing': self._get_timing_score,
            'source_quality': self._get_source_quality_score,
            'behavioral_signals': self._get_behavioral_signals_score
        }
    
    def assign_lead(self, lead_id: str, assignment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign lead to best available user based on capacity and probability scoring.
        """
        try:
            # Get lead details
            lead = Lead.objects.get(id=lead_id)
            
            # Get available users
            available_users = self._get_available_users(lead, assignment_config)
            
            if not available_users:
                return {
                    'status': 'error',
                    'error': 'No available users for assignment'
                }
            
            # Calculate assignment scores for each user
            assignment_scores = []
            for user in available_users:
                score = self._calculate_assignment_score(lead, user, assignment_config)
                assignment_scores.append({
                    'user': user,
                    'score': score,
                    'breakdown': self._get_score_breakdown(lead, user, assignment_config)
                })
            
            # Sort by score and select best user
            assignment_scores.sort(key=lambda x: x['score']['total_score'], reverse=True)
            best_assignment = assignment_scores[0]
            
            # Assign lead to best user
            lead.assigned_to = best_assignment['user']
            lead.assignment_score = best_assignment['score']['total_score']
            lead.assignment_breakdown = best_assignment['breakdown']
            lead.assigned_at = timezone.now()
            lead.save()
            
            # Log assignment result
            assignment_result = self._log_assignment_result(
                lead, best_assignment, assignment_config
            )
            
            return {
                'status': 'success',
                'assigned_user': {
                    'id': str(best_assignment['user'].id),
                    'email': best_assignment['user'].email,
                    'name': best_assignment['user'].get_full_name()
                },
                'assignment_score': best_assignment['score']['total_score'],
                'score_breakdown': best_assignment['breakdown'],
                'assignment_id': str(assignment_result.id),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Lead assignment failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def batch_assign_leads(self, lead_ids: List[str], assignment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Batch assign multiple leads using optimization algorithm.
        """
        try:
            # Get all leads
            leads = Lead.objects.filter(id__in=lead_ids)
            
            # Get available users
            available_users = self._get_available_users_for_batch(leads, assignment_config)
            
            if not available_users:
                return {
                    'status': 'error',
                    'error': 'No available users for batch assignment'
                }
            
            # Create assignment matrix
            assignment_matrix = self._create_assignment_matrix(leads, available_users, assignment_config)
            
            # Solve assignment optimization
            optimal_assignments = self._solve_assignment_optimization(assignment_matrix, assignment_config)
            
            # Apply assignments
            assignment_results = []
            for lead, user, score in optimal_assignments:
                lead.assigned_to = user
                lead.assignment_score = score
                lead.assigned_at = timezone.now()
                lead.save()
                
                assignment_results.append({
                    'lead_id': str(lead.id),
                    'user_id': str(user.id),
                    'score': score
                })
            
            # Log batch assignment results
            batch_result = self._log_batch_assignment_results(
                assignment_results, assignment_config
            )
            
            return {
                'status': 'success',
                'assignments': assignment_results,
                'batch_id': str(batch_result.id),
                'total_assigned': len(assignment_results),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch assignment failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def optimize_assignment_model(self, training_data: List[Dict[str, Any]], 
                                optimization_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize assignment model using machine learning.
        """
        try:
            # Prepare training data
            X_train, y_train = self._prepare_assignment_training_data(training_data)
            
            # Train assignment model
            assignment_model = self._train_assignment_model(X_train, y_train, optimization_config)
            
            # Evaluate model performance
            evaluation_results = self._evaluate_assignment_model(assignment_model, training_data)
            
            # Save optimized model
            model_record = self._save_assignment_model(assignment_model, evaluation_results, optimization_config)
            
            return {
                'status': 'success',
                'model_id': str(model_record.id),
                'evaluation_results': evaluation_results,
                'optimization_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Assignment model optimization failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _calculate_assignment_score(self, lead: Lead, user: User, config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive assignment score"""
        try:
            # Get individual factor scores
            capacity_score = self._calculate_capacity_score(lead, user, config)
            probability_score = self._calculate_probability_score(lead, user, config)
            territory_score = self._calculate_territory_score(lead, user, config)
            workload_score = self._calculate_workload_score(lead, user, config)
            performance_score = self._calculate_performance_score(lead, user, config)
            preference_score = self._calculate_preference_score(lead, user, config)
            
            # Calculate weighted total score
            weights = config.get('assignment_weights', {
                'capacity': 0.25,
                'probability': 0.20,
                'territory': 0.15,
                'workload': 0.15,
                'performance': 0.15,
                'preference': 0.10
            })
            
            total_score = (
                weights['capacity'] * capacity_score +
                weights['probability'] * probability_score +
                weights['territory'] * territory_score +
                weights['workload'] * workload_score +
                weights['performance'] * performance_score +
                weights['preference'] * preference_score
            )
            
            return {
                'total_score': total_score,
                'capacity_score': capacity_score,
                'probability_score': probability_score,
                'territory_score': territory_score,
                'workload_score': workload_score,
                'performance_score': performance_score,
                'preference_score': preference_score
            }
            
        except Exception as e:
            logger.error(f"Assignment score calculation failed: {str(e)}")
            return {
                'total_score': 0.0,
                'capacity_score': 0.0,
                'probability_score': 0.0,
                'territory_score': 0.0,
                'workload_score': 0.0,
                'performance_score': 0.0,
                'preference_score': 0.0
            }
    
    def _calculate_capacity_score(self, lead: Lead, user: User, config: Dict[str, Any]) -> float:
        """Calculate capacity-based assignment score"""
        try:
            # Get user's current capacity metrics
            current_workload = self._get_current_workload(user)
            max_capacity = self._get_max_capacity(user)
            utilization_rate = self._get_utilization_rate(user)
            skill_match = self._get_skill_match(lead, user)
            availability = self._get_availability(user)
            
            # Calculate capacity score (0-1, higher is better)
            capacity_score = 0.0
            
            # Utilization factor (lower utilization = higher score)
            if utilization_rate < 0.7:
                capacity_score += 0.4
            elif utilization_rate < 0.9:
                capacity_score += 0.2
            
            # Skill match factor
            capacity_score += skill_match * 0.3
            
            # Availability factor
            capacity_score += availability * 0.3
            
            return min(capacity_score, 1.0)
            
        except Exception as e:
            logger.error(f"Capacity score calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_probability_score(self, lead: Lead, user: User, config: Dict[str, Any]) -> float:
        """Calculate probability-based assignment score"""
        try:
            # Get probability factors
            lead_quality = self._get_lead_quality_score(lead)
            company_fit = self._get_company_fit_score(lead, user)
            timing = self._get_timing_score(lead, user)
            source_quality = self._get_source_quality_score(lead)
            behavioral_signals = self._get_behavioral_signals_score(lead)
            
            # Calculate weighted probability score
            weights = {
                'lead_quality': 0.3,
                'company_fit': 0.25,
                'timing': 0.15,
                'source_quality': 0.15,
                'behavioral_signals': 0.15
            }
            
            probability_score = (
                weights['lead_quality'] * lead_quality +
                weights['company_fit'] * company_fit +
                weights['timing'] * timing +
                weights['source_quality'] * source_quality +
                weights['behavioral_signals'] * behavioral_signals
            )
            
            return min(probability_score, 1.0)
            
        except Exception as e:
            logger.error(f"Probability score calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_territory_score(self, lead: Lead, user: User, config: Dict[str, Any]) -> float:
        """Calculate territory-based assignment score"""
        try:
            # Check if user has territory assignments
            user_territories = user.territories.all()
            
            if not user_territories.exists():
                return 0.5  # Neutral score if no territory constraints
            
            # Check if lead matches user's territories
            lead_location = self._get_lead_location(lead)
            
            territory_match = 0.0
            for territory in user_territories:
                if self._check_territory_match(lead_location, territory):
                    territory_match = 1.0
                    break
            
            return territory_match
            
        except Exception as e:
            logger.error(f"Territory score calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_workload_score(self, lead: Lead, user: User, config: Dict[str, Any]) -> float:
        """Calculate workload-based assignment score"""
        try:
            # Get user's current workload
            current_workload = self._get_current_workload(user)
            max_workload = self._get_max_capacity(user)
            
            # Calculate workload score (lower workload = higher score)
            if max_workload > 0:
                workload_ratio = current_workload / max_workload
                workload_score = max(0.0, 1.0 - workload_ratio)
            else:
                workload_score = 0.5
            
            return workload_score
            
        except Exception as e:
            logger.error(f"Workload score calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_performance_score(self, lead: Lead, user: User, config: Dict[str, Any]) -> float:
        """Calculate performance-based assignment score"""
        try:
            # Get user's historical performance
            performance_metrics = self._get_user_performance_metrics(user)
            
            # Calculate performance score based on historical success
            performance_score = 0.0
            
            # Conversion rate factor
            if performance_metrics.get('conversion_rate', 0) > 0.15:
                performance_score += 0.4
            elif performance_metrics.get('conversion_rate', 0) > 0.10:
                performance_score += 0.2
            
            # Deal value factor
            if performance_metrics.get('avg_deal_value', 0) > 50000:
                performance_score += 0.3
            elif performance_metrics.get('avg_deal_value', 0) > 25000:
                performance_score += 0.15
            
            # Activity factor
            if performance_metrics.get('activity_score', 0) > 0.7:
                performance_score += 0.3
            elif performance_metrics.get('activity_score', 0) > 0.5:
                performance_score += 0.15
            
            return min(performance_score, 1.0)
            
        except Exception as e:
            logger.error(f"Performance score calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_preference_score(self, lead: Lead, user: User, config: Dict[str, Any]) -> float:
        """Calculate preference-based assignment score"""
        try:
            # Get user preferences
            user_preferences = self._get_user_preferences(user)
            
            # Calculate preference score
            preference_score = 0.0
            
            # Lead source preference
            if lead.source in user_preferences.get('preferred_sources', []):
                preference_score += 0.3
            
            # Industry preference
            if lead.company_name and lead.company_name in user_preferences.get('preferred_industries', []):
                preference_score += 0.3
            
            # Lead size preference
            lead_size = self._get_lead_size(lead)
            if lead_size in user_preferences.get('preferred_sizes', []):
                preference_score += 0.2
            
            # Geographic preference
            lead_location = self._get_lead_location(lead)
            if lead_location in user_preferences.get('preferred_locations', []):
                preference_score += 0.2
            
            return min(preference_score, 1.0)
            
        except Exception as e:
            logger.error(f"Preference score calculation failed: {str(e)}")
            return 0.0
    
    def _get_current_workload(self, user: User) -> int:
        """Get user's current workload"""
        try:
            # Count active leads
            active_leads = Lead.objects.filter(
                assigned_to=user,
                status__in=['new', 'contacted', 'qualified', 'nurturing']
            ).count()
            
            # Count active deals
            active_deals = Deal.objects.filter(
                assigned_to=user,
                status__in=['open', 'negotiation', 'proposal']
            ).count()
            
            # Count pending activities
            pending_activities = Activity.objects.filter(
                assigned_to=user,
                status='pending'
            ).count()
            
            return active_leads + active_deals + pending_activities
            
        except Exception as e:
            logger.error(f"Current workload calculation failed: {str(e)}")
            return 0
    
    def _get_max_capacity(self, user: User) -> int:
        """Get user's maximum capacity"""
        try:
            # Get user's capacity profile
            capacity_profile = CapacityProfile.objects.filter(user=user).first()
            
            if capacity_profile:
                return capacity_profile.max_leads + capacity_profile.max_deals
            else:
                # Default capacity based on user role
                if user.role == 'sales_manager':
                    return 50
                elif user.role == 'sales_rep':
                    return 30
                else:
                    return 20
                    
        except Exception as e:
            logger.error(f"Max capacity calculation failed: {str(e)}")
            return 20
    
    def _get_utilization_rate(self, user: User) -> float:
        """Get user's current utilization rate"""
        try:
            current_workload = self._get_current_workload(user)
            max_capacity = self._get_max_capacity(user)
            
            if max_capacity > 0:
                return current_workload / max_capacity
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Utilization rate calculation failed: {str(e)}")
            return 0.0
    
    def _get_skill_match(self, lead: Lead, user: User) -> float:
        """Get skill match score between lead and user"""
        try:
            # This would implement actual skill matching logic
            # For now, return a placeholder score
            return 0.7
            
        except Exception as e:
            logger.error(f"Skill match calculation failed: {str(e)}")
            return 0.0
    
    def _get_availability(self, user: User) -> float:
        """Get user's availability score"""
        try:
            # Check if user is currently available
            # This would check calendar, status, etc.
            # For now, return a placeholder score
            return 0.8
            
        except Exception as e:
            logger.error(f"Availability calculation failed: {str(e)}")
            return 0.0
    
    def _get_lead_quality_score(self, lead: Lead) -> float:
        """Get lead quality score"""
        try:
            quality_score = 0.0
            
            # Email quality
            if lead.email and '@' in lead.email:
                quality_score += 0.2
            
            # Phone quality
            if lead.phone and len(lead.phone) >= 10:
                quality_score += 0.2
            
            # Company quality
            if lead.company_name:
                quality_score += 0.2
            
            # Source quality
            if lead.source in ['referral', 'website', 'social_media']:
                quality_score += 0.2
            
            # Score quality
            if lead.score and lead.score > 70:
                quality_score += 0.2
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            logger.error(f"Lead quality score calculation failed: {str(e)}")
            return 0.0
    
    def _get_company_fit_score(self, lead: Lead, user: User) -> float:
        """Get company fit score"""
        try:
            # This would implement actual company fit logic
            # For now, return a placeholder score
            return 0.6
            
        except Exception as e:
            logger.error(f"Company fit score calculation failed: {str(e)}")
            return 0.0
    
    def _get_timing_score(self, lead: Lead, user: User) -> float:
        """Get timing score"""
        try:
            # This would implement actual timing logic
            # For now, return a placeholder score
            return 0.5
            
        except Exception as e:
            logger.error(f"Timing score calculation failed: {str(e)}")
            return 0.0
    
    def _get_source_quality_score(self, lead: Lead) -> float:
        """Get source quality score"""
        try:
            source_scores = {
                'referral': 0.9,
                'website': 0.8,
                'social_media': 0.7,
                'email': 0.6,
                'phone': 0.5,
                'other': 0.4
            }
            
            return source_scores.get(lead.source, 0.5)
            
        except Exception as e:
            logger.error(f"Source quality score calculation failed: {str(e)}")
            return 0.0
    
    def _get_behavioral_signals_score(self, lead: Lead) -> float:
        """Get behavioral signals score"""
        try:
            # This would implement actual behavioral analysis
            # For now, return a placeholder score
            return 0.6
            
        except Exception as e:
            logger.error(f"Behavioral signals score calculation failed: {str(e)}")
            return 0.0
    
    def _get_lead_location(self, lead: Lead) -> str:
        """Get lead location"""
        try:
            # This would extract location from lead data
            # For now, return a placeholder
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Lead location extraction failed: {str(e)}")
            return 'unknown'
    
    def _check_territory_match(self, lead_location: str, territory) -> bool:
        """Check if lead location matches territory"""
        try:
            # This would implement actual territory matching
            # For now, return True as placeholder
            return True
            
        except Exception as e:
            logger.error(f"Territory match check failed: {str(e)}")
            return False
    
    def _get_user_performance_metrics(self, user: User) -> Dict[str, Any]:
        """Get user's performance metrics"""
        try:
            # This would calculate actual performance metrics
            # For now, return placeholder metrics
            return {
                'conversion_rate': 0.15,
                'avg_deal_value': 35000,
                'activity_score': 0.7
            }
            
        except Exception as e:
            logger.error(f"User performance metrics calculation failed: {str(e)}")
            return {}
    
    def _get_user_preferences(self, user: User) -> Dict[str, Any]:
        """Get user preferences"""
        try:
            # This would get actual user preferences
            # For now, return placeholder preferences
            return {
                'preferred_sources': ['referral', 'website'],
                'preferred_industries': ['technology', 'finance'],
                'preferred_sizes': ['medium', 'large'],
                'preferred_locations': ['US', 'Canada']
            }
            
        except Exception as e:
            logger.error(f"User preferences retrieval failed: {str(e)}")
            return {}
    
    def _get_lead_size(self, lead: Lead) -> str:
        """Get lead size category"""
        try:
            # This would determine lead size based on company data
            # For now, return a placeholder
            return 'medium'
            
        except Exception as e:
            logger.error(f"Lead size determination failed: {str(e)}")
            return 'unknown'
    
    def _get_available_users(self, lead: Lead, config: Dict[str, Any]) -> List[User]:
        """Get available users for assignment"""
        try:
            # Get users from the same company
            users = User.objects.filter(
                company=lead.company,
                is_active=True
            )
            
            # Apply filters
            if config.get('role_filter'):
                users = users.filter(role__in=config['role_filter'])
            
            if config.get('territory_filter'):
                users = users.filter(territories__in=config['territory_filter'])
            
            return list(users)
            
        except Exception as e:
            logger.error(f"Available users retrieval failed: {str(e)}")
            return []
    
    def _get_available_users_for_batch(self, leads: List[Lead], config: Dict[str, Any]) -> List[User]:
        """Get available users for batch assignment"""
        try:
            # Get users from the same company as leads
            company_ids = set(lead.company.id for lead in leads)
            
            users = User.objects.filter(
                company_id__in=company_ids,
                is_active=True
            )
            
            return list(users)
            
        except Exception as e:
            logger.error(f"Available users for batch retrieval failed: {str(e)}")
            return []
    
    def _create_assignment_matrix(self, leads: List[Lead], users: List[User], config: Dict[str, Any]) -> np.ndarray:
        """Create assignment matrix for optimization"""
        try:
            matrix = np.zeros((len(leads), len(users)))
            
            for i, lead in enumerate(leads):
                for j, user in enumerate(users):
                    score = self._calculate_assignment_score(lead, user, config)
                    matrix[i, j] = score['total_score']
            
            return matrix
            
        except Exception as e:
            logger.error(f"Assignment matrix creation failed: {str(e)}")
            return np.zeros((len(leads), len(users)))
    
    def _solve_assignment_optimization(self, matrix: np.ndarray, config: Dict[str, Any]) -> List[Tuple[Lead, User, float]]:
        """Solve assignment optimization problem"""
        try:
            # This would implement actual optimization algorithm
            # For now, return simple greedy assignment
            assignments = []
            
            for i in range(matrix.shape[0]):
                best_user_idx = np.argmax(matrix[i])
                best_score = matrix[i, best_user_idx]
                assignments.append((i, best_user_idx, best_score))
            
            return assignments
            
        except Exception as e:
            logger.error(f"Assignment optimization failed: {str(e)}")
            return []
    
    def _get_score_breakdown(self, lead: Lead, user: User, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed score breakdown"""
        try:
            score = self._calculate_assignment_score(lead, user, config)
            return {
                'total_score': score['total_score'],
                'capacity_score': score['capacity_score'],
                'probability_score': score['probability_score'],
                'territory_score': score['territory_score'],
                'workload_score': score['workload_score'],
                'performance_score': score['performance_score'],
                'preference_score': score['preference_score']
            }
            
        except Exception as e:
            logger.error(f"Score breakdown calculation failed: {str(e)}")
            return {}
    
    def _log_assignment_result(self, lead: Lead, assignment: Dict[str, Any], config: Dict[str, Any]) -> AssignmentResult:
        """Log assignment result"""
        return AssignmentResult.objects.create(
            lead=lead,
            assigned_user=assignment['user'],
            assignment_score=assignment['score']['total_score'],
            score_breakdown=assignment['breakdown'],
            assignment_config=config,
            assigned_at=timezone.now()
        )
    
    def _log_batch_assignment_results(self, assignment_results: List[Dict[str, Any]], config: Dict[str, Any]) -> Any:
        """Log batch assignment results"""
        # This would create a batch assignment record
        # For now, return a placeholder
        return None
    
    def _prepare_assignment_training_data(self, training_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for assignment model"""
        # This would prepare actual training data
        # For now, return placeholders
        X = np.random.randn(100, 20)
        y = np.random.randn(100)
        return X, y
    
    def _train_assignment_model(self, X_train: np.ndarray, y_train: np.ndarray, config: Dict[str, Any]) -> Any:
        """Train assignment model"""
        # This would train the actual model
        # For now, return a placeholder
        return None
    
    def _evaluate_assignment_model(self, model: Any, test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate assignment model"""
        # This would evaluate the actual model
        # For now, return placeholder metrics
        return {
            'accuracy': 0.85,
            'precision': 0.82,
            'recall': 0.78,
            'f1_score': 0.80
        }
    
    def _save_assignment_model(self, model: Any, evaluation_results: Dict[str, Any], config: Dict[str, Any]) -> AssignmentModel:
        """Save assignment model"""
        return AssignmentModel.objects.create(
            model_name=config.get('model_name', 'Assignment Model'),
            model_data=pickle.dumps(model),
            evaluation_results=evaluation_results,
            is_active=True,
            created_at=timezone.now()
        )

# Celery tasks
@shared_task
def assign_lead_async(lead_id: str, assignment_config: Dict[str, Any]):
    """Async task to assign lead"""
    engine = AssignmentModelEngine()
    return engine.assign_lead(lead_id, assignment_config)

@shared_task
def batch_assign_leads_async(lead_ids: List[str], assignment_config: Dict[str, Any]):
    """Async task to batch assign leads"""
    engine = AssignmentModelEngine()
    return engine.batch_assign_leads(lead_ids, assignment_config)

@shared_task
def optimize_assignment_model_async(training_data: List[Dict[str, Any]], optimization_config: Dict[str, Any]):
    """Async task to optimize assignment model"""
    engine = AssignmentModelEngine()
    return engine.optimize_assignment_model(training_data, optimization_config)

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_lead(request):
    """API endpoint to assign lead"""
    engine = AssignmentModelEngine()
    result = engine.assign_lead(
        request.data.get('lead_id'),
        request.data.get('assignment_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_assign_leads(request):
    """API endpoint to batch assign leads"""
    engine = AssignmentModelEngine()
    result = engine.batch_assign_leads(
        request.data.get('lead_ids', []),
        request.data.get('assignment_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def optimize_assignment_model(request):
    """API endpoint to optimize assignment model"""
    engine = AssignmentModelEngine()
    result = engine.optimize_assignment_model(
        request.data.get('training_data', []),
        request.data.get('optimization_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)
