# crm/lead_scoring_service.py
# Lead Scoring v2 with feature extraction and explanation

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from django.utils import timezone
from django.db.models import Count, Q
from crm.models import Lead
from analytics.models import LeadScoreCache

logger = logging.getLogger(__name__)

class LeadScoringV2Service:
    """Lead scoring service with multi-factor analysis and explanations"""
    
    # Default weights for scoring components
    DEFAULT_WEIGHTS = {
        'status': 25,
        'recent_activity': 20,
        'age': 15,
        'completeness': 20,
        'engagement': 15,
        'custom_fields': 5,
    }
    
    # Status weights
    STATUS_WEIGHTS = {
        'new': 30,
        'contacted': 50,
        'qualified': 80,
        'unqualified': 10,
        'converted': 100,
        'lost': 0,
    }
    
    @classmethod
    def calculate_lead_score(
        cls,
        lead: Lead,
        score_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive lead score with explanation.
        
        Args:
            lead: Lead instance to score
            score_config: Optional custom scoring configuration
        
        Returns:
            Dict with 'total_score', 'components', and 'explanation'
        """
        weights = score_config or cls.DEFAULT_WEIGHTS
        components = []
        
        # 1. Status component
        status_score, status_exp = cls._score_status(lead, weights.get('status', 25))
        components.append({
            'name': 'status',
            'weight': weights.get('status', 25),
            'contribution': status_score,
            'explanation': status_exp
        })
        
        # 2. Recent activity component
        activity_score, activity_exp = cls._score_recent_activity(
            lead, weights.get('recent_activity', 20)
        )
        components.append({
            'name': 'recent_activity',
            'weight': weights.get('recent_activity', 20),
            'contribution': activity_score,
            'explanation': activity_exp
        })
        
        # 3. Age/freshness component
        age_score, age_exp = cls._score_age(lead, weights.get('age', 15))
        components.append({
            'name': 'age',
            'weight': weights.get('age', 15),
            'contribution': age_score,
            'explanation': age_exp
        })
        
        # 4. Completeness component
        completeness_score, completeness_exp = cls._score_completeness(
            lead, weights.get('completeness', 20)
        )
        components.append({
            'name': 'completeness',
            'weight': weights.get('completeness', 20),
            'contribution': completeness_score,
            'explanation': completeness_exp
        })
        
        # 5. Engagement component
        engagement_score, engagement_exp = cls._score_engagement(
            lead, weights.get('engagement', 15)
        )
        components.append({
            'name': 'engagement',
            'weight': weights.get('engagement', 15),
            'contribution': engagement_score,
            'explanation': engagement_exp
        })
        
        # 6. Custom fields component
        custom_score, custom_exp = cls._score_custom_fields(
            lead, weights.get('custom_fields', 5), score_config
        )
        components.append({
            'name': 'custom_fields',
            'weight': weights.get('custom_fields', 5),
            'contribution': custom_score,
            'explanation': custom_exp
        })
        
        # Calculate total score
        total_score = sum(c['contribution'] for c in components)
        total_score = max(0, min(100, int(total_score)))  # Clamp to 0-100
        
        return {
            'total_score': total_score,
            'components': components,
            'explanation': cls._generate_explanation(total_score, components),
            'calculated_at': timezone.now().isoformat(),
            'score_version': 'v2'
        }
    
    @classmethod
    def _score_status(cls, lead: Lead, weight: int) -> Tuple[float, str]:
        """Score based on lead status"""
        status = getattr(lead, 'status', 'new')
        status_weight = cls.STATUS_WEIGHTS.get(status, 50)
        score = (status_weight / 100) * weight
        explanation = f"Status '{status}' contributes {status_weight}% weight"
        return score, explanation
    
    @classmethod
    def _score_recent_activity(cls, lead: Lead, weight: int) -> Tuple[float, str]:
        """Score based on recent activities"""
        # Get activities in last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        try:
            from activities.models import Activity
            activity_count = Activity.objects.filter(
                lead=lead,
                created_at__gte=thirty_days_ago
            ).count()
        except:
            activity_count = 0
        
        # Score: more activities = higher score (cap at 10 activities)
        activity_factor = min(activity_count / 10, 1.0)
        score = activity_factor * weight
        explanation = f"{activity_count} activities in last 30 days"
        return score, explanation
    
    @classmethod
    def _score_age(cls, lead: Lead, weight: int) -> Tuple[float, str]:
        """Score based on lead age (fresher leads score higher)"""
        days_since_creation = (timezone.now() - lead.created_at).days
        
        # Score decreases with age (optimal window: 0-30 days)
        if days_since_creation <= 7:
            age_factor = 1.0  # Very fresh
        elif days_since_creation <= 30:
            age_factor = 0.8  # Fresh
        elif days_since_creation <= 90:
            age_factor = 0.5  # Moderate
        else:
            age_factor = 0.2  # Old
        
        score = age_factor * weight
        explanation = f"{days_since_creation} days old"
        return score, explanation
    
    @classmethod
    def _score_completeness(cls, lead: Lead, weight: int) -> Tuple[float, str]:
        """Score based on profile completeness"""
        fields_to_check = [
            'email', 'phone', 'company_name', 'industry',
            'annual_revenue', 'budget', 'title'
        ]
        
        filled_count = sum(
            1 for field in fields_to_check
            if getattr(lead, field, None)
        )
        completeness_factor = filled_count / len(fields_to_check)
        score = completeness_factor * weight
        explanation = f"{filled_count}/{len(fields_to_check)} key fields filled"
        return score, explanation
    
    @classmethod
    def _score_engagement(cls, lead: Lead, weight: int) -> Tuple[float, str]:
        """Score based on engagement signals"""
        engagement_score = 0
        signals = []
        
        # Check various engagement signals
        if hasattr(lead, 'email_opened') and lead.email_opened:
            engagement_score += 0.3
            signals.append('email_opened')
        
        if hasattr(lead, 'link_clicked') and lead.link_clicked:
            engagement_score += 0.3
            signals.append('link_clicked')
        
        if hasattr(lead, 'form_submitted') and lead.form_submitted:
            engagement_score += 0.4
            signals.append('form_submitted')
        
        score = min(engagement_score, 1.0) * weight
        explanation = f"Engagement signals: {', '.join(signals) if signals else 'none'}"
        return score, explanation
    
    @classmethod
    def _score_custom_fields(
        cls,
        lead: Lead,
        weight: int,
        config: Dict = None
    ) -> Tuple[float, str]:
        """Score based on custom field values"""
        if not config or 'custom_field_weights' not in config:
            return 0, "No custom field weights configured"
        
        custom_weights = config['custom_field_weights']
        custom_fields = getattr(lead, 'custom_fields', {}) or {}
        
        score = 0
        scored_fields = []
        
        for field_name, field_weight in custom_weights.items():
            if field_name in custom_fields and custom_fields[field_name]:
                score += field_weight
                scored_fields.append(field_name)
        
        score = min(score / 100, 1.0) * weight
        explanation = f"Custom fields scored: {', '.join(scored_fields) if scored_fields else 'none'}"
        return score, explanation
    
    @classmethod
    def _generate_explanation(
        cls,
        total_score: int,
        components: List[Dict]
    ) -> str:
        """Generate human-readable explanation of score"""
        if total_score >= 80:
            quality = "🔥 HOT"
            recommendation = "High priority - contact immediately"
        elif total_score >= 60:
            quality = "🌡️ WARM"
            recommendation = "Good prospect - schedule follow-up within 24 hours"
        elif total_score >= 40:
            quality = "❄️ COOL"
            recommendation = "Average prospect - add to nurture campaign"
        else:
            quality = "🧊 COLD"
            recommendation = "Low priority - consider disqualifying or long-term nurture"
        
        top_contributors = sorted(
            components,
            key=lambda x: x['contribution'],
            reverse=True
        )[:3]
        
        top_factors = ', '.join([c['name'] for c in top_contributors])
        
        return (
            f"{quality} Lead (Score: {total_score}/100). "
            f"{recommendation}. "
            f"Top factors: {top_factors}."
        )
    
    @classmethod
    def update_lead_score_cache(
        cls,
        lead: Lead,
        score_config: Dict = None
    ) -> LeadScoreCache:
        """Calculate and update lead score cache"""
        score_data = cls.calculate_lead_score(lead, score_config)
        
        # Create or update cache
        cache, created = LeadScoreCache.objects.update_or_create(
            lead=lead,
            company=lead.company,
            defaults={
                'total_score': score_data['total_score'],
                'score_components': {
                    c['name']: c['contribution']
                    for c in score_data['components']
                },
                'explanation': score_data,
                'status_weight': cls.STATUS_WEIGHTS.get(
                    getattr(lead, 'status', 'new'), 50
                ),
                'recent_activity_count': 0,  # TODO: get actual count
                'days_since_creation': (timezone.now() - lead.created_at).days,
                'score_version': 'v2'
            }
        )
        
        return cache
    
    @classmethod
    def bulk_update_scores(cls, company, limit: int = 100):
        """Bulk update lead scores for a company"""
        leads = Lead.objects.filter(
            company=company,
            is_active=True
        )[:limit]
        
        updated = 0
        for lead in leads:
            try:
                cls.update_lead_score_cache(lead)
                updated += 1
            except Exception as e:
                logger.error(f"Error updating score for lead {lead.id}: {e}")
        
        logger.info(f"Updated scores for {updated}/{len(leads)} leads")
        return updated
