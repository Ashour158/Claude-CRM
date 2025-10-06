# tests/test_api_lead_convert_serializer.py
"""Tests for lead conversion API endpoint and serializer."""

import pytest
from rest_framework import status
from crm.models import Lead, Contact, Account
from django.urls import reverse


@pytest.mark.django_db
class TestLeadConversionAPI:
    """Test lead conversion endpoint."""
    
    def test_lead_convert_returns_200(self, authenticated_api_client, lead):
        """Test that lead conversion returns 200 OK."""
        url = reverse('lead-convert', args=[lead.id])
        response = authenticated_api_client.post(url, {})
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_lead_convert_creates_contact(self, authenticated_api_client, lead):
        """Test that converting lead creates a contact."""
        initial_contact_count = Contact.objects.count()
        
        url = reverse('lead-convert', args=[lead.id])
        response = authenticated_api_client.post(url, {})
        
        assert response.status_code == status.HTTP_200_OK
        assert Contact.objects.count() == initial_contact_count + 1
    
    def test_lead_convert_response_serializer(self, authenticated_api_client, lead):
        """Test that conversion response matches LeadConversionResultSerializer."""
        url = reverse('lead-convert', args=[lead.id])
        response = authenticated_api_client.post(url, {})
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check expected serializer fields
        assert 'lead_id' in response.data
        assert 'contact_id' in response.data
        assert 'account_id' in response.data
        assert 'created_account' in response.data
        assert 'status' in response.data
        
        assert response.data['status'] == 'converted'
    
    def test_lead_convert_creates_account_when_company_name_present(
        self, authenticated_api_client, company, user
    ):
        """Test that account is created when lead has company_name."""
        lead = Lead.objects.create(
            company=company,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            company_name='Test Company',
            owner=user
        )
        
        initial_account_count = Account.objects.count()
        
        url = reverse('lead-convert', args=[lead.id])
        response = authenticated_api_client.post(url, {})
        
        assert response.status_code == status.HTTP_200_OK
        assert Account.objects.count() == initial_account_count + 1
        assert response.data['created_account'] is True
        assert response.data['account_id'] is not None
    
    def test_lead_convert_already_converted_returns_400(self, authenticated_api_client, lead):
        """Test that converting an already converted lead returns 400."""
        # Convert the lead first
        url = reverse('lead-convert', args=[lead.id])
        authenticated_api_client.post(url, {})
        
        # Try converting again
        response = authenticated_api_client.post(url, {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_lead_convert_updates_lead_status(self, authenticated_api_client, lead):
        """Test that converting lead updates its status."""
        assert lead.status != 'converted'
        
        url = reverse('lead-convert', args=[lead.id])
        response = authenticated_api_client.post(url, {})
        
        assert response.status_code == status.HTTP_200_OK
        
        lead.refresh_from_db()
        assert lead.status == 'converted'
        assert lead.converted_contact is not None
    
    def test_lead_convert_duplicate_account_detection(
        self, authenticated_api_client, company, user
    ):
        """Test that duplicate account detection works (reuses existing account)."""
        # Create an existing account
        existing_account = Account.objects.create(
            company=company,
            name='Existing Company',
            owner=user
        )
        
        # Create a lead with same company name
        lead = Lead.objects.create(
            company=company,
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            company_name='Existing Company',  # Same name
            owner=user
        )
        
        initial_account_count = Account.objects.count()
        
        url = reverse('lead-convert', args=[lead.id])
        response = authenticated_api_client.post(url, {})
        
        assert response.status_code == status.HTTP_200_OK
        # Should not create a new account
        assert Account.objects.count() == initial_account_count
        assert response.data['created_account'] is False
        assert response.data['account_id'] == existing_account.id
