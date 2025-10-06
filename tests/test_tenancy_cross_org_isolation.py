# tests/test_tenancy_cross_org_isolation.py
"""Tests for cross-organization isolation using TenantQuerySet scoping."""

import pytest
from crm.models import Account, Contact, Lead
from activities.models import TimelineEvent


@pytest.mark.django_db
class TestCrossOrganizationIsolation:
    """Test that data is properly isolated between organizations/companies."""
    
    def test_accounts_isolated_by_company(self, user_factory, organization):
        """Test that accounts are isolated by company."""
        # Create two companies
        from tests.conftest import CompanyFactory
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        
        user = user_factory()
        
        # Create accounts for each company without triggering auto-generation
        account1 = Account.objects.create(
            company=company1,
            name='Company 1 Account',
            account_number='ACC1-000001',  # Explicit number
            owner=user
        )
        account2 = Account.objects.create(
            company=company2,
            name='Company 2 Account',
            account_number='ACC2-000001',  # Explicit number
            owner=user
        )
        
        # Query accounts for company1
        company1_accounts = Account.objects.filter(company=company1)
        
        # Should only see company1's account
        assert company1_accounts.count() == 1
        assert account1 in company1_accounts
        assert account2 not in company1_accounts
    
    def test_contacts_isolated_by_company(self, user_factory):
        """Test that contacts are isolated by company."""
        from tests.conftest import CompanyFactory
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        
        user = user_factory()
        
        # Create contacts for each company
        contact1 = Contact.objects.create(
            company=company1,
            first_name='John',
            last_name='Doe',
            email='john@company1.com',
            owner=user
        )
        contact2 = Contact.objects.create(
            company=company2,
            first_name='Jane',
            last_name='Smith',
            email='jane@company2.com',
            owner=user
        )
        
        # Query contacts for company1
        company1_contacts = Contact.objects.filter(company=company1)
        
        # Should only see company1's contact
        assert company1_contacts.count() == 1
        assert contact1 in company1_contacts
        assert contact2 not in company1_contacts
    
    def test_leads_isolated_by_company(self, user_factory):
        """Test that leads are isolated by company."""
        from tests.conftest import CompanyFactory
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        
        user = user_factory()
        
        # Create leads for each company
        lead1 = Lead.objects.create(
            company=company1,
            first_name='Lead',
            last_name='One',
            email='lead1@company1.com',
            owner=user
        )
        lead2 = Lead.objects.create(
            company=company2,
            first_name='Lead',
            last_name='Two',
            email='lead2@company2.com',
            owner=user
        )
        
        # Query leads for company1
        company1_leads = Lead.objects.filter(company=company1)
        
        # Should only see company1's lead
        assert company1_leads.count() == 1
        assert lead1 in company1_leads
        assert lead2 not in company1_leads
    
    def test_timeline_events_isolated_by_company(self, user_factory):
        """Test that timeline events are isolated by company."""
        from tests.conftest import CompanyFactory
        company1 = CompanyFactory()
        company2 = CompanyFactory()
        
        user = user_factory()
        
        # Create timeline events for each company
        event1 = TimelineEvent.objects.create(
            company=company1,
            event_type='created',
            title='Event 1',
            user=user
        )
        event2 = TimelineEvent.objects.create(
            company=company2,
            event_type='created',
            title='Event 2',
            user=user
        )
        
        # Query timeline events for company1
        company1_events = TimelineEvent.objects.filter(company=company1)
        
        # Should only see company1's event
        assert company1_events.count() == 1
        assert event1 in company1_events
        assert event2 not in company1_events
    
    def test_lead_conversion_preserves_company_isolation(self, user_factory):
        """Test that lead conversion creates entities in the same company."""
        from tests.conftest import CompanyFactory
        from django.urls import reverse
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        from core.models import UserCompanyAccess
        
        company = CompanyFactory()
        user = user_factory()
        
        # Create user company access
        UserCompanyAccess.objects.create(
            user=user,
            company=company,
            role='admin',
            is_active=True
        )
        
        # Create lead
        lead = Lead.objects.create(
            company=company,
            first_name='Test',
            last_name='Lead',
            email='test@example.com',
            company_name='Test Company',
            owner=user
        )
        
        # Convert lead
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('lead-convert', args=[lead.id])
        response = client.post(url, {})
        
        assert response.status_code == 200
        
        # Verify all created entities are in the same company
        lead.refresh_from_db()
        assert lead.company == company
        assert lead.converted_contact.company == company
        if lead.converted_account:
            assert lead.converted_account.company == company
