# crm/accounts/services/account_service.py
"""
Account service layer for business logic
"""
from django.db import transaction
from crm.accounts.models import Account


class AccountService:
    """Service for account operations"""
    
    @staticmethod
    @transaction.atomic
    def create_account(organization, data, user=None):
        """
        Create a new account
        
        Args:
            organization: Company instance
            data: Dict with account data
            user: User creating the account
            
        Returns:
            Account instance
        """
        account = Account(
            organization=organization,
            **data
        )
        if user:
            account.created_by = user
            account.updated_by = user
        account.save()
        return account
    
    @staticmethod
    @transaction.atomic
    def update_account(account, data, user=None):
        """
        Update an existing account
        
        Args:
            account: Account instance
            data: Dict with updated data
            user: User updating the account
            
        Returns:
            Updated Account instance
        """
        for key, value in data.items():
            if hasattr(account, key):
                setattr(account, key, value)
        
        if user:
            account.updated_by = user
        account.save()
        return account
    
    @staticmethod
    @transaction.atomic
    def soft_delete_account(account, user=None):
        """
        Soft delete an account (set is_active=False)
        
        Args:
            account: Account instance
            user: User deleting the account
            
        Returns:
            Updated Account instance
        """
        account.is_active = False
        if user:
            account.updated_by = user
        account.save()
        return account
    
    @staticmethod
    def validate_account_data(data):
        """
        Validate account data before create/update
        
        Args:
            data: Dict with account data
            
        Returns:
            Tuple (is_valid, errors)
        """
        errors = {}
        
        if not data.get('name'):
            errors['name'] = 'Name is required'
        
        if data.get('email') and '@' not in data['email']:
            errors['email'] = 'Invalid email format'
        
        return len(errors) == 0, errors
