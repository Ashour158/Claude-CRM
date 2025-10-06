# tests/test_analytics_facts.py
"""
Tests for analytics fact models, ETL, and APIs
"""

import pytest
from django.utils import timezone
from datetime import timedelta
from analytics.models import (
    FactDealStageTransition, FactActivity, FactLeadConversion,
    AnalyticsExportJob
)
from django.core.management import call_command
from io import StringIO


@pytest.mark.django_db
class TestFactDealStageTransition:
    """Tests for FactDealStageTransition model"""
    
    def test_create_fact_deal_stage_transition(self, company, user, deal):
        """Test creating a deal stage transition fact"""
        fact = FactDealStageTransition.objects.create(
            company=company,
            deal=deal,
            from_stage='',
            to_stage='prospecting',
            transition_date=timezone.now(),
            days_in_previous_stage=0,
            deal_amount=deal.amount,
            probability=deal.probability,
            weighted_amount=deal.weighted_amount,
            owner=user,
            region='NA',
            gdpr_consent=True
        )
        
        assert fact.deal == deal
        assert fact.to_stage == 'prospecting'
        assert fact.owner == user
        assert fact.region == 'NA'
    
    def test_fact_indexes(self, company, user, deal):
        """Test that fact records can be efficiently queried"""
        # Create multiple facts
        for i in range(5):
            FactDealStageTransition.objects.create(
                company=company,
                deal=deal,
                from_stage='prospecting',
                to_stage='qualification',
                transition_date=timezone.now() - timedelta(days=i),
                days_in_previous_stage=i,
                deal_amount=deal.amount,
                probability=deal.probability,
                weighted_amount=deal.weighted_amount,
                owner=user,
                region='NA',
                gdpr_consent=True
            )
        
        # Test date-based query
        cutoff = timezone.now() - timedelta(days=3)
        recent_facts = FactDealStageTransition.objects.filter(
            transition_date__gte=cutoff
        )
        assert recent_facts.count() >= 3
    
    def test_weighted_amount_calculation(self, company, user, deal):
        """Test weighted amount is correctly stored"""
        deal.amount = 10000
        deal.probability = 50
        deal.save()
        
        fact = FactDealStageTransition.objects.create(
            company=company,
            deal=deal,
            from_stage='',
            to_stage='prospecting',
            transition_date=timezone.now(),
            days_in_previous_stage=0,
            deal_amount=deal.amount,
            probability=deal.probability,
            weighted_amount=deal.amount * deal.probability / 100,
            owner=user,
            region='NA',
            gdpr_consent=True
        )
        
        assert fact.weighted_amount == 5000


@pytest.mark.django_db
class TestFactActivity:
    """Tests for FactActivity model"""
    
    def test_create_fact_activity(self, company, user, activity):
        """Test creating an activity fact"""
        fact = FactActivity.objects.create(
            company=company,
            activity_type=activity.activity_type,
            activity_date=activity.activity_date,
            subject=activity.subject,
            duration_minutes=30,
            status=activity.status,
            assigned_to=user,
            is_completed=False,
            is_overdue=False,
            region='NA',
            gdpr_consent=True
        )
        
        assert fact.activity_type == activity.activity_type
        assert fact.assigned_to == user
        assert fact.duration_minutes == 30
    
    def test_activity_volume_by_type(self, company, user):
        """Test querying activity volume by type"""
        # Create various activity types
        activity_types = ['call', 'email', 'meeting', 'demo']
        for activity_type in activity_types:
            for i in range(3):
                FactActivity.objects.create(
                    company=company,
                    activity_type=activity_type,
                    activity_date=timezone.now(),
                    subject=f'Test {activity_type}',
                    duration_minutes=15,
                    status='completed',
                    assigned_to=user,
                    is_completed=True,
                    is_overdue=False,
                    region='NA',
                    gdpr_consent=True
                )
        
        # Query by type
        call_count = FactActivity.objects.filter(activity_type='call').count()
        assert call_count == 3
        
        # Query all completed
        completed = FactActivity.objects.filter(is_completed=True).count()
        assert completed == 12
    
    def test_completion_rate_calculation(self, company, user):
        """Test calculating activity completion rates"""
        # Create completed and pending activities
        for i in range(7):
            FactActivity.objects.create(
                company=company,
                activity_type='call',
                activity_date=timezone.now(),
                subject='Test call',
                duration_minutes=15,
                status='completed',
                assigned_to=user,
                is_completed=True,
                is_overdue=False,
                region='NA',
                gdpr_consent=True
            )
        
        for i in range(3):
            FactActivity.objects.create(
                company=company,
                activity_type='call',
                activity_date=timezone.now(),
                subject='Test call',
                duration_minutes=15,
                status='planned',
                assigned_to=user,
                is_completed=False,
                is_overdue=False,
                region='NA',
                gdpr_consent=True
            )
        
        total = FactActivity.objects.count()
        completed = FactActivity.objects.filter(is_completed=True).count()
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        assert total == 10
        assert completed == 7
        assert completion_rate == 70.0


@pytest.mark.django_db
class TestFactLeadConversion:
    """Tests for FactLeadConversion model"""
    
    def test_create_fact_lead_conversion(self, company, user, lead):
        """Test creating a lead conversion fact"""
        fact = FactLeadConversion.objects.create(
            company=company,
            lead=lead,
            event_type='created',
            event_date=timezone.now(),
            lead_status=lead.lead_status,
            lead_source='website',
            lead_score=lead.lead_score,
            days_since_creation=0,
            days_in_previous_status=0,
            owner=user,
            region='NA',
            gdpr_consent=True
        )
        
        assert fact.lead == lead
        assert fact.event_type == 'created'
        assert fact.owner == user
    
    def test_conversion_funnel_tracking(self, company, user, lead):
        """Test tracking lead through conversion funnel"""
        # Create event
        FactLeadConversion.objects.create(
            company=company,
            lead=lead,
            event_type='created',
            event_date=timezone.now() - timedelta(days=10),
            lead_status='new',
            lead_source='website',
            lead_score=50,
            days_since_creation=0,
            days_in_previous_status=0,
            owner=user,
            region='NA',
            gdpr_consent=True
        )
        
        # Qualified event
        FactLeadConversion.objects.create(
            company=company,
            lead=lead,
            event_type='qualified',
            event_date=timezone.now() - timedelta(days=5),
            lead_status='qualified',
            lead_source='website',
            lead_score=75,
            days_since_creation=5,
            days_in_previous_status=5,
            owner=user,
            region='NA',
            gdpr_consent=True
        )
        
        # Converted event
        FactLeadConversion.objects.create(
            company=company,
            lead=lead,
            event_type='converted',
            event_date=timezone.now(),
            lead_status='converted',
            lead_source='website',
            lead_score=100,
            days_since_creation=10,
            days_in_previous_status=5,
            conversion_value=50000,
            owner=user,
            region='NA',
            gdpr_consent=True
        )
        
        # Verify funnel progression
        events = FactLeadConversion.objects.filter(lead=lead).order_by('event_date')
        assert events.count() == 3
        assert events[0].event_type == 'created'
        assert events[1].event_type == 'qualified'
        assert events[2].event_type == 'converted'
        assert events[2].conversion_value == 50000
    
    def test_conversion_rate_calculation(self, company, user):
        """Test calculating conversion rates"""
        from tests.conftest import LeadFactory
        
        # Create 10 leads with 'created' events
        for i in range(10):
            lead = LeadFactory(company=company, owner=user)
            FactLeadConversion.objects.create(
                company=company,
                lead=lead,
                event_type='created',
                event_date=timezone.now(),
                lead_status='new',
                lead_source='website',
                lead_score=50,
                days_since_creation=0,
                days_in_previous_status=0,
                owner=user,
                region='NA',
                gdpr_consent=True
            )
        
        # 5 of them are qualified
        qualified_leads = FactLeadConversion.objects.filter(event_type='created')[:5]
        for fact in qualified_leads:
            FactLeadConversion.objects.create(
                company=company,
                lead=fact.lead,
                event_type='qualified',
                event_date=timezone.now(),
                lead_status='qualified',
                lead_source='website',
                lead_score=75,
                days_since_creation=7,
                days_in_previous_status=7,
                owner=user,
                region='NA',
                gdpr_consent=True
            )
        
        # 2 of them are converted
        converted_leads = FactLeadConversion.objects.filter(event_type='qualified')[:2]
        for fact in converted_leads:
            FactLeadConversion.objects.create(
                company=company,
                lead=fact.lead,
                event_type='converted',
                event_date=timezone.now(),
                lead_status='converted',
                lead_source='website',
                lead_score=100,
                days_since_creation=14,
                days_in_previous_status=7,
                conversion_value=50000,
                owner=user,
                region='NA',
                gdpr_consent=True
            )
        
        created_count = FactLeadConversion.objects.filter(event_type='created').count()
        qualified_count = FactLeadConversion.objects.filter(event_type='qualified').count()
        converted_count = FactLeadConversion.objects.filter(event_type='converted').count()
        
        assert created_count == 10
        assert qualified_count == 5
        assert converted_count == 2
        
        # Calculate rates
        created_to_qualified = (qualified_count / created_count * 100) if created_count > 0 else 0
        qualified_to_converted = (converted_count / qualified_count * 100) if qualified_count > 0 else 0
        
        assert created_to_qualified == 50.0
        assert qualified_to_converted == 40.0


@pytest.mark.django_db
class TestAnalyticsExportJob:
    """Tests for AnalyticsExportJob model"""
    
    def test_create_export_job(self, company, user):
        """Test creating an analytics export job"""
        job = AnalyticsExportJob.objects.create(
            company=company,
            name='Test Export',
            description='Export deal transitions',
            export_type='csv',
            data_source='fact_deal_stage_transition',
            filters={'days': 30},
            status='pending',
            owner=user
        )
        
        assert job.name == 'Test Export'
        assert job.status == 'pending'
        assert job.owner == user
    
    def test_export_job_status_transitions(self, company, user):
        """Test export job status transitions"""
        job = AnalyticsExportJob.objects.create(
            company=company,
            name='Test Export',
            export_type='csv',
            data_source='fact_deal_stage_transition',
            status='pending',
            owner=user
        )
        
        # Start job
        job.status = 'running'
        job.started_at = timezone.now()
        job.save()
        assert job.status == 'running'
        
        # Complete job
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.total_records = 100
        job.save()
        assert job.status == 'completed'
        assert job.total_records == 100


@pytest.mark.django_db
class TestETLBackfill:
    """Tests for ETL backfill functionality"""
    
    def test_backfill_deal_transitions_dry_run(self, company, user, deal):
        """Test backfill command in dry-run mode"""
        out = StringIO()
        call_command(
            'backfill_analytics_facts',
            '--fact-type=deals',
            '--days=30',
            '--dry-run',
            stdout=out
        )
        
        output = out.getvalue()
        assert 'DRY RUN MODE' in output
        assert 'Backfilling deal stage transitions' in output
    
    def test_backfill_creates_facts(self, company, user, deal):
        """Test backfill actually creates fact records"""
        initial_count = FactDealStageTransition.objects.count()
        
        call_command(
            'backfill_analytics_facts',
            '--fact-type=deals',
            '--days=30',
            verbosity=0
        )
        
        final_count = FactDealStageTransition.objects.count()
        assert final_count > initial_count


@pytest.mark.django_db
class TestGDPRCompliance:
    """Tests for GDPR compliance features"""
    
    def test_region_tagging(self, company, user, deal):
        """Test that facts are tagged with region"""
        fact = FactDealStageTransition.objects.create(
            company=company,
            deal=deal,
            from_stage='',
            to_stage='prospecting',
            transition_date=timezone.now(),
            days_in_previous_stage=0,
            deal_amount=deal.amount,
            probability=deal.probability,
            weighted_amount=deal.weighted_amount,
            owner=user,
            region='EU',
            gdpr_consent=True
        )
        
        assert fact.region == 'EU'
        assert fact.gdpr_consent is True
    
    def test_data_retention_date(self, company, user, deal):
        """Test data retention date is set"""
        retention_date = timezone.now().date() + timedelta(days=730)  # 2 years
        
        fact = FactDealStageTransition.objects.create(
            company=company,
            deal=deal,
            from_stage='',
            to_stage='prospecting',
            transition_date=timezone.now(),
            days_in_previous_stage=0,
            deal_amount=deal.amount,
            probability=deal.probability,
            weighted_amount=deal.weighted_amount,
            owner=user,
            region='EU',
            gdpr_consent=True,
            data_retention_date=retention_date
        )
        
        assert fact.data_retention_date == retention_date
    
    def test_query_by_region(self, company, user, deal):
        """Test filtering facts by region"""
        # Create facts in different regions
        for region in ['NA', 'EU', 'APAC']:
            FactDealStageTransition.objects.create(
                company=company,
                deal=deal,
                from_stage='',
                to_stage='prospecting',
                transition_date=timezone.now(),
                days_in_previous_stage=0,
                deal_amount=deal.amount,
                probability=deal.probability,
                weighted_amount=deal.weighted_amount,
                owner=user,
                region=region,
                gdpr_consent=True
            )
        
        # Query by region
        eu_facts = FactDealStageTransition.objects.filter(region='EU')
        assert eu_facts.count() == 1
        assert eu_facts.first().region == 'EU'
