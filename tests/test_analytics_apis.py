# tests/test_analytics_apis.py
"""
Tests for analytics API endpoints
"""

import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from analytics.models import (
    FactDealStageTransition, FactActivity, FactLeadConversion,
    AnalyticsExportJob
)


@pytest.mark.django_db
class TestPipelineVelocityAPI:
    """Tests for pipeline velocity API endpoint"""
    
    def test_pipeline_velocity_endpoint(self, authenticated_api_client, company, user, deal):
        """Test pipeline velocity API returns correct data"""
        # Create some fact records
        for i in range(5):
            FactDealStageTransition.objects.create(
                company=company,
                deal=deal,
                from_stage='prospecting',
                to_stage='qualification',
                transition_date=timezone.now() - timedelta(days=i),
                days_in_previous_stage=i + 1,
                deal_amount=10000,
                probability=50,
                weighted_amount=5000,
                owner=user,
                region='NA',
                gdpr_consent=True
            )
        
        response = authenticated_api_client.get(
            '/api/analytics/fact-deal-stage-transitions/pipeline_velocity/?days=30'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'stage_metrics' in data
        assert 'total_transitions' in data
        assert 'win_rate' in data
        assert data['period_days'] == 30
    
    def test_pipeline_velocity_by_region(self, authenticated_api_client, company, user, deal):
        """Test pipeline velocity filtered by region"""
        # Create facts in different regions
        for region in ['NA', 'EU']:
            for i in range(3):
                FactDealStageTransition.objects.create(
                    company=company,
                    deal=deal,
                    from_stage='prospecting',
                    to_stage='qualification',
                    transition_date=timezone.now(),
                    days_in_previous_stage=i + 1,
                    deal_amount=10000,
                    probability=50,
                    weighted_amount=5000,
                    owner=user,
                    region=region,
                    gdpr_consent=True
                )
        
        response = authenticated_api_client.get(
            '/api/analytics/fact-deal-stage-transitions/pipeline_velocity/?region=NA'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_transitions'] == 3  # Only NA region


@pytest.mark.django_db
class TestActivityVolumeAPI:
    """Tests for activity volume API endpoint"""
    
    def test_activity_volume_endpoint(self, authenticated_api_client, company, user):
        """Test activity volume API returns correct data"""
        # Create activity facts
        activity_types = ['call', 'email', 'meeting']
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
        
        response = authenticated_api_client.get(
            '/api/analytics/fact-activities/activity_volume/?days=30'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'total_activities' in data
        assert 'completed_activities' in data
        assert 'completion_rate' in data
        assert 'volume_by_type' in data
        assert data['total_activities'] == 9
        assert data['completed_activities'] == 9
        assert data['completion_rate'] == 100.0
    
    def test_activity_volume_by_user(self, authenticated_api_client, company, user):
        """Test activity volume filtered by user"""
        from tests.conftest import UserFactory
        
        # Create another user
        other_user = UserFactory()
        
        # Create activities for different users
        for assigned_user in [user, other_user]:
            for i in range(3):
                FactActivity.objects.create(
                    company=company,
                    activity_type='call',
                    activity_date=timezone.now(),
                    subject='Test call',
                    duration_minutes=15,
                    status='completed',
                    assigned_to=assigned_user,
                    is_completed=True,
                    is_overdue=False,
                    region='NA',
                    gdpr_consent=True
                )
        
        response = authenticated_api_client.get(
            f'/api/analytics/fact-activities/activity_volume/?user_id={user.id}'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_activities'] == 3  # Only current user's activities


@pytest.mark.django_db
class TestConversionFunnelAPI:
    """Tests for conversion funnel API endpoint"""
    
    def test_conversion_funnel_endpoint(self, authenticated_api_client, company, user):
        """Test conversion funnel API returns correct data"""
        from tests.conftest import LeadFactory
        
        # Create leads and conversion events
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
        
        # Half are qualified
        for lead in LeadFactory._meta.model.objects.all()[:5]:
            FactLeadConversion.objects.create(
                company=company,
                lead=lead,
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
        
        response = authenticated_api_client.get(
            '/api/analytics/fact-lead-conversions/conversion_funnel/?days=30'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'funnel_metrics' in data
        assert 'conversion_rates' in data
        assert 'created_to_qualified' in data['conversion_rates']
        assert 'qualified_to_converted' in data['conversion_rates']


@pytest.mark.django_db
class TestExportJobAPI:
    """Tests for analytics export job API"""
    
    def test_create_export_job(self, authenticated_api_client, company, user):
        """Test creating an export job via API"""
        data = {
            'name': 'Test Export',
            'description': 'Export pipeline data',
            'export_type': 'csv',
            'data_source': 'fact_deal_stage_transition',
            'filters': {'days': 30}
        }
        
        response = authenticated_api_client.post(
            '/api/analytics/export-jobs/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        job_data = response.json()
        assert job_data['name'] == 'Test Export'
        assert job_data['status'] == 'pending'
    
    def test_list_export_jobs(self, authenticated_api_client, company, user):
        """Test listing export jobs"""
        # Create a few export jobs
        for i in range(3):
            AnalyticsExportJob.objects.create(
                company=company,
                name=f'Export {i}',
                export_type='csv',
                data_source='fact_deal_stage_transition',
                status='pending',
                owner=user
            )
        
        response = authenticated_api_client.get('/api/analytics/export-jobs/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 3
    
    def test_cancel_export_job(self, authenticated_api_client, company, user):
        """Test cancelling an export job"""
        job = AnalyticsExportJob.objects.create(
            company=company,
            name='Test Export',
            export_type='csv',
            data_source='fact_deal_stage_transition',
            status='pending',
            owner=user
        )
        
        response = authenticated_api_client.post(
            f'/api/analytics/export-jobs/{job.id}/cancel/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        job.refresh_from_db()
        assert job.status == 'cancelled'
    
    def test_cannot_cancel_completed_job(self, authenticated_api_client, company, user):
        """Test that completed jobs cannot be cancelled"""
        job = AnalyticsExportJob.objects.create(
            company=company,
            name='Test Export',
            export_type='csv',
            data_source='fact_deal_stage_transition',
            status='completed',
            owner=user
        )
        
        response = authenticated_api_client.post(
            f'/api/analytics/export-jobs/{job.id}/cancel/'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_download_completed_export(self, authenticated_api_client, company, user, temp_media_dir):
        """Test downloading a completed export"""
        from django.core.files.base import ContentFile
        
        job = AnalyticsExportJob.objects.create(
            company=company,
            name='Test Export',
            export_type='csv',
            data_source='fact_deal_stage_transition',
            status='completed',
            owner=user,
            total_records=100
        )
        
        # Simulate file creation
        job.output_file.save('export.csv', ContentFile(b'test,data\n1,2\n'))
        job.save()
        
        response = authenticated_api_client.get(
            f'/api/analytics/export-jobs/{job.id}/download/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'download_url' in data
        assert data['total_records'] == 100


@pytest.mark.django_db
class TestFactTableReadOnlyAccess:
    """Tests for read-only access to fact tables"""
    
    def test_fact_tables_are_read_only(self, authenticated_api_client, company, user, deal):
        """Test that fact tables cannot be modified via API"""
        # Try to create via POST (should fail for read-only viewset)
        data = {
            'deal': str(deal.id),
            'to_stage': 'qualification',
            'transition_date': timezone.now().isoformat()
        }
        
        response = authenticated_api_client.post(
            '/api/analytics/fact-deal-stage-transitions/',
            data,
            format='json'
        )
        
        # Should return 405 Method Not Allowed for read-only viewset
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_can_read_fact_tables(self, authenticated_api_client, company, user, deal):
        """Test that fact tables can be read via API"""
        # Create a fact record
        fact = FactDealStageTransition.objects.create(
            company=company,
            deal=deal,
            from_stage='',
            to_stage='prospecting',
            transition_date=timezone.now(),
            days_in_previous_stage=0,
            deal_amount=10000,
            probability=50,
            weighted_amount=5000,
            owner=user,
            region='NA',
            gdpr_consent=True
        )
        
        # Read via GET
        response = authenticated_api_client.get(
            f'/api/analytics/fact-deal-stage-transitions/{fact.id}/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['to_stage'] == 'prospecting'


@pytest.mark.django_db
class TestAnalyticsFiltering:
    """Tests for analytics API filtering"""
    
    def test_filter_by_date_range(self, authenticated_api_client, company, user, deal):
        """Test filtering facts by date range"""
        # Create facts over different dates
        for days_ago in [1, 5, 10, 30, 60]:
            FactDealStageTransition.objects.create(
                company=company,
                deal=deal,
                from_stage='prospecting',
                to_stage='qualification',
                transition_date=timezone.now() - timedelta(days=days_ago),
                days_in_previous_stage=1,
                deal_amount=10000,
                probability=50,
                weighted_amount=5000,
                owner=user,
                region='NA',
                gdpr_consent=True
            )
        
        # Query with different date ranges
        response = authenticated_api_client.get(
            '/api/analytics/fact-deal-stage-transitions/pipeline_velocity/?days=7'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should only include records from last 7 days (1 and 5 days ago)
        assert data['total_transitions'] == 2
    
    def test_filter_by_owner(self, authenticated_api_client, company, user, deal):
        """Test filtering facts by owner"""
        from tests.conftest import UserFactory
        
        other_user = UserFactory()
        
        # Create facts for different owners
        FactDealStageTransition.objects.create(
            company=company,
            deal=deal,
            from_stage='prospecting',
            to_stage='qualification',
            transition_date=timezone.now(),
            days_in_previous_stage=1,
            deal_amount=10000,
            probability=50,
            weighted_amount=5000,
            owner=user,
            region='NA',
            gdpr_consent=True
        )
        
        FactDealStageTransition.objects.create(
            company=company,
            deal=deal,
            from_stage='qualification',
            to_stage='proposal',
            transition_date=timezone.now(),
            days_in_previous_stage=2,
            deal_amount=10000,
            probability=60,
            weighted_amount=6000,
            owner=other_user,
            region='NA',
            gdpr_consent=True
        )
        
        # Filter by owner
        response = authenticated_api_client.get(
            f'/api/analytics/fact-deal-stage-transitions/?owner={user.id}'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
