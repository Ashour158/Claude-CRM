# tests/crm/accounts/test_account_model.py
"""
Tests for Account model
"""
import pytest
from django.utils import timezone
from crm.accounts.models import Account
from crm.accounts.services.account_service import AccountService
from crm.accounts.selectors.account_selector import AccountSelector
from core.models import Company, User


@pytest.fixture
def organization():
    """Create test organization"""
    return Company.objects.create(
        name='Test Company',
        code='TEST001',
        is_active=True
    )


@pytest.fixture
def user(organization):
    """Create test user"""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    return user


@pytest.mark.django_db
class TestAccountModel:
    """Test Account model"""
    
    def test_create_account(self, organization, user):
        """Test creating an account"""
        account = Account.objects.create(
            organization=organization,
            name='Acme Corporation',
            email='contact@acme.com',
            account_type='customer',
            created_by=user
        )
        
        assert account.id is not None
        assert account.name == 'Acme Corporation'
        assert account.organization == organization
        assert account.created_by == user
        assert account.is_active is True
    
    def test_tenant_manager_scoping(self, organization, user):
        """Test that TenantManager properly scopes queries"""
        # Create another organization
        other_org = Company.objects.create(
            name='Other Company',
            code='OTHER001'
        )
        
        # Create accounts in both organizations
        account1 = Account.objects.create(
            organization=organization,
            name='Account 1'
        )
        account2 = Account.objects.create(
            organization=other_org,
            name='Account 2'
        )
        
        # Query for specific organization
        accounts = Account.objects.for_organization(organization)
        
        assert account1 in accounts
        assert account2 not in accounts
        assert accounts.count() == 1


@pytest.mark.django_db
class TestAccountService:
    """Test AccountService"""
    
    def test_create_account_service(self, organization, user):
        """Test creating account via service"""
        account_data = {
            'name': 'Service Account',
            'email': 'service@example.com',
            'account_type': 'prospect',
            'industry': 'technology'
        }
        
        account = AccountService.create_account(
            organization=organization,
            data=account_data,
            user=user
        )
        
        assert account.id is not None
        assert account.name == 'Service Account'
        assert account.email == 'service@example.com'
        assert account.created_by == user
        assert account.updated_by == user
