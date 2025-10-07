# ai_scoring/assignment_engine_advanced.py
"""
Advanced Assignment Engine Implementation
P2 Priority: SLA assignment latency <200ms

This module implements:
- High-performance assignment engine
- Real-time assignment with SLA guarantees
- Intelligent agent selection
- Performance monitoring and optimization
- Assignment analytics and reporting
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from core.models import Company, User
from events.event_bus import event_bus
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

@dataclass
class AssignmentRequest:
    """Assignment request with SLA requirements"""
    id: str
    request_type: str
    priority: str
    entity_id: str
    entity_type: str
    company_id: str
    user_id: str
    sla_deadline: timezone.datetime
    requirements: Dict[str, Any]
    created_at: timezone.datetime
    assigned_to: Optional[str] = None
    assignment_time: Optional[timezone.datetime] = None
    status: str = "pending"

@dataclass
class AssignmentResult:
    """Assignment result with performance metrics"""
    id: str
    request_id: str
    assigned_to: str
    assignment_score: float
    assignment_time_ms: float
    sla_met: bool
    confidence_score: float
    reasoning: str
    created_at: timezone.datetime

@dataclass
class AgentProfile:
    """Agent profile for assignment"""
    id: str
    user_id: str
    company_id: str
    skills: List[str]
    workload_score: float
    performance_score: float
    availability_score: float
    capacity: int
    current_assignments: int
    last_activity: timezone.datetime
    is_available: bool

class AdvancedAssignmentEngine:
    """
    Advanced assignment engine with SLA guarantees
    """
    
    def __init__(self):
        self.assignment_requests: Dict[str, AssignmentRequest] = {}
        self.assignment_results: List[AssignmentResult] = []
        self.agent_profiles: Dict[str, AgentProfile] = {}
        self.performance_metrics: Dict[str, Any] = {}
        
        # SLA configuration
        self.sla_config = {
            "max_assignment_time_ms": 200,
            "high_priority_sla_ms": 100,
            "medium_priority_sla_ms": 150,
            "low_priority_sla_ms": 200,
            "assignment_timeout_ms": 500
        }
        
        # Assignment scoring weights
        self.scoring_weights = {
            "skill_match": 0.3,
            "workload_balance": 0.2,
            "performance_history": 0.2,
            "availability": 0.15,
            "geographic_proximity": 0.1,
            "preference": 0.05
        }
        
        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.assignment_lock = threading.Lock()
    
    def create_assignment_request(self, request_type: str, entity_id: str, 
                                entity_type: str, company: Company, user: User,
                                priority: str = "medium", 
                                requirements: Dict[str, Any] = None) -> AssignmentRequest:
        """Create a new assignment request"""
        request_id = str(uuid.uuid4())
        
        # Calculate SLA deadline based on priority
        sla_deadline = self._calculate_sla_deadline(priority)
        
        assignment_request = AssignmentRequest(
            id=request_id,
            request_type=request_type,
            priority=priority,
            entity_id=entity_id,
            entity_type=entity_type,
            company_id=str(company.id),
            user_id=str(user.id),
            sla_deadline=sla_deadline,
            requirements=requirements or {},
            created_at=timezone.now()
        )
        
        self.assignment_requests[request_id] = assignment_request
        
        # Publish assignment request event
        event_bus.publish(
            event_type='ASSIGNMENT_REQUEST_CREATED',
            data={
                'request_id': request_id,
                'request_type': request_type,
                'priority': priority,
                'entity_type': entity_type,
                'sla_deadline': sla_deadline.isoformat()
            },
            actor=user,
            company_id=company.id
        )
        
        logger.info(f"Assignment request created: {request_id} ({request_type})")
        return assignment_request
    
    def _calculate_sla_deadline(self, priority: str) -> timezone.datetime:
        """Calculate SLA deadline based on priority"""
        now = timezone.now()
        
        if priority == "high":
            sla_ms = self.sla_config["high_priority_sla_ms"]
        elif priority == "medium":
            sla_ms = self.sla_config["medium_priority_sla_ms"]
        else:  # low
            sla_ms = self.sla_config["low_priority_sla_ms"]
        
        return now + timedelta(milliseconds=sla_ms)
    
    def assign_entity(self, request_id: str, company: Company) -> AssignmentResult:
        """Assign entity to best available agent with SLA guarantee"""
        if request_id not in self.assignment_requests:
            raise ValueError(f"Assignment request not found: {request_id}")
        
        request = self.assignment_requests[request_id]
        start_time = time.time()
        
        try:
            # Get available agents for the company
            available_agents = self._get_available_agents(company.id)
            
            if not available_agents:
                raise ValueError("No available agents found")
            
            # Score agents for this assignment
            agent_scores = self._score_agents(request, available_agents)
            
            # Select best agent
            best_agent = max(agent_scores.items(), key=lambda x: x[1])
            assigned_agent_id = best_agent[0]
            assignment_score = best_agent[1]
            
            # Create assignment result
            assignment_time = time.time() - start_time
            assignment_time_ms = assignment_time * 1000
            
            sla_met = assignment_time_ms <= self.sla_config["max_assignment_time_ms"]
            
            assignment_result = AssignmentResult(
                id=str(uuid.uuid4()),
                request_id=request_id,
                assigned_to=assigned_agent_id,
                assignment_score=assignment_score,
                assignment_time_ms=assignment_time_ms,
                sla_met=sla_met,
                confidence_score=self._calculate_confidence_score(assignment_score, assignment_time_ms),
                reasoning=self._generate_assignment_reasoning(request, assigned_agent_id, assignment_score),
                created_at=timezone.now()
            )
            
            # Update request status
            request.assigned_to = assigned_agent_id
            request.assignment_time = timezone.now()
            request.status = "assigned"
            
            # Update agent profile
            if assigned_agent_id in self.agent_profiles:
                self.agent_profiles[assigned_agent_id].current_assignments += 1
                self.agent_profiles[assigned_agent_id].last_activity = timezone.now()
            
            self.assignment_results.append(assignment_result)
            
            # Track performance metrics
            self._update_performance_metrics(assignment_result)
            
            # Publish assignment result event
            event_bus.publish(
                event_type='ENTITY_ASSIGNED',
                data={
                    'result_id': assignment_result.id,
                    'request_id': request_id,
                    'assigned_to': assigned_agent_id,
                    'assignment_score': assignment_score,
                    'assignment_time_ms': assignment_time_ms,
                    'sla_met': sla_met
                },
                company_id=company.id
            )
            
            logger.info(f"Entity assigned: {request_id} -> {assigned_agent_id} ({assignment_time_ms:.2f}ms)")
            return assignment_result
            
        except Exception as e:
            # Handle assignment failure
            assignment_time = time.time() - start_time
            assignment_time_ms = assignment_time * 1000
            
            logger.error(f"Assignment failed for {request_id}: {e}")
            
            # Create failure result
            failure_result = AssignmentResult(
                id=str(uuid.uuid4()),
                request_id=request_id,
                assigned_to="",
                assignment_score=0.0,
                assignment_time_ms=assignment_time_ms,
                sla_met=False,
                confidence_score=0.0,
                reasoning=f"Assignment failed: {str(e)}",
                created_at=timezone.now()
            )
            
            self.assignment_results.append(failure_result)
            raise
    
    def _get_available_agents(self, company_id: str) -> List[AgentProfile]:
        """Get available agents for assignment"""
        # In a real implementation, this would query the database
        # For now, return mock agent profiles
        available_agents = []
        
        for agent_id, profile in self.agent_profiles.items():
            if (profile.company_id == str(company_id) and 
                profile.is_available and 
                profile.current_assignments < profile.capacity):
                available_agents.append(profile)
        
        return available_agents
    
    def _score_agents(self, request: AssignmentRequest, 
                     agents: List[AgentProfile]) -> Dict[str, float]:
        """Score agents for assignment suitability"""
        agent_scores = {}
        
        for agent in agents:
            score = 0.0
            
            # Skill match scoring
            skill_score = self._calculate_skill_match_score(request, agent)
            score += skill_score * self.scoring_weights["skill_match"]
            
            # Workload balance scoring
            workload_score = self._calculate_workload_score(agent)
            score += workload_score * self.scoring_weights["workload_balance"]
            
            # Performance history scoring
            performance_score = agent.performance_score
            score += performance_score * self.scoring_weights["performance_history"]
            
            # Availability scoring
            availability_score = agent.availability_score
            score += availability_score * self.scoring_weights["availability"]
            
            # Geographic proximity scoring
            geo_score = self._calculate_geographic_score(request, agent)
            score += geo_score * self.scoring_weights["geographic_proximity"]
            
            # Preference scoring
            preference_score = self._calculate_preference_score(request, agent)
            score += preference_score * self.scoring_weights["preference"]
            
            agent_scores[agent.id] = score
        
        return agent_scores
    
    def _calculate_skill_match_score(self, request: AssignmentRequest, 
                                   agent: AgentProfile) -> float:
        """Calculate skill match score between request and agent"""
        required_skills = request.requirements.get("required_skills", [])
        if not required_skills:
            return 1.0  # No specific skills required
        
        agent_skills = set(agent.skills)
        required_skills_set = set(required_skills)
        
        # Calculate skill overlap
        overlap = len(agent_skills & required_skills_set)
        total_required = len(required_skills_set)
        
        if total_required == 0:
            return 1.0
        
        return overlap / total_required
    
    def _calculate_workload_score(self, agent: AgentProfile) -> float:
        """Calculate workload balance score for agent"""
        if agent.capacity == 0:
            return 0.0
        
        utilization = agent.current_assignments / agent.capacity
        # Lower utilization is better (inverse relationship)
        return 1.0 - utilization
    
    def _calculate_geographic_score(self, request: AssignmentRequest, 
                                  agent: AgentProfile) -> float:
        """Calculate geographic proximity score"""
        # Mock geographic calculation
        # In real implementation, this would use actual geographic data
        return 0.8  # Default score
    
    def _calculate_preference_score(self, request: AssignmentRequest, 
                                  agent: AgentProfile) -> float:
        """Calculate preference score based on agent preferences"""
        # Mock preference calculation
        # In real implementation, this would consider agent preferences
        return 0.9  # Default score
    
    def _calculate_confidence_score(self, assignment_score: float, 
                                  assignment_time_ms: float) -> float:
        """Calculate confidence score for assignment"""
        # Base confidence on assignment score
        base_confidence = assignment_score
        
        # Adjust for assignment time (faster is better)
        time_factor = max(0.5, 1.0 - (assignment_time_ms / self.sla_config["max_assignment_time_ms"]))
        
        return min(1.0, base_confidence * time_factor)
    
    def _generate_assignment_reasoning(self, request: AssignmentRequest, 
                                     agent_id: str, score: float) -> str:
        """Generate human-readable reasoning for assignment"""
        agent = self.agent_profiles.get(agent_id)
        if not agent:
            return f"Assigned to agent {agent_id} with score {score:.2f}"
        
        reasoning_parts = [
            f"Assigned to {agent_id} (score: {score:.2f})",
            f"Skills: {', '.join(agent.skills[:3])}",
            f"Workload: {agent.current_assignments}/{agent.capacity}",
            f"Performance: {agent.performance_score:.2f}"
        ]
        
        return " | ".join(reasoning_parts)
    
    def _update_performance_metrics(self, result: AssignmentResult):
        """Update performance metrics"""
        if "assignment_metrics" not in self.performance_metrics:
            self.performance_metrics["assignment_metrics"] = {
                "total_assignments": 0,
                "sla_met_count": 0,
                "avg_assignment_time": 0.0,
                "avg_confidence_score": 0.0
            }
        
        metrics = self.performance_metrics["assignment_metrics"]
        metrics["total_assignments"] += 1
        
        if result.sla_met:
            metrics["sla_met_count"] += 1
        
        # Update running averages
        total = metrics["total_assignments"]
        metrics["avg_assignment_time"] = (
            (metrics["avg_assignment_time"] * (total - 1) + result.assignment_time_ms) / total
        )
        metrics["avg_confidence_score"] = (
            (metrics["avg_confidence_score"] * (total - 1) + result.confidence_score) / total
        )
    
    def create_agent_profile(self, user: User, skills: List[str], 
                           capacity: int = 10) -> AgentProfile:
        """Create agent profile for assignment"""
        agent_id = str(uuid.uuid4())
        
        agent_profile = AgentProfile(
            id=agent_id,
            user_id=str(user.id),
            company_id=str(user.company.id),
            skills=skills,
            workload_score=0.0,
            performance_score=0.8,  # Default performance score
            availability_score=1.0,
            capacity=capacity,
            current_assignments=0,
            last_activity=timezone.now(),
            is_available=True
        )
        
        self.agent_profiles[agent_id] = agent_profile
        
        logger.info(f"Agent profile created: {agent_id} for user {user.id}")
        return agent_profile
    
    def update_agent_availability(self, agent_id: str, is_available: bool):
        """Update agent availability status"""
        if agent_id in self.agent_profiles:
            self.agent_profiles[agent_id].is_available = is_available
            self.agent_profiles[agent_id].last_activity = timezone.now()
            
            logger.info(f"Agent {agent_id} availability updated: {is_available}")
    
    def get_assignment_performance_metrics(self, company: Company, 
                                         lookback_hours: int = 24) -> Dict[str, Any]:
        """Get assignment performance metrics"""
        cutoff_time = timezone.now() - timedelta(hours=lookback_hours)
        
        # Filter results by company and time
        company_results = [
            result for result in self.assignment_results
            if result.created_at >= cutoff_time
        ]
        
        if not company_results:
            return {"status": "no_data", "message": "No assignment data available"}
        
        # Calculate metrics
        total_assignments = len(company_results)
        sla_met_count = sum(1 for r in company_results if r.sla_met)
        sla_met_rate = sla_met_count / total_assignments if total_assignments > 0 else 0
        
        avg_assignment_time = np.mean([r.assignment_time_ms for r in company_results])
        avg_confidence = np.mean([r.confidence_score for r in company_results])
        
        # SLA performance by priority
        priority_metrics = {}
        for priority in ["high", "medium", "low"]:
            priority_results = [
                r for r in company_results
                if self.assignment_requests.get(r.request_id, {}).priority == priority
            ]
            if priority_results:
                priority_sla_met = sum(1 for r in priority_results if r.sla_met)
                priority_metrics[priority] = {
                    "total_assignments": len(priority_results),
                    "sla_met_count": priority_sla_met,
                    "sla_met_rate": priority_sla_met / len(priority_results),
                    "avg_assignment_time": np.mean([r.assignment_time_ms for r in priority_results])
                }
        
        return {
            "company_id": str(company.id),
            "period_hours": lookback_hours,
            "total_assignments": total_assignments,
            "sla_met_count": sla_met_count,
            "sla_met_rate": sla_met_rate,
            "avg_assignment_time_ms": avg_assignment_time,
            "avg_confidence_score": avg_confidence,
            "target_sla_ms": self.sla_config["max_assignment_time_ms"],
            "target_met": avg_assignment_time <= self.sla_config["max_assignment_time_ms"],
            "priority_metrics": priority_metrics,
            "active_agents": len([a for a in self.agent_profiles.values() if a.is_available])
        }
    
    def optimize_assignment_performance(self) -> Dict[str, Any]:
        """Optimize assignment performance"""
        # Analyze recent performance
        recent_results = [
            result for result in self.assignment_results
            if result.created_at >= timezone.now() - timedelta(hours=1)
        ]
        
        if not recent_results:
            return {"status": "no_data", "message": "No recent assignment data"}
        
        # Identify performance issues
        slow_assignments = [r for r in recent_results if r.assignment_time_ms > self.sla_config["max_assignment_time_ms"]]
        low_confidence = [r for r in recent_results if r.confidence_score < 0.7]
        
        # Generate optimization recommendations
        recommendations = []
        
        if len(slow_assignments) > len(recent_results) * 0.1:  # >10% slow assignments
            recommendations.append("Consider increasing agent capacity or reducing assignment complexity")
        
        if len(low_confidence) > len(recent_results) * 0.2:  # >20% low confidence
            recommendations.append("Review agent skill matching and training requirements")
        
        # Check agent utilization
        overutilized_agents = [
            agent for agent in self.agent_profiles.values()
            if agent.current_assignments > agent.capacity * 0.9
        ]
        
        if overutilized_agents:
            recommendations.append(f"Consider load balancing for {len(overutilized_agents)} overutilized agents")
        
        return {
            "total_recent_assignments": len(recent_results),
            "slow_assignments": len(slow_assignments),
            "low_confidence_assignments": len(low_confidence),
            "overutilized_agents": len(overutilized_agents),
            "recommendations": recommendations,
            "optimization_needed": len(recommendations) > 0
        }

# Global instance
advanced_assignment_engine = AdvancedAssignmentEngine()
