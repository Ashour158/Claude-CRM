# tests/crm/leads/test_lead_conversion.py
"""
Tests for Lead conversion
"""
import pytest
from crm.leads.models import Lead
from crm.leads.services.conversion_service import ConversionService
from crm.accounts.models import Account
from crm.contacts.models import Contact
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
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def qualified_lead(organization, user):
    """Create a qualified lead"""
    return Lead.objects.create(
        organization=organization,
        first_name='John',
        last_name='Doe',
        company_name='Acme Corp',
        email='john@acme.com',
        phone='555-1234',
        lead_status='qualified',
        created_by=user
    )


@pytest.mark.django_db
class TestLeadConversion:
    """Test lead conversion functionality"""
    
    def test_convert_lead_creates_account(self, qualified_lead, user):
        """Test that converting a lead creates an account"""
        account, contact, deal = ConversionService.convert_lead(
            lead=qualified_lead,
            create_deal=False,
            user=user
        )
        
        assert account is not None
        assert account.name == 'Acme Corp'
        assert account.email == 'john@acme.com'
        assert account.organization == qualified_lead.organization
    
    def test_convert_lead_creates_contact(self, qualified_lead, user):
        """Test that converting a lead creates a contact"""
        account, contact, deal = ConversionService.convert_lead(
            lead=qualified_lead,
            create_deal=False,
            user=user
        )
        
        assert contact is not None
        assert contact.first_name == 'John'
        assert contact.last_name == 'Doe'
        assert contact.email == 'john@acme.com'
        assert contact.account == account
    
    def test_convert_lead_with_deal(self, qualified_lead, user):
        """Test converting lead with deal creation"""
        account, contact, deal = ConversionService.convert_lead(
            lead=qualified_lead,
            create_deal=True,
            deal_data={'amount': 50000},
            user=user
        )
        
        assert deal is not None
        assert deal.account == account
        assert deal.contact == contact
    
    def test_lead_status_updated_after_conversion(self, qualified_lead, user):
        """Test that lead status is updated to converted"""
        ConversionService.convert_lead(
            lead=qualified_lead,
            create_deal=False,
            user=user
        )
        
        qualified_lead.refresh_from_db()
        assert qualified_lead.lead_status == 'converted'
        assert qualified_lead.converted_at is not None
        assert qualified_lead.converted_account is not None
        assert qualified_lead.converted_contact is not None


@pytest.mark.django_db
class TestLeadConversionIdempotent:
    """Test lead conversion idempotency"""
    
    def test_cannot_convert_lead_twice(self, qualified_lead, user):
        """Test that a lead cannot be converted twice"""
        # First conversion
        account1, contact1, deal1 = ConversionService.convert_lead(
            lead=qualified_lead,
            create_deal=False,
            user=user
        )
        
        # Second conversion should raise error
        with pytest.raises(ValueError, match="already been converted"):
            ConversionService.convert_lead(
                lead=qualified_lead,
                create_deal=False,
                user=user
            )
        
        # Verify original conversion unchanged
        qualified_lead.refresh_from_db()
        assert qualified_lead.converted_account == account1
        assert qualified_lead.converted_contact == contact1
    
    def test_can_convert_lead_validation(self, qualified_lead):
        """Test validation before conversion"""
        can_convert, reason = ConversionService.can_convert_lead(qualified_lead)
        assert can_convert is True
        assert reason == ""
        
        # Convert the lead
        ConversionService.convert_lead(qualified_lead)
        
        # Now should not be able to convert
        can_convert, reason = ConversionService.can_convert_lead(qualified_lead)
        assert can_convert is False
        assert "already been converted" in reason
