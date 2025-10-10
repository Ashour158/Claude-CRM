# core/ai_insights.py
# AI insights and recommendations - Phase 9

from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class AIInsightsService:
    """AI-powered insights and recommendations"""
    
    @staticmethod
    def get_lead_scoring(lead):
        """Calculate lead score based on various factors"""
        score = 0
        factors = []
        
        # Email domain scoring
        if lead.email:
            domain = lead.email.split('@')[1] if '@' in lead.email else ''
            if domain in ['gmail.com', 'yahoo.com', 'hotmail.com']:
                score += 5
                factors.append("Personal email domain (+5)")
            else:
                score += 15
                factors.append("Business email domain (+15)")
        
        # Company size indicator
        if hasattr(lead, 'company') and lead.company:
            score += 10
            factors.append("Company associated (+10)")
        
        # Title/Position scoring
        if hasattr(lead, 'title') and lead.title:
            title_lower = lead.title.lower()
            if any(x in title_lower for x in ['ceo', 'cto', 'cfo', 'director', 'vp']):
                score += 20
                factors.append("Decision maker title (+20)")
            elif any(x in title_lower for x in ['manager', 'lead', 'head']):
                score += 10
                factors.append("Manager level title (+10)")
        
        # Activity engagement
        if hasattr(lead, 'activities'):
            activity_count = lead.activities.count() if hasattr(lead.activities, 'count') else 0
            if activity_count > 5:
                score += 15
                factors.append("High engagement (+15)")
            elif activity_count > 2:
                score += 10
                factors.append("Medium engagement (+10)")
        
        # Time-based scoring (recent leads are hotter)
        if lead.created_at:
            days_old = (timezone.now() - lead.created_at).days
            if days_old < 7:
                score += 10
                factors.append("Recent lead (+10)")
            elif days_old < 30:
                score += 5
                factors.append("Moderately recent (+5)")
        
        # Cap score at 100
        score = min(score, 100)
        
        return {
            'score': score,
            'grade': 'A' if score >= 80 else 'B' if score >= 60 else 'C' if score >= 40 else 'D',
            'factors': factors,
            'recommendation': AIInsightsService._get_lead_recommendation(score)
        }
    
    @staticmethod
    def _get_lead_recommendation(score):
        """Get recommendation based on lead score"""
        if score >= 80:
            return "High priority - Contact immediately"
        elif score >= 60:
            return "Good potential - Follow up within 24 hours"
        elif score >= 40:
            return "Moderate potential - Follow up within 3 days"
        else:
            return "Low priority - Nurture campaign recommended"
    
    @staticmethod
    def get_deal_health_analysis(deal):
        """Analyze deal health and predict outcome"""
        health_score = 50  # Base score
        indicators = []
        risks = []
        
        # Stage progression analysis
        if hasattr(deal, 'created_at'):
            days_in_stage = (timezone.now() - deal.created_at).days
            avg_days_in_stage = 30  # Could be calculated from historical data
            
            if days_in_stage > avg_days_in_stage * 2:
                health_score -= 15
                risks.append("Deal stalled - exceeds average time in stage")
            elif days_in_stage < avg_days_in_stage / 2:
                health_score += 10
                indicators.append("Moving quickly through pipeline")
        
        # Amount validation
        if deal.amount:
            if deal.amount > 100000:
                health_score += 5
                indicators.append("High value deal")
            elif deal.amount < 5000:
                health_score -= 5
                risks.append("Low value deal")
        
        # Engagement level
        if hasattr(deal, 'activities'):
            activity_count = deal.activities.count() if hasattr(deal.activities, 'count') else 0
            if activity_count > 10:
                health_score += 15
                indicators.append("High engagement")
            elif activity_count < 3:
                health_score -= 10
                risks.append("Low engagement")
        
        # Account relationship
        if hasattr(deal, 'account') and deal.account:
            # Check if account has other won deals
            health_score += 10
            indicators.append("Existing account relationship")
        
        # Probability alignment
        if hasattr(deal, 'probability') and deal.probability:
            if deal.stage == 'negotiation' and deal.probability < 70:
                health_score -= 10
                risks.append("Low probability for advanced stage")
        
        health_score = max(0, min(100, health_score))
        
        return {
            'health_score': health_score,
            'status': 'Healthy' if health_score >= 70 else 'At Risk' if health_score >= 40 else 'Critical',
            'positive_indicators': indicators,
            'risk_factors': risks,
            'win_probability': AIInsightsService._calculate_win_probability(deal, health_score),
            'recommended_actions': AIInsightsService._get_deal_recommendations(health_score, risks)
        }
    
    @staticmethod
    def _calculate_win_probability(deal, health_score):
        """Calculate deal win probability"""
        base_probability = 50
        
        # Adjust based on health score
        probability_adjustment = (health_score - 50) * 0.5
        probability = base_probability + probability_adjustment
        
        # Stage-based adjustments
        stage_probabilities = {
            'prospecting': 10,
            'qualification': 25,
            'proposal': 50,
            'negotiation': 75,
            'closed_won': 100,
            'closed_lost': 0,
        }
        
        if deal.stage in stage_probabilities:
            probability = (probability + stage_probabilities[deal.stage]) / 2
        
        return max(0, min(100, round(probability)))
    
    @staticmethod
    def _get_deal_recommendations(health_score, risks):
        """Get recommendations for deal"""
        recommendations = []
        
        if health_score < 40:
            recommendations.append("Schedule urgent meeting with stakeholders")
            recommendations.append("Review and address all concerns")
        
        if health_score < 70:
            recommendations.append("Increase engagement frequency")
            recommendations.append("Provide value-added content")
        
        if "Deal stalled" in str(risks):
            recommendations.append("Re-engage with decision maker")
            recommendations.append("Create urgency with limited-time offer")
        
        if "Low engagement" in str(risks):
            recommendations.append("Schedule product demo")
            recommendations.append("Share customer success stories")
        
        if not recommendations:
            recommendations.append("Continue current engagement strategy")
            recommendations.append("Prepare for contract negotiation")
        
        return recommendations
    
    @staticmethod
    def get_next_best_action(user, company):
        """Recommend next best action for user"""
        from activities.models import Task
        from crm.models import Lead
        from deals.models import Deal
        
        actions = []
        
        # Check overdue tasks
        overdue_tasks = Task.objects.filter(
            company=company,
            owner=user,
            status='pending',
            due_date__lt=timezone.now()
        ).order_by('due_date')[:5]
        
        for task in overdue_tasks:
            actions.append({
                'type': 'task',
                'priority': 'high',
                'action': f"Complete overdue task: {task.subject}",
                'object_id': str(task.id),
                'due_date': task.due_date
            })
        
        # Check hot leads without recent activity
        hot_leads = Lead.objects.filter(
            company=company,
            owner=user,
            status__in=['new', 'contacted']
        ).order_by('-created_at')[:10]
        
        for lead in hot_leads:
            score_data = AIInsightsService.get_lead_scoring(lead)
            if score_data['score'] >= 70:
                actions.append({
                    'type': 'lead',
                    'priority': 'high',
                    'action': f"Follow up with hot lead: {lead.first_name} {lead.last_name}",
                    'object_id': str(lead.id),
                    'score': score_data['score']
                })
        
        # Check at-risk deals
        at_risk_deals = Deal.objects.filter(
            company=company,
            owner=user,
            stage__in=['proposal', 'negotiation']
        )[:10]
        
        for deal in at_risk_deals:
            health = AIInsightsService.get_deal_health_analysis(deal)
            if health['health_score'] < 60:
                actions.append({
                    'type': 'deal',
                    'priority': 'medium',
                    'action': f"Review at-risk deal: {deal.name}",
                    'object_id': str(deal.id),
                    'health_score': health['health_score']
                })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        actions.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return actions[:10]  # Return top 10 actions
    
    @staticmethod
    def predict_churn_risk(account):
        """Predict customer churn risk"""
        risk_score = 0
        indicators = []
        
        # Activity analysis
        if hasattr(account, 'activities'):
            recent_activities = account.activities.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count() if hasattr(account.activities, 'filter') else 0
            
            if recent_activities == 0:
                risk_score += 30
                indicators.append("No recent engagement")
            elif recent_activities < 3:
                risk_score += 15
                indicators.append("Low engagement")
        
        # Support ticket analysis (if available)
        # Open deals analysis
        if hasattr(account, 'deals'):
            open_deals = account.deals.filter(
                stage__in=['prospecting', 'qualification', 'proposal', 'negotiation']
            ).count() if hasattr(account.deals, 'filter') else 0
            
            if open_deals == 0:
                risk_score += 20
                indicators.append("No active opportunities")
        
        risk_level = 'High' if risk_score >= 50 else 'Medium' if risk_score >= 30 else 'Low'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'indicators': indicators,
            'recommendations': AIInsightsService._get_retention_recommendations(risk_score)
        }
    
    @staticmethod
    def _get_retention_recommendations(risk_score):
        """Get customer retention recommendations"""
        if risk_score >= 50:
            return [
                "Schedule executive business review",
                "Offer value-added services",
                "Check-in on satisfaction"
            ]
        elif risk_score >= 30:
            return [
                "Increase touchpoint frequency",
                "Share relevant content",
                "Introduce new features"
            ]
        else:
            return [
                "Continue regular engagement",
                "Monitor for changes"
            ]
