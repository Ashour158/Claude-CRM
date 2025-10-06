# crm/accounts/selectors/account_selector.py
"""
Account selector layer for data retrieval
"""
from django.db.models import Q, Count
from crm.accounts.models import Account


class AccountSelector:
    """Selector for account queries"""
    
    @staticmethod
    def get_account(account_id, organization):
        """
        Get a single account by ID
        
        Args:
            account_id: Account ID
            organization: Company instance
            
        Returns:
            Account instance or None
        """
        try:
            return Account.objects.for_organization(organization).get(id=account_id)
        except Account.DoesNotExist:
            return None
    
    @staticmethod
    def list_accounts(organization, filters=None, order_by='-created_at'):
        """
        List accounts for an organization
        
        Args:
            organization: Company instance
            filters: Optional dict of filters
            order_by: Order by field
            
        Returns:
            QuerySet of accounts
        """
        queryset = Account.objects.for_organization(organization)
        
        if filters:
            if 'account_type' in filters:
                queryset = queryset.filter(account_type=filters['account_type'])
            if 'industry' in filters:
                queryset = queryset.filter(industry=filters['industry'])
            if 'is_active' in filters:
                queryset = queryset.filter(is_active=filters['is_active'])
            if 'owner' in filters:
                queryset = queryset.filter(owner=filters['owner'])
        
        return queryset.order_by(order_by)
    
    @staticmethod
    def search_accounts(organization, query):
        """
        Search accounts by name, email, or other fields
        
        Args:
            organization: Company instance
            query: Search query string
            
        Returns:
            QuerySet of matching accounts
        """
        return Account.objects.for_organization(organization).filter(
            Q(name__icontains=query) |
            Q(legal_name__icontains=query) |
            Q(email__icontains=query) |
            Q(description__icontains=query)
        )
    
    @staticmethod
    def get_account_statistics(organization):
        """
        Get account statistics for an organization
        
        Args:
            organization: Company instance
            
        Returns:
            Dict with statistics
        """
        accounts = Account.objects.for_organization(organization)
        
        return {
            'total': accounts.count(),
            'active': accounts.filter(is_active=True).count(),
            'by_type': {
                account_type: accounts.filter(account_type=account_type).count()
                for account_type, _ in Account.TYPE_CHOICES
            },
            'by_industry': {
                industry: accounts.filter(industry=industry).count()
                for industry, _ in Account.INDUSTRY_CHOICES
            }
        }
