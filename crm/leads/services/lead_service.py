# crm/leads/services/lead_service.py
"""
Lead service layer for business logic
"""
from django.db import transaction
from crm.leads.models import Lead


class LeadService:
    """Service for lead operations"""
    
    @staticmethod
    @transaction.atomic
    def create_lead(organization, data, user=None):
        """
        Create a new lead
        
        Args:
            organization: Company instance
            data: Dict with lead data
            user: User creating the lead
            
        Returns:
            Lead instance
        """
        lead = Lead(
            organization=organization,
            **data
        )
        if user:
            lead.created_by = user
            lead.updated_by = user
        lead.save()
        return lead
    
    @staticmethod
    @transaction.atomic
    def update_lead(lead, data, user=None):
        """
        Update an existing lead
        
        Args:
            lead: Lead instance
            data: Dict with updated data
            user: User updating the lead
            
        Returns:
            Updated Lead instance
        """
        for key, value in data.items():
            if hasattr(lead, key):
                setattr(lead, key, value)
        
        if user:
            lead.updated_by = user
        lead.save()
        return lead
    
    @staticmethod
    def calculate_lead_score(lead):
        """
        Calculate lead score based on various factors
        
        Args:
            lead: Lead instance
            
        Returns:
            Score (0-100)
        """
        score = 0
        
        # Email provided (+10)
        if lead.email:
            score += 10
        
        # Phone provided (+5)
        if lead.phone or lead.mobile:
            score += 5
        
        # Company name provided (+10)
        if lead.company_name:
            score += 10
        
        # Industry known (+5)
        if lead.industry:
            score += 5
        
        # Revenue data (+10)
        if lead.annual_revenue:
            score += 10
        
        # Budget provided (+15)
        if lead.budget:
            score += 15
        
        # Rating boost
        if lead.rating == 'hot':
            score += 20
        elif lead.rating == 'warm':
            score += 10
        
        # Recent activity boost
        if lead.days_since_creation <= 7:
            score += 10
        
        return min(score, 100)  # Cap at 100
