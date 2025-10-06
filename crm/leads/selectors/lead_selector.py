# crm/leads/selectors/lead_selector.py
"""
Lead selector layer for data retrieval
"""
from django.db.models import Q
from crm.leads.models import Lead


class LeadSelector:
    """Selector for lead queries"""
    
    @staticmethod
    def get_lead(lead_id, organization):
        """
        Get a single lead by ID
        
        Args:
            lead_id: Lead ID
            organization: Company instance
            
        Returns:
            Lead instance or None
        """
        try:
            return Lead.objects.for_organization(organization).get(id=lead_id)
        except Lead.DoesNotExist:
            return None
    
    @staticmethod
    def get_lead_for_update(lead_id, organization, user=None):
        """
        Get lead for update with locking
        
        Args:
            lead_id: Lead ID
            organization: Company instance
            user: Optional user for permission checks
            
        Returns:
            Lead instance or None
        """
        try:
            return Lead.objects.for_organization(organization).select_for_update().get(id=lead_id)
        except Lead.DoesNotExist:
            return None
    
    @staticmethod
    def list_leads(organization, filters=None, order_by='-created_at'):
        """
        List leads for an organization
        
        Args:
            organization: Company instance
            filters: Optional dict of filters
            order_by: Order by field
            
        Returns:
            QuerySet of leads
        """
        queryset = Lead.objects.for_organization(organization)
        
        if filters:
            if 'lead_status' in filters:
                queryset = queryset.filter(lead_status=filters['lead_status'])
            if 'lead_source' in filters:
                queryset = queryset.filter(lead_source=filters['lead_source'])
            if 'rating' in filters:
                queryset = queryset.filter(rating=filters['rating'])
            if 'owner' in filters:
                queryset = queryset.filter(owner=filters['owner'])
            if 'is_active' in filters:
                queryset = queryset.filter(is_active=filters['is_active'])
        
        return queryset.order_by(order_by)
    
    @staticmethod
    def search_leads(organization, query):
        """
        Search leads by name, email, company, or other fields
        
        Args:
            organization: Company instance
            query: Search query string
            
        Returns:
            QuerySet of matching leads
        """
        return Lead.objects.for_organization(organization).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(email__icontains=query) |
            Q(description__icontains=query)
        )
