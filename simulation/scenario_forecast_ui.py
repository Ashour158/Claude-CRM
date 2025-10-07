# simulation/scenario_forecast_ui.py
"""
Scenario Forecast UI Implementation
P3 Priority: Scenario diff adoption (>50% active managers)

This module implements:
- Interactive scenario forecasting UI
- Scenario comparison and analysis
- Manager adoption tracking
- User engagement metrics
- Scenario recommendation engine
"""

import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from core.models import Company, User
from events.event_bus import event_bus
import uuid

logger = logging.getLogger(__name__)

@dataclass
class ScenarioSession:
    """User scenario session"""
    id: str
    user_id: str
    company_id: str
    session_start: timezone.datetime
    session_end: Optional[timezone.datetime] = None
    scenarios_created: int = 0
    scenarios_compared: int = 0
    scenarios_shared: int = 0
    total_time_spent: int = 0  # seconds
    is_active: bool = True

@dataclass
class ScenarioComparison:
    """Scenario comparison result"""
    id: str
    user_id: str
    company_id: str
    scenario_ids: List[str]
    comparison_type: str  # baseline, optimistic, pessimistic
    created_at: timezone.datetime
    insights: Dict[str, Any]
    recommendations: List[str]
    adoption_score: float

@dataclass
class ManagerAdoption:
    """Manager adoption tracking"""
    id: str
    user_id: str
    company_id: str
    adoption_level: str  # low, medium, high
    scenarios_used: int
    comparisons_made: int
    shares_made: int
    last_activity: timezone.datetime
    engagement_score: float

class ScenarioForecastUI:
    """
    Scenario forecast UI with manager adoption tracking
    """
    
    def __init__(self):
        self.scenario_sessions: Dict[str, ScenarioSession] = {}
        self.scenario_comparisons: List[ScenarioComparison] = []
        self.manager_adoptions: Dict[str, ManagerAdoption] = {}
        
        # UI configuration
        self.config = {
            "adoption_threshold": 0.5,  # 50% adoption target
            "engagement_threshold": 0.7,  # 70% engagement threshold
            "session_timeout_minutes": 30,
            "max_scenarios_per_comparison": 5,
            "recommendation_engine_enabled": True
        }
        
        # Adoption tracking
        self.adoption_metrics = {
            "total_managers": 0,
            "active_managers": 0,
            "high_adoption_managers": 0,
            "adoption_rate": 0.0,
            "avg_engagement_score": 0.0
        }
    
    def start_scenario_session(self, user: User, company: Company) -> ScenarioSession:
        """Start a new scenario session for a user"""
        session_id = str(uuid.uuid4())
        
        # End any existing active session
        self._end_active_session(user.id)
        
        session = ScenarioSession(
            id=session_id,
            user_id=str(user.id),
            company_id=str(company.id),
            session_start=timezone.now()
        )
        
        self.scenario_sessions[session_id] = session
        
        # Initialize or update manager adoption
        self._initialize_manager_adoption(user, company)
        
        # Publish session start event
        event_bus.publish(
            event_type='SCENARIO_SESSION_STARTED',
            data={
                'session_id': session_id,
                'user_id': str(user.id),
                'company_id': str(company.id)
            },
            actor=user,
            company_id=company.id
        )
        
        logger.info(f"Scenario session started: {session_id} for user {user.id}")
        return session
    
    def _end_active_session(self, user_id: str):
        """End any active session for a user"""
        for session in self.scenario_sessions.values():
            if session.user_id == str(user_id) and session.is_active:
                session.is_active = False
                session.session_end = timezone.now()
                session.total_time_spent = (session.session_end - session.session_start).total_seconds()
                break
    
    def _initialize_manager_adoption(self, user: User, company: Company):
        """Initialize manager adoption tracking"""
        user_id = str(user.id)
        
        if user_id not in self.manager_adoptions:
            self.manager_adoptions[user_id] = ManagerAdoption(
                id=str(uuid.uuid4()),
                user_id=user_id,
                company_id=str(company.id),
                adoption_level="low",
                scenarios_used=0,
                comparisons_made=0,
                shares_made=0,
                last_activity=timezone.now(),
                engagement_score=0.0
            )
    
    def create_scenario(self, session_id: str, scenario_name: str, 
                       scenario_type: str, parameters: Dict[str, Any],
                       user: User) -> Dict[str, Any]:
        """Create a new scenario in a session"""
        if session_id not in self.scenario_sessions:
            raise ValueError(f"Session not found: {session_id}")
        
        session = self.scenario_sessions[session_id]
        if not session.is_active:
            raise ValueError(f"Session is not active: {session_id}")
        
        # Create scenario (mock implementation)
        scenario_id = str(uuid.uuid4())
        scenario_data = {
            "id": scenario_id,
            "name": scenario_name,
            "type": scenario_type,
            "parameters": parameters,
            "created_at": timezone.now().isoformat(),
            "created_by": str(user.id),
            "status": "created"
        }
        
        # Update session metrics
        session.scenarios_created += 1
        
        # Update manager adoption
        self._update_manager_adoption(user.id, "scenario_created")
        
        # Publish scenario creation event
        event_bus.publish(
            event_type='SCENARIO_CREATED',
            data={
                'scenario_id': scenario_id,
                'session_id': session_id,
                'scenario_name': scenario_name,
                'scenario_type': scenario_type
            },
            actor=user,
            company_id=user.company.id
        )
        
        logger.info(f"Scenario created: {scenario_id} ({scenario_name})")
        return scenario_data
    
    def compare_scenarios(self, session_id: str, scenario_ids: List[str],
                         comparison_type: str, user: User) -> ScenarioComparison:
        """Compare multiple scenarios"""
        if session_id not in self.scenario_sessions:
            raise ValueError(f"Session not found: {session_id}")
        
        session = self.scenario_sessions[session_id]
        if not session.is_active:
            raise ValueError(f"Session is not active: {session_id}")
        
        if len(scenario_ids) < 2:
            raise ValueError("At least 2 scenarios required for comparison")
        
        if len(scenario_ids) > self.config["max_scenarios_per_comparison"]:
            raise ValueError(f"Maximum {self.config['max_scenarios_per_comparison']} scenarios allowed")
        
        # Generate comparison insights
        insights = self._generate_comparison_insights(scenario_ids, comparison_type)
        recommendations = self._generate_recommendations(insights, comparison_type)
        
        # Create comparison result
        comparison = ScenarioComparison(
            id=str(uuid.uuid4()),
            user_id=str(user.id),
            company_id=str(user.company.id),
            scenario_ids=scenario_ids,
            comparison_type=comparison_type,
            created_at=timezone.now(),
            insights=insights,
            recommendations=recommendations,
            adoption_score=self._calculate_adoption_score(insights)
        )
        
        self.scenario_comparisons.append(comparison)
        
        # Update session metrics
        session.scenarios_compared += 1
        
        # Update manager adoption
        self._update_manager_adoption(user.id, "comparison_made")
        
        # Publish comparison event
        event_bus.publish(
            event_type='SCENARIO_COMPARISON_CREATED',
            data={
                'comparison_id': comparison.id,
                'session_id': session_id,
                'scenario_count': len(scenario_ids),
                'comparison_type': comparison_type,
                'adoption_score': comparison.adoption_score
            },
            actor=user,
            company_id=user.company.id
        )
        
        logger.info(f"Scenario comparison created: {comparison.id} ({len(scenario_ids)} scenarios)")
        return comparison
    
    def _generate_comparison_insights(self, scenario_ids: List[str], 
                                    comparison_type: str) -> Dict[str, Any]:
        """Generate insights from scenario comparison"""
        # Mock implementation - in real scenario, this would analyze actual scenario data
        insights = {
            "scenario_count": len(scenario_ids),
            "comparison_type": comparison_type,
            "key_differences": [
                "Revenue variance: 15%",
                "Cost impact: 8%",
                "Risk level: Medium"
            ],
            "best_scenario": scenario_ids[0] if scenario_ids else None,
            "worst_scenario": scenario_ids[-1] if scenario_ids else None,
            "confidence_score": 0.85,
            "analysis_timestamp": timezone.now().isoformat()
        }
        
        return insights
    
    def _generate_recommendations(self, insights: Dict[str, Any], 
                                comparison_type: str) -> List[str]:
        """Generate recommendations based on comparison insights"""
        recommendations = []
        
        if insights.get("confidence_score", 0) > 0.8:
            recommendations.append("High confidence in scenario analysis - proceed with recommended scenario")
        
        if comparison_type == "baseline":
            recommendations.append("Consider running optimistic and pessimistic scenarios for risk assessment")
        elif comparison_type == "optimistic":
            recommendations.append("Optimistic scenario shows potential - consider resource allocation")
        elif comparison_type == "pessimistic":
            recommendations.append("Pessimistic scenario indicates risks - develop mitigation strategies")
        
        if insights.get("scenario_count", 0) > 3:
            recommendations.append("Multiple scenarios analyzed - consider scenario portfolio approach")
        
        return recommendations
    
    def _calculate_adoption_score(self, insights: Dict[str, Any]) -> float:
        """Calculate adoption score based on insights"""
        # Base score from confidence
        base_score = insights.get("confidence_score", 0.5)
        
        # Bonus for multiple scenarios
        scenario_count = insights.get("scenario_count", 1)
        scenario_bonus = min(0.2, (scenario_count - 1) * 0.05)
        
        # Bonus for detailed analysis
        analysis_bonus = 0.1 if len(insights.get("key_differences", [])) > 2 else 0.0
        
        return min(1.0, base_score + scenario_bonus + analysis_bonus)
    
    def share_scenario(self, session_id: str, scenario_id: str, 
                      share_type: str, recipients: List[str], user: User) -> Dict[str, Any]:
        """Share a scenario with other users"""
        if session_id not in self.scenario_sessions:
            raise ValueError(f"Session not found: {session_id}")
        
        session = self.scenario_sessions[session_id]
        if not session.is_active:
            raise ValueError(f"Session is not active: {session_id}")
        
        # Create share record
        share_id = str(uuid.uuid4())
        share_data = {
            "id": share_id,
            "scenario_id": scenario_id,
            "session_id": session_id,
            "share_type": share_type,
            "recipients": recipients,
            "shared_by": str(user.id),
            "shared_at": timezone.now().isoformat(),
            "status": "shared"
        }
        
        # Update session metrics
        session.scenarios_shared += 1
        
        # Update manager adoption
        self._update_manager_adoption(user.id, "scenario_shared")
        
        # Publish share event
        event_bus.publish(
            event_type='SCENARIO_SHARED',
            data={
                'share_id': share_id,
                'scenario_id': scenario_id,
                'share_type': share_type,
                'recipient_count': len(recipients)
            },
            actor=user,
            company_id=user.company.id
        )
        
        logger.info(f"Scenario shared: {scenario_id} with {len(recipients)} recipients")
        return share_data
    
    def _update_manager_adoption(self, user_id: str, action: str):
        """Update manager adoption metrics"""
        if user_id not in self.manager_adoptions:
            return
        
        adoption = self.manager_adoptions[user_id]
        adoption.last_activity = timezone.now()
        
        if action == "scenario_created":
            adoption.scenarios_used += 1
        elif action == "comparison_made":
            adoption.comparisons_made += 1
        elif action == "scenario_shared":
            adoption.shares_made += 1
        
        # Calculate engagement score
        adoption.engagement_score = self._calculate_engagement_score(adoption)
        
        # Update adoption level
        if adoption.engagement_score >= 0.8:
            adoption.adoption_level = "high"
        elif adoption.engagement_score >= 0.5:
            adoption.adoption_level = "medium"
        else:
            adoption.adoption_level = "low"
    
    def _calculate_engagement_score(self, adoption: ManagerAdoption) -> float:
        """Calculate engagement score for a manager"""
        # Weighted scoring based on different activities
        scenario_weight = 0.3
        comparison_weight = 0.4
        share_weight = 0.3
        
        # Normalize scores (assuming max values for normalization)
        scenario_score = min(1.0, adoption.scenarios_used / 10.0)
        comparison_score = min(1.0, adoption.comparisons_made / 5.0)
        share_score = min(1.0, adoption.shares_made / 3.0)
        
        engagement_score = (
            scenario_score * scenario_weight +
            comparison_score * comparison_weight +
            share_score * share_weight
        )
        
        return min(1.0, engagement_score)
    
    def end_scenario_session(self, session_id: str, user: User) -> Dict[str, Any]:
        """End a scenario session"""
        if session_id not in self.scenario_sessions:
            raise ValueError(f"Session not found: {session_id}")
        
        session = self.scenario_sessions[session_id]
        if not session.is_active:
            raise ValueError(f"Session is not active: {session_id}")
        
        # End session
        session.is_active = False
        session.session_end = timezone.now()
        session.total_time_spent = (session.session_end - session.session_start).total_seconds()
        
        # Update manager adoption
        self._update_manager_adoption(user.id, "session_ended")
        
        # Publish session end event
        event_bus.publish(
            event_type='SCENARIO_SESSION_ENDED',
            data={
                'session_id': session_id,
                'user_id': str(user.id),
                'scenarios_created': session.scenarios_created,
                'scenarios_compared': session.scenarios_compared,
                'scenarios_shared': session.scenarios_shared,
                'total_time_spent': session.total_time_spent
            },
            actor=user,
            company_id=user.company.id
        )
        
        logger.info(f"Scenario session ended: {session_id} ({session.total_time_spent:.0f}s)")
        return {
            "session_id": session_id,
            "scenarios_created": session.scenarios_created,
            "scenarios_compared": session.scenarios_compared,
            "scenarios_shared": session.scenarios_shared,
            "total_time_spent": session.total_time_spent
        }
    
    def get_adoption_metrics(self, company: Company, 
                            lookback_days: int = 30) -> Dict[str, Any]:
        """Get scenario adoption metrics for a company"""
        cutoff_date = timezone.now() - timedelta(days=lookback_days)
        
        # Filter data by company and time
        company_sessions = [
            session for session in self.scenario_sessions.values()
            if session.company_id == str(company.id) and session.session_start >= cutoff_date
        ]
        
        company_adoptions = [
            adoption for adoption in self.manager_adoptions.values()
            if adoption.company_id == str(company.id) and adoption.last_activity >= cutoff_date
        ]
        
        if not company_sessions and not company_adoptions:
            return {"status": "no_data", "message": "No scenario data available"}
        
        # Calculate adoption metrics
        total_managers = len(company_adoptions)
        active_managers = len([a for a in company_adoptions if a.last_activity >= cutoff_date])
        high_adoption_managers = len([a for a in company_adoptions if a.adoption_level == "high"])
        
        adoption_rate = high_adoption_managers / total_managers if total_managers > 0 else 0
        avg_engagement_score = sum(a.engagement_score for a in company_adoptions) / total_managers if total_managers > 0 else 0
        
        # Calculate session metrics
        total_sessions = len(company_sessions)
        total_scenarios_created = sum(session.scenarios_created for session in company_sessions)
        total_comparisons = sum(session.scenarios_compared for session in company_sessions)
        total_shares = sum(session.scenarios_shared for session in company_sessions)
        
        return {
            "company_id": str(company.id),
            "period_days": lookback_days,
            "total_managers": total_managers,
            "active_managers": active_managers,
            "high_adoption_managers": high_adoption_managers,
            "adoption_rate": adoption_rate,
            "target_met": adoption_rate >= self.config["adoption_threshold"],
            "avg_engagement_score": avg_engagement_score,
            "total_sessions": total_sessions,
            "total_scenarios_created": total_scenarios_created,
            "total_comparisons": total_comparisons,
            "total_shares": total_shares,
            "avg_scenarios_per_session": total_scenarios_created / total_sessions if total_sessions > 0 else 0,
            "adoption_levels": {
                "high": len([a for a in company_adoptions if a.adoption_level == "high"]),
                "medium": len([a for a in company_adoptions if a.adoption_level == "medium"]),
                "low": len([a for a in company_adoptions if a.adoption_level == "low"])
            }
        }
    
    def get_user_engagement(self, user: User, 
                           lookback_days: int = 30) -> Dict[str, Any]:
        """Get user engagement metrics"""
        cutoff_date = timezone.now() - timedelta(days=lookback_days)
        
        # Get user sessions
        user_sessions = [
            session for session in self.scenario_sessions.values()
            if session.user_id == str(user.id) and session.session_start >= cutoff_date
        ]
        
        # Get user adoption
        user_adoption = self.manager_adoptions.get(str(user.id))
        
        if not user_sessions and not user_adoption:
            return {"status": "no_data", "message": "No user data available"}
        
        # Calculate engagement metrics
        total_sessions = len(user_sessions)
        total_scenarios = sum(session.scenarios_created for session in user_sessions)
        total_comparisons = sum(session.scenarios_compared for session in user_sessions)
        total_shares = sum(session.scenarios_shared for session in user_sessions)
        
        # Calculate time spent
        total_time_spent = sum(session.total_time_spent for session in user_sessions)
        avg_session_time = total_time_spent / total_sessions if total_sessions > 0 else 0
        
        return {
            "user_id": str(user.id),
            "period_days": lookback_days,
            "total_sessions": total_sessions,
            "total_scenarios": total_scenarios,
            "total_comparisons": total_comparisons,
            "total_shares": total_shares,
            "total_time_spent": total_time_spent,
            "avg_session_time": avg_session_time,
            "adoption_level": user_adoption.adoption_level if user_adoption else "low",
            "engagement_score": user_adoption.engagement_score if user_adoption else 0.0,
            "last_activity": user_adoption.last_activity.isoformat() if user_adoption else None
        }
    
    def get_recommendations(self, user: User, company: Company) -> List[Dict[str, Any]]:
        """Get personalized recommendations for scenario usage"""
        user_adoption = self.manager_adoptions.get(str(user.id))
        
        if not user_adoption:
            return [{"type": "onboarding", "message": "Start by creating your first scenario"}]
        
        recommendations = []
        
        # Based on adoption level
        if user_adoption.adoption_level == "low":
            recommendations.append({
                "type": "scenario_creation",
                "message": "Try creating different types of scenarios (optimistic, pessimistic, baseline)",
                "priority": "high"
            })
        elif user_adoption.adoption_level == "medium":
            recommendations.append({
                "type": "scenario_comparison",
                "message": "Compare multiple scenarios to gain deeper insights",
                "priority": "medium"
            })
        else:  # high
            recommendations.append({
                "type": "scenario_sharing",
                "message": "Share scenarios with your team to collaborate on planning",
                "priority": "low"
            })
        
        # Based on engagement score
        if user_adoption.engagement_score < 0.5:
            recommendations.append({
                "type": "engagement",
                "message": "Explore different scenario parameters to increase engagement",
                "priority": "high"
            })
        
        # Based on activity patterns
        if user_adoption.scenarios_used > 0 and user_adoption.comparisons_made == 0:
            recommendations.append({
                "type": "comparison",
                "message": "Try comparing scenarios to see the impact of different assumptions",
                "priority": "medium"
            })
        
        return recommendations

# Global instance
scenario_forecast_ui = ScenarioForecastUI()
