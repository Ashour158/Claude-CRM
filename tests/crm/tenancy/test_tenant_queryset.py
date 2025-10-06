# tests/crm/tenancy/test_tenant_queryset.py
"""
Tests for tenant scoping functionality
"""
import pytest
from crm.accounts.models import Account
from crm.leads.models import Lead
from core.models import Company, User, UserCompanyAccess


@pytest.fixture
def org1():
    """First organization"""
    return Company.objects.create(name='Org 1', code='ORG1')


@pytest.fixture
def org2():
    """Second organization"""
    return Company.objects.create(name='Org 2', code='ORG2')


@pytest.fixture
def user():
    """Test user"""
    return User.objects.create_user(
        email='user@example.com',
        password='testpass123'
    )


@pytest.mark.django_db
class TestTenantQuerySet:
    """Test tenant queryset scoping"""
    
    def test_for_organization_filters_correctly(self, org1, org2):
        """Test that for_organization properly filters"""
        # Create accounts in both orgs
        acc1 = Account.objects.create(organization=org1, name='Acc 1')
        acc2 = Account.objects.create(organization=org2, name='Acc 2')
        
        # Query org1
        org1_accounts = Account.objects.for_organization(org1)
        assert acc1 in org1_accounts
        assert acc2 not in org1_accounts
        assert org1_accounts.count() == 1
        
        # Query org2
        org2_accounts = Account.objects.for_organization(org2)
        assert acc2 in org2_accounts
        assert acc1 not in org2_accounts
        assert org2_accounts.count() == 1
    
    def test_for_user_organizations(self, org1, org2, user):
        """Test filtering by user's organizations"""
        # Give user access to org1 only
        UserCompanyAccess.objects.create(
            user=user,
            company=org1,
            is_active=True
        )
        
        # Create leads in both orgs
        lead1 = Lead.objects.create(
            organization=org1,
            first_name='John',
            last_name='Doe',
            email='john@test.com'
        )
        lead2 = Lead.objects.create(
            organization=org2,
            first_name='Jane',
            last_name='Smith',
            email='jane@test.com'
        )
        
        # Query user's accessible leads
        user_leads = Lead.objects.for_user_organizations(user)
        assert lead1 in user_leads
        assert lead2 not in user_leads
    
    def test_created_by_user_filter(self, org1, user):
        """Test filtering by creator"""
        # Create accounts by different users
        acc1 = Account.objects.create(
            organization=org1,
            name='Acc 1',
            created_by=user
        )
        acc2 = Account.objects.create(
            organization=org1,
            name='Acc 2'
        )
        
        # Filter by creator
        user_accounts = Account.objects.for_organization(org1).created_by_user(user)
        assert acc1 in user_accounts
        assert acc2 not in user_accounts
