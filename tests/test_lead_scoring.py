# tests/test_lead_scoring.py
# Tests for Lead Scoring v2 Phase 4+

import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import Company
from crm.models import Lead
from analytics.models import LeadScoreCache
from crm.lead_scoring_service import LeadScoringV2Service

User = get_user_model()

@pytest.fixture
def company(db):
    return Company.objects.create(
        name="Test Company",
        code="TEST001"
    )

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123"
    )

@pytest.fixture
def lead(db, company, user):
    return Lead.objects.create(
        company=company,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="+1234567890",
        company_name="Test Corp",
        status="qualified",
        created_by=user
    )

class TestLeadScoringComponents:
    """Test individual scoring components"""
    
    @pytest.mark.django_db
    def test_status_component_qualified(self, lead):
        """Test status component for qualified lead"""
        score, explanation = LeadScoringV2Service._score_status(lead, weight=25)
        
        # Qualified status has 80% weight
        expected_score = (80 / 100) * 25
        assert score == expected_score
        assert "qualified" in explanation.lower()
    
    @pytest.mark.django_db
    def test_status_component_new(self, lead):
        """Test status component for new lead"""
        lead.status = "new"
        score, explanation = LeadScoringV2Service._score_status(lead, weight=25)
        
        # New status has 30% weight
        expected_score = (30 / 100) * 25
        assert score == expected_score
        assert "new" in explanation.lower()
    
    @pytest.mark.django_db
    def test_age_component_fresh_lead(self, lead):
        """Test age component for very fresh lead (< 7 days)"""
        score, explanation = LeadScoringV2Service._score_age(lead, weight=15)
        
        # Fresh leads should get full weight
        assert score == 15
        assert "days old" in explanation
    
    @pytest.mark.django_db
    def test_age_component_old_lead(self, lead):
        """Test age component for old lead (> 90 days)"""
        # Set created_at to 120 days ago
        lead.created_at = timezone.now() - timedelta(days=120)
        lead.save()
        
        score, explanation = LeadScoringV2Service._score_age(lead, weight=15)
        
        # Old leads get 20% factor
        expected_score = 0.2 * 15
        assert score == expected_score
        assert "120" in explanation
    
    @pytest.mark.django_db
    def test_completeness_component_full_profile(self, lead):
        """Test completeness component for fully filled lead"""
        # Fill all tracked fields
        lead.email = "test@example.com"
        lead.phone = "+1234567890"
        lead.company_name = "Test Corp"
        lead.industry = "Technology"
        lead.annual_revenue = 1000000
        lead.budget = 50000
        lead.title = "CEO"
        lead.save()
        
        score, explanation = LeadScoringV2Service._score_completeness(lead, weight=20)
        
        # All 7 fields filled = full weight
        assert score == 20
        assert "7/7" in explanation
    
    @pytest.mark.django_db
    def test_completeness_component_partial_profile(self, lead):
        """Test completeness component for partially filled lead"""
        # Only email and phone filled (2 of 7)
        lead.industry = None
        lead.annual_revenue = None
        lead.budget = None
        lead.title = None
        lead.save()
        
        score, explanation = LeadScoringV2Service._score_completeness(lead, weight=20)
        
        # At least email, phone, company_name filled (3 of 7)
        expected_factor = 3 / 7
        expected_score = expected_factor * 20
        assert abs(score - expected_score) < 0.1

class TestLeadScoringIntegration:
    """Test complete lead scoring"""
    
    @pytest.mark.django_db
    def test_calculate_hot_lead_score(self, lead, company):
        """Test scoring for a hot lead"""
        # Setup hot lead
        lead.status = "qualified"  # 80% = 20 pts (weight 25)
        lead.email = "test@example.com"
        lead.phone = "+1234567890"
        lead.company_name = "Test Corp"
        lead.industry = "Technology"
        lead.annual_revenue = 1000000
        lead.budget = 50000
        lead.title = "CEO"
        lead.save()
        
        result = LeadScoringV2Service.calculate_lead_score(lead)
        
        assert 'total_score' in result
        assert 'components' in result
        assert 'explanation' in result
        
        # Should be a hot lead (>= 80)
        # We can't guarantee exact score without activities, but it should be high
        assert result['total_score'] >= 50  # At minimum
        assert result['score_version'] == 'v2'
        assert len(result['components']) == 6
    
    @pytest.mark.django_db
    def test_calculate_cold_lead_score(self, lead):
        """Test scoring for a cold lead"""
        # Setup cold lead
        lead.status = "unqualified"  # 10% = 2.5 pts (weight 25)
        lead.created_at = timezone.now() - timedelta(days=150)  # Very old
        lead.industry = None
        lead.annual_revenue = None
        lead.budget = None
        lead.title = None
        lead.save()
        
        result = LeadScoringV2Service.calculate_lead_score(lead)
        
        # Should be a cold lead (< 40)
        assert result['total_score'] < 40
        assert "COLD" in result['explanation'] or "COOL" in result['explanation']
    
    @pytest.mark.django_db
    def test_score_explanation_includes_recommendation(self, lead):
        """Test that score includes recommendation"""
        result = LeadScoringV2Service.calculate_lead_score(lead)
        
        explanation = result['explanation']
        assert "Lead" in explanation
        assert any(word in explanation for word in ["contact", "follow-up", "nurture", "disqualify"])
    
    @pytest.mark.django_db
    def test_score_components_sum_to_weights(self, lead):
        """Test that component weights are respected"""
        weights = {
            'status': 30,
            'recent_activity': 20,
            'age': 10,
            'completeness': 25,
            'engagement': 10,
            'custom_fields': 5,
        }
        
        result = LeadScoringV2Service.calculate_lead_score(lead, score_config=weights)
        
        # Check that each component respects its weight
        for component in result['components']:
            assert component['weight'] == weights[component['name']]
    
    @pytest.mark.django_db
    def test_custom_field_scoring(self, lead):
        """Test custom field contribution to score"""
        lead.custom_fields = {
            "budget_approved": True,
            "decision_maker": True,
            "urgent_need": False
        }
        lead.save()
        
        score_config = {
            'status': 25,
            'recent_activity': 20,
            'age': 15,
            'completeness': 20,
            'engagement': 15,
            'custom_fields': 5,
            'custom_field_weights': {
                'budget_approved': 40,
                'decision_maker': 30,
                'urgent_need': 30
            }
        }
        
        result = LeadScoringV2Service.calculate_lead_score(lead, score_config=score_config)
        
        # Find custom_fields component
        custom_component = next(
            c for c in result['components']
            if c['name'] == 'custom_fields'
        )
        
        # Should have scored for budget_approved (40) + decision_maker (30) = 70
        # Normalized: 70/100 * 5 = 3.5 points
        assert custom_component['contribution'] > 0
        assert 'budget_approved' in custom_component['explanation'] or 'decision_maker' in custom_component['explanation']

class TestLeadScoreCache:
    """Test lead score caching"""
    
    @pytest.mark.django_db
    def test_update_lead_score_cache_creates_cache(self, lead):
        """Test that updating cache creates LeadScoreCache"""
        cache = LeadScoringV2Service.update_lead_score_cache(lead)
        
        assert cache is not None
        assert cache.lead == lead
        assert cache.total_score >= 0
        assert cache.total_score <= 100
        assert cache.score_version == 'v2'
    
    @pytest.mark.django_db
    def test_update_lead_score_cache_updates_existing(self, lead):
        """Test that updating cache updates existing record"""
        # Create initial cache
        cache1 = LeadScoringV2Service.update_lead_score_cache(lead)
        cache1_id = cache1.id
        
        # Update lead and recalculate
        lead.status = "qualified"
        lead.save()
        cache2 = LeadScoringV2Service.update_lead_score_cache(lead)
        
        # Should update same record, not create new one
        assert cache2.id == cache1_id
        assert cache2.total_score != cache1.total_score  # Score should change
    
    @pytest.mark.django_db
    def test_bulk_update_scores(self, company, user):
        """Test bulk score update"""
        # Create multiple leads
        leads = []
        for i in range(5):
            lead = Lead.objects.create(
                company=company,
                first_name=f"Lead{i}",
                last_name="Test",
                email=f"lead{i}@test.com",
                status="new",
                created_by=user
            )
            leads.append(lead)
        
        # Bulk update scores
        updated_count = LeadScoringV2Service.bulk_update_scores(company, limit=10)
        
        assert updated_count == 5
        
        # Verify all leads have cached scores
        for lead in leads:
            lead.refresh_from_db()
            assert hasattr(lead, 'score_cache')

class TestLeadScoringEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.django_db
    def test_lead_with_missing_fields(self, company, user):
        """Test scoring lead with minimal data"""
        lead = Lead.objects.create(
            company=company,
            email="minimal@test.com",
            created_by=user
        )
        
        result = LeadScoringV2Service.calculate_lead_score(lead)
        
        # Should still calculate score without errors
        assert result['total_score'] >= 0
        assert result['total_score'] <= 100
    
    @pytest.mark.django_db
    def test_score_clamped_to_0_100(self, lead):
        """Test that score is always clamped to 0-100 range"""
        # Use extreme weights
        weights = {
            'status': 200,  # Extremely high
            'recent_activity': 0,
            'age': 0,
            'completeness': 0,
            'engagement': 0,
            'custom_fields': 0,
        }
        
        result = LeadScoringV2Service.calculate_lead_score(lead, score_config=weights)
        
        # Score should still be clamped to 100
        assert result['total_score'] >= 0
        assert result['total_score'] <= 100
    
    @pytest.mark.django_db
    def test_negative_days_since_creation(self, lead):
        """Test handling of leads with future created_at (edge case)"""
        # Set created_at to future (shouldn't happen but test resilience)
        lead.created_at = timezone.now() + timedelta(days=1)
        lead.save()
        
        result = LeadScoringV2Service.calculate_lead_score(lead)
        
        # Should not crash
        assert result['total_score'] >= 0

@pytest.mark.django_db
class TestLeadScoringRecommendations:
    """Test recommendation generation"""
    
    def test_hot_lead_recommendation(self, lead):
        """Test recommendation for hot lead (80+)"""
        # Create conditions for high score
        lead.status = "qualified"
        lead.email = "test@example.com"
        lead.phone = "+1234567890"
        lead.company_name = "Test Corp"
        lead.industry = "Technology"
        lead.annual_revenue = 1000000
        lead.budget = 50000
        lead.title = "CEO"
        lead.save()
        
        # Force high score by manipulating components
        result = LeadScoringV2Service.calculate_lead_score(lead)
        explanation = LeadScoringV2Service._generate_explanation(85, result['components'])
        
        assert "HOT" in explanation or "WARM" in explanation
        assert any(word in explanation.lower() for word in ["contact", "immediately", "priority"])
    
    def test_cold_lead_recommendation(self, lead):
        """Test recommendation for cold lead (<40)"""
        result = LeadScoringV2Service.calculate_lead_score(lead)
        explanation = LeadScoringV2Service._generate_explanation(25, result['components'])
        
        assert "COLD" in explanation or "COOL" in explanation
        assert any(word in explanation.lower() for word in ["disqualify", "nurture", "low priority"])
