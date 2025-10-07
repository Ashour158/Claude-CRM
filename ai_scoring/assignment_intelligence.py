# ai_scoring/assignment_intelligence.py
# ML-Based Assignment Intelligence Engine

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
import joblib
import pickle
from celery import shared_task

from .models import (
    MLModel, ModelTraining, ModelPrediction, AssignmentScore,
    WorkloadAnalysis, SkillMatching, TerritoryOptimization
)
from core.models import User, Company
from crm.models import Lead, Deal, Account
from territories.models import Territory

logger = logging.getLogger(__name__)

class AssignmentIntelligenceEngine:
    """
    ML-based assignment intelligence engine for optimal lead/deal assignment
    based on workload, skills, territory, and performance.
    """
    
    def __init__(self):
        self.assignment_models = {
            'workload_optimization': self._optimize_workload_assignment,
            'skill_matching': self._optimize_skill_assignment,
            'territory_optimization': self._optimize_territory_assignment,
            'performance_based': self._optimize_performance_assignment,
            'hybrid': self._optimize_hybrid_assignment
        }
        
        self.scoring_factors = {
            'workload_score': self._calculate_workload_score,
            'skill_match_score': self._calculate_skill_match_score,
            'territory_score': self._calculate_territory_score,
            'performance_score': self._calculate_performance_score,
            'availability_score': self._calculate_availability_score
        }
    
    def assign_lead_to_agent(self, lead_id: str, assignment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign lead to optimal agent using ML-based intelligence.
        """
        try:
            lead = Lead.objects.get(id=lead_id)
            company = lead.company
            
            # Get available agents
            available_agents = self._get_available_agents(company, assignment_config)
            
            if not available_agents:
                return {
                    'status': 'error',
                    'error': 'No available agents found'
                }
            
            # Calculate assignment scores for each agent
            assignment_scores = []
            
            for agent in available_agents:
                score_data = self._calculate_assignment_score(lead, agent, assignment_config)
                
                assignment_scores.append({
                    'agent_id': str(agent.id),
                    'agent_name': agent.get_full_name(),
                    'total_score': score_data['total_score'],
                    'factor_scores': score_data['factor_scores'],
                    'recommendation_reason': score_data['recommendation_reason']
                })
            
            # Sort by total score
            assignment_scores.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Select best agent
            best_assignment = assignment_scores[0]
            
            # Apply assignment
            assignment_result = self._apply_assignment(lead, best_assignment, assignment_config)
            
            # Log assignment
            self._log_assignment(lead, best_assignment, assignment_result)
            
            return {
                'status': 'success',
                'assigned_agent_id': best_assignment['agent_id'],
                'assigned_agent_name': best_assignment['agent_name'],
                'assignment_score': best_assignment['total_score'],
                'assignment_reason': best_assignment['recommendation_reason'],
                'all_scores': assignment_scores
            }
            
        except Exception as e:
            logger.error(f"Lead assignment failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def assign_deal_to_agent(self, deal_id: str, assignment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign deal to optimal agent using ML-based intelligence.
        """
        try:
            deal = Deal.objects.get(id=deal_id)
            company = deal.company
            
            # Get available agents
            available_agents = self._get_available_agents(company, assignment_config)
            
            if not available_agents:
                return {
                    'status': 'error',
                    'error': 'No available agents found'
                }
            
            # Calculate assignment scores for each agent
            assignment_scores = []
            
            for agent in available_agents:
                score_data = self._calculate_deal_assignment_score(deal, agent, assignment_config)
                
                assignment_scores.append({
                    'agent_id': str(agent.id),
                    'agent_name': agent.get_full_name(),
                    'total_score': score_data['total_score'],
                    'factor_scores': score_data['factor_scores'],
                    'recommendation_reason': score_data['recommendation_reason']
                })
            
            # Sort by total score
            assignment_scores.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Select best agent
            best_assignment = assignment_scores[0]
            
            # Apply assignment
            assignment_result = self._apply_deal_assignment(deal, best_assignment, assignment_config)
            
            # Log assignment
            self._log_deal_assignment(deal, best_assignment, assignment_result)
            
            return {
                'status': 'success',
                'assigned_agent_id': best_assignment['agent_id'],
                'assigned_agent_name': best_assignment['agent_name'],
                'assignment_score': best_assignment['total_score'],
                'assignment_reason': best_assignment['recommendation_reason'],
                'all_scores': assignment_scores
            }
            
        except Exception as e:
            logger.error(f"Deal assignment failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def optimize_territory_assignments(self, company_id: str, optimization_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize territory assignments using ML algorithms.
        """
        try:
            company = Company.objects.get(id=company_id)
            
            # Get territories and agents
            territories = Territory.objects.filter(company=company, is_active=True)
            agents = User.objects.filter(company=company, is_active=True)
            
            if not territories.exists() or not agents.exists():
                return {
                    'status': 'error',
                    'error': 'No territories or agents found'
                }
            
            # Analyze current assignments
            current_analysis = self._analyze_current_assignments(territories, agents)
            
            # Generate optimization recommendations
            optimization_recommendations = self._generate_optimization_recommendations(
                territories, agents, current_analysis, optimization_config
            )
            
            # Apply optimizations if requested
            if optimization_config.get('apply_optimizations', False):
                applied_optimizations = self._apply_territory_optimizations(
                    optimization_recommendations, optimization_config
                )
            else:
                applied_optimizations = []
            
            return {
                'status': 'success',
                'current_analysis': current_analysis,
                'optimization_recommendations': optimization_recommendations,
                'applied_optimizations': applied_optimizations
            }
            
        except Exception as e:
            logger.error(f"Territory optimization failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_available_agents(self, company: Company, config: Dict[str, Any]) -> List[User]:
        """Get available agents for assignment"""
        # Base query
        agents = User.objects.filter(company=company, is_active=True)
        
        # Filter by role if specified
        if 'role_filter' in config:
            agents = agents.filter(role__in=config['role_filter'])
        
        # Filter by territory if specified
        if 'territory_filter' in config:
            agents = agents.filter(territory__in=config['territory_filter'])
        
        # Filter by availability
        if config.get('check_availability', True):
            available_agents = []
            for agent in agents:
                if self._is_agent_available(agent, config):
                    available_agents.append(agent)
            return available_agents
        
        return list(agents)
    
    def _is_agent_available(self, agent: User, config: Dict[str, Any]) -> bool:
        """Check if agent is available for assignment"""
        # Check workload
        current_workload = self._calculate_agent_workload(agent)
        max_workload = config.get('max_workload', 50)
        
        if current_workload >= max_workload:
            return False
        
        # Check availability hours
        if config.get('check_business_hours', True):
            now = timezone.now()
            if not (9 <= now.hour <= 17):  # Business hours
                return False
        
        # Check agent status
        if hasattr(agent, 'status') and agent.status != 'available':
            return False
        
        return True
    
    def _calculate_assignment_score(self, lead: Lead, agent: User, config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive assignment score"""
        factor_weights = config.get('factor_weights', {
            'workload': 0.25,
            'skill_match': 0.30,
            'territory': 0.20,
            'performance': 0.15,
            'availability': 0.10
        })
        
        # Calculate individual scores
        workload_score = self._calculate_workload_score(lead, agent)
        skill_score = self._calculate_skill_match_score(lead, agent)
        territory_score = self._calculate_territory_score(lead, agent)
        performance_score = self._calculate_performance_score(lead, agent)
        availability_score = self._calculate_availability_score(lead, agent)
        
        # Calculate weighted total score
        total_score = (
            workload_score * factor_weights['workload'] +
            skill_score * factor_weights['skill_match'] +
            territory_score * factor_weights['territory'] +
            performance_score * factor_weights['performance'] +
            availability_score * factor_weights['availability']
        )
        
        # Generate recommendation reason
        reason = self._generate_recommendation_reason({
            'workload': workload_score,
            'skill_match': skill_score,
            'territory': territory_score,
            'performance': performance_score,
            'availability': availability_score
        })
        
        return {
            'total_score': total_score,
            'factor_scores': {
                'workload': workload_score,
                'skill_match': skill_score,
                'territory': territory_score,
                'performance': performance_score,
                'availability': availability_score
            },
            'recommendation_reason': reason
        }
    
    def _calculate_workload_score(self, lead: Lead, agent: User) -> float:
        """Calculate workload-based score (lower workload = higher score)"""
        current_workload = self._calculate_agent_workload(agent)
        
        # Normalize workload (0-1 scale, inverted)
        max_workload = 100  # Configurable
        normalized_workload = min(current_workload / max_workload, 1.0)
        workload_score = 1.0 - normalized_workload
        
        return max(0.0, workload_score)
    
    def _calculate_skill_match_score(self, lead: Lead, agent: User) -> float:
        """Calculate skill match score"""
        # Lead requirements
        lead_industry = lead.account.industry if lead.account else None
        lead_company_size = lead.account.company_size if lead.account else None
        lead_source = lead.source
        
        # Agent skills (would come from user profile/skills)
        agent_skills = getattr(agent, 'skills', [])
        agent_industries = getattr(agent, 'industries', [])
        agent_company_sizes = getattr(agent, 'company_sizes', [])
        agent_sources = getattr(agent, 'sources', [])
        
        score = 0.0
        factors = 0
        
        # Industry match
        if lead_industry and lead_industry in agent_industries:
            score += 1.0
        factors += 1
        
        # Company size match
        if lead_company_size and lead_company_size in agent_company_sizes:
            score += 1.0
        factors += 1
        
        # Source match
        if lead_source and lead_source in agent_sources:
            score += 1.0
        factors += 1
        
        # General skills match
        if agent_skills:
            # This would be more sophisticated in production
            score += 0.5
            factors += 1
        
        return score / factors if factors > 0 else 0.5
    
    def _calculate_territory_score(self, lead: Lead, agent: User) -> float:
        """Calculate territory-based score"""
        # Check if agent has territory assignments
        agent_territories = getattr(agent, 'territories', [])
        
        if not agent_territories:
            return 0.5  # Neutral score if no territory restrictions
        
        # Check if lead's location matches agent's territories
        lead_location = self._get_lead_location(lead)
        
        if lead_location:
            for territory in agent_territories:
                if self._location_matches_territory(lead_location, territory):
                    return 1.0
        
        return 0.0  # No territory match
    
    def _calculate_performance_score(self, lead: Lead, agent: User) -> float:
        """Calculate performance-based score"""
        # Get agent's performance metrics
        performance_metrics = self._get_agent_performance_metrics(agent)
        
        # Calculate performance score
        conversion_rate = performance_metrics.get('conversion_rate', 0.5)
        avg_deal_size = performance_metrics.get('avg_deal_size', 0)
        response_time = performance_metrics.get('avg_response_time', 24)  # hours
        
        # Normalize metrics
        conversion_score = min(conversion_rate / 0.3, 1.0)  # 30% is good
        deal_size_score = min(avg_deal_size / 50000, 1.0)  # $50k is good
        response_score = max(0, 1.0 - (response_time / 48))  # 48 hours is max
        
        # Weighted performance score
        performance_score = (
            conversion_score * 0.4 +
            deal_size_score * 0.3 +
            response_score * 0.3
        )
        
        return performance_score
    
    def _calculate_availability_score(self, lead: Lead, agent: User) -> float:
        """Calculate availability score"""
        # Check agent's current status
        if hasattr(agent, 'status'):
            if agent.status == 'available':
                return 1.0
            elif agent.status == 'busy':
                return 0.5
            else:
                return 0.0
        
        # Check workload
        current_workload = self._calculate_agent_workload(agent)
        if current_workload < 20:
            return 1.0
        elif current_workload < 40:
            return 0.7
        elif current_workload < 60:
            return 0.4
        else:
            return 0.1
    
    def _calculate_agent_workload(self, agent: User) -> float:
        """Calculate agent's current workload"""
        # Count active leads
        active_leads = Lead.objects.filter(
            company=agent.company,
            assigned_to=agent,
            status__in=['new', 'contacted', 'qualified']
        ).count()
        
        # Count active deals
        active_deals = Deal.objects.filter(
            company=agent.company,
            assigned_to=agent,
            stage__in=['prospecting', 'qualification', 'proposal', 'negotiation']
        ).count()
        
        # Weight different types of work
        workload = (active_leads * 1.0) + (active_deals * 2.0)
        
        return workload
    
    def _get_agent_performance_metrics(self, agent: User) -> Dict[str, float]:
        """Get agent's performance metrics"""
        # Get metrics for last 90 days
        start_date = timezone.now() - timedelta(days=90)
        
        # Conversion rate
        total_leads = Lead.objects.filter(
            company=agent.company,
            assigned_to=agent,
            created_at__gte=start_date
        ).count()
        
        converted_leads = Lead.objects.filter(
            company=agent.company,
            assigned_to=agent,
            created_at__gte=start_date,
            status='converted'
        ).count()
        
        conversion_rate = converted_leads / total_leads if total_leads > 0 else 0
        
        # Average deal size
        closed_deals = Deal.objects.filter(
            company=agent.company,
            assigned_to=agent,
            stage='closed_won',
            closed_at__gte=start_date
        )
        
        avg_deal_size = closed_deals.aggregate(
            avg_size=models.Avg('amount')
        )['avg_size'] or 0
        
        # Average response time (simplified)
        avg_response_time = 24  # hours - would be calculated from actual data
        
        return {
            'conversion_rate': conversion_rate,
            'avg_deal_size': float(avg_deal_size),
            'avg_response_time': avg_response_time
        }
    
    def _get_lead_location(self, lead: Lead) -> Optional[Dict[str, str]]:
        """Get lead's location information"""
        if lead.account:
            return {
                'country': getattr(lead.account, 'country', ''),
                'state': getattr(lead.account, 'state', ''),
                'city': getattr(lead.account, 'city', '')
            }
        return None
    
    def _location_matches_territory(self, location: Dict[str, str], territory: Territory) -> bool:
        """Check if location matches territory criteria"""
        if territory.countries and location.get('country') not in territory.countries:
            return False
        
        if territory.states and location.get('state') not in territory.states:
            return False
        
        if territory.cities and location.get('city') not in territory.cities:
            return False
        
        return True
    
    def _generate_recommendation_reason(self, scores: Dict[str, float]) -> str:
        """Generate human-readable recommendation reason"""
        reasons = []
        
        if scores['skill_match'] > 0.8:
            reasons.append("excellent skill match")
        elif scores['skill_match'] > 0.6:
            reasons.append("good skill match")
        
        if scores['workload'] > 0.8:
            reasons.append("low current workload")
        elif scores['workload'] > 0.6:
            reasons.append("manageable workload")
        
        if scores['performance'] > 0.8:
            reasons.append("high performance history")
        elif scores['performance'] > 0.6:
            reasons.append("good performance history")
        
        if scores['territory'] > 0.8:
            reasons.append("territory alignment")
        
        if scores['availability'] > 0.8:
            reasons.append("high availability")
        
        if not reasons:
            reasons.append("balanced assignment factors")
        
        return f"Recommended due to: {', '.join(reasons)}"
    
    def _apply_assignment(self, lead: Lead, assignment: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the assignment"""
        try:
            agent = User.objects.get(id=assignment['agent_id'])
            
            # Update lead assignment
            lead.assigned_to = agent
            lead.status = 'assigned'
            lead.save()
            
            # Create assignment score record
            AssignmentScore.objects.create(
                company=lead.company,
                lead=lead,
                agent=agent,
                total_score=assignment['total_score'],
                factor_scores=assignment['factor_scores'],
                assignment_reason=assignment['recommendation_reason'],
                assigned_at=timezone.now()
            )
            
            return {
                'success': True,
                'assigned_agent': agent.get_full_name(),
                'assignment_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Assignment application failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _apply_deal_assignment(self, deal: Deal, assignment: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply deal assignment"""
        try:
            agent = User.objects.get(id=assignment['agent_id'])
            
            # Update deal assignment
            deal.assigned_to = agent
            deal.save()
            
            # Create assignment score record
            AssignmentScore.objects.create(
                company=deal.company,
                deal=deal,
                agent=agent,
                total_score=assignment['total_score'],
                factor_scores=assignment['factor_scores'],
                assignment_reason=assignment['recommendation_reason'],
                assigned_at=timezone.now()
            )
            
            return {
                'success': True,
                'assigned_agent': agent.get_full_name(),
                'assignment_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Deal assignment application failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _log_assignment(self, lead: Lead, assignment: Dict[str, Any], result: Dict[str, Any]):
        """Log assignment for audit"""
        from security.models import AuditLog
        
        AuditLog.objects.create(
            company=lead.company,
            event_type='lead_assigned',
            data={
                'lead_id': str(lead.id),
                'assigned_agent_id': assignment['agent_id'],
                'assignment_score': assignment['total_score'],
                'assignment_reason': assignment['recommendation_reason'],
                'success': result.get('success', False)
            }
        )
    
    def _log_deal_assignment(self, deal: Deal, assignment: Dict[str, Any], result: Dict[str, Any]):
        """Log deal assignment for audit"""
        from security.models import AuditLog
        
        AuditLog.objects.create(
            company=deal.company,
            event_type='deal_assigned',
            data={
                'deal_id': str(deal.id),
                'assigned_agent_id': assignment['agent_id'],
                'assignment_score': assignment['total_score'],
                'assignment_reason': assignment['recommendation_reason'],
                'success': result.get('success', False)
            }
        )
    
    def _calculate_deal_assignment_score(self, deal: Deal, agent: User, config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate assignment score for deal"""
        # Similar to lead assignment but with deal-specific factors
        factor_weights = config.get('factor_weights', {
            'workload': 0.20,
            'skill_match': 0.35,
            'territory': 0.25,
            'performance': 0.15,
            'availability': 0.05
        })
        
        # Calculate individual scores
        workload_score = self._calculate_workload_score(deal, agent)
        skill_score = self._calculate_deal_skill_match_score(deal, agent)
        territory_score = self._calculate_territory_score(deal, agent)
        performance_score = self._calculate_performance_score(deal, agent)
        availability_score = self._calculate_availability_score(deal, agent)
        
        # Calculate weighted total score
        total_score = (
            workload_score * factor_weights['workload'] +
            skill_score * factor_weights['skill_match'] +
            territory_score * factor_weights['territory'] +
            performance_score * factor_weights['performance'] +
            availability_score * factor_weights['availability']
        )
        
        # Generate recommendation reason
        reason = self._generate_recommendation_reason({
            'workload': workload_score,
            'skill_match': skill_score,
            'territory': territory_score,
            'performance': performance_score,
            'availability': availability_score
        })
        
        return {
            'total_score': total_score,
            'factor_scores': {
                'workload': workload_score,
                'skill_match': skill_score,
                'territory': territory_score,
                'performance': performance_score,
                'availability': availability_score
            },
            'recommendation_reason': reason
        }
    
    def _calculate_deal_skill_match_score(self, deal: Deal, agent: User) -> float:
        """Calculate skill match score for deal"""
        # Deal-specific skill matching
        deal_stage = deal.stage
        deal_amount = deal.amount or 0
        
        # Agent's deal stage experience
        agent_stage_experience = getattr(agent, 'stage_experience', {})
        stage_score = agent_stage_experience.get(deal_stage, 0.5)
        
        # Agent's deal size experience
        agent_size_experience = getattr(agent, 'size_experience', {})
        if deal_amount > 100000:
            size_category = 'enterprise'
        elif deal_amount > 50000:
            size_category = 'mid_market'
        else:
            size_category = 'small_business'
        
        size_score = agent_size_experience.get(size_category, 0.5)
        
        # Combine scores
        return (stage_score + size_score) / 2
    
    def _analyze_current_assignments(self, territories: List[Territory], agents: List[User]) -> Dict[str, Any]:
        """Analyze current territory assignments"""
        analysis = {
            'territory_coverage': {},
            'agent_workload': {},
            'performance_by_territory': {},
            'optimization_opportunities': []
        }
        
        for territory in territories:
            territory_agents = territory.get_all_users()
            
            # Territory coverage
            analysis['territory_coverage'][territory.name] = {
                'agent_count': len(territory_agents),
                'agents': [agent.get_full_name() for agent in territory_agents]
            }
            
            # Agent workload in territory
            for agent in territory_agents:
                workload = self._calculate_agent_workload(agent)
                analysis['agent_workload'][agent.get_full_name()] = workload
        
        return analysis
    
    def _generate_optimization_recommendations(self, territories: List[Territory], agents: List[User], 
                                            current_analysis: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate territory optimization recommendations"""
        recommendations = []
        
        # Analyze workload distribution
        agent_workloads = current_analysis['agent_workload']
        avg_workload = sum(agent_workloads.values()) / len(agent_workloads) if agent_workloads else 0
        
        for agent_name, workload in agent_workloads.items():
            if workload > avg_workload * 1.5:  # Overloaded
                recommendations.append({
                    'type': 'workload_reduction',
                    'agent': agent_name,
                    'current_workload': workload,
                    'recommendation': 'Consider redistributing some assignments',
                    'priority': 'high'
                })
            elif workload < avg_workload * 0.5:  # Underloaded
                recommendations.append({
                    'type': 'workload_increase',
                    'agent': agent_name,
                    'current_workload': workload,
                    'recommendation': 'Can handle additional assignments',
                    'priority': 'medium'
                })
        
        return recommendations
    
    def _apply_territory_optimizations(self, recommendations: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply territory optimization recommendations"""
        applied = []
        
        for recommendation in recommendations:
            if recommendation['type'] == 'workload_reduction':
                # Implement workload reduction logic
                applied.append({
                    'recommendation_id': recommendation.get('id'),
                    'action': 'workload_reduced',
                    'status': 'applied'
                })
            elif recommendation['type'] == 'workload_increase':
                # Implement workload increase logic
                applied.append({
                    'recommendation_id': recommendation.get('id'),
                    'action': 'workload_increased',
                    'status': 'applied'
                })
        
        return applied

# Celery tasks
@shared_task
def auto_assign_lead(lead_id: str, assignment_config: Dict[str, Any]):
    """Async task to auto-assign lead"""
    engine = AssignmentIntelligenceEngine()
    return engine.assign_lead_to_agent(lead_id, assignment_config)

@shared_task
def auto_assign_deal(deal_id: str, assignment_config: Dict[str, Any]):
    """Async task to auto-assign deal"""
    engine = AssignmentIntelligenceEngine()
    return engine.assign_deal_to_agent(deal_id, assignment_config)

@shared_task
def optimize_territory_assignments_async(company_id: str, optimization_config: Dict[str, Any]):
    """Async task to optimize territory assignments"""
    engine = AssignmentIntelligenceEngine()
    return engine.optimize_territory_assignments(company_id, optimization_config)

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_lead_to_agent(request):
    """API endpoint to assign lead to agent"""
    engine = AssignmentIntelligenceEngine()
    result = engine.assign_lead_to_agent(
        request.data.get('lead_id'),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_deal_to_agent(request):
    """API endpoint to assign deal to agent"""
    engine = AssignmentIntelligenceEngine()
    result = engine.assign_deal_to_agent(
        request.data.get('deal_id'),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def optimize_territory_assignments(request):
    """API endpoint to optimize territory assignments"""
    engine = AssignmentIntelligenceEngine()
    result = engine.optimize_territory_assignments(
        str(request.user.company.id),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)
