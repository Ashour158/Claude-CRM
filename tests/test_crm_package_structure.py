"""
Test that the new crm_package structure can be imported without errors.

This test ensures that the scaffolding is properly set up and doesn't
introduce any import errors or circular dependencies.
"""

import pytest


class TestCRMPackageStructure:
    """Test suite for CRM package structure."""
    
    def test_package_imports(self):
        """Test that main package can be imported."""
        import crm_package
        assert crm_package.__version__ == "0.1.0"
    
    def test_core_module_imports(self):
        """Test that core module can be imported."""
        import crm_package.core
        assert hasattr(crm_package.core, 'tenancy')
    
    def test_tenancy_imports(self):
        """Test that tenancy module can be imported."""
        from crm_package.core import tenancy
        
        # Check that key components are available
        assert hasattr(tenancy, 'get_current_organization_id')
        assert hasattr(tenancy, 'set_current_organization_id')
        assert hasattr(tenancy, 'TenancyMiddleware')
        assert hasattr(tenancy, 'TenantOwnedModel')
    
    def test_tenancy_context(self):
        """Test that tenancy context functions work."""
        from crm_package.core.tenancy import (
            get_current_organization_id,
            set_current_organization_id,
            clear_current_organization,
        )
        import uuid
        
        # Initially should be None
        assert get_current_organization_id() is None
        
        # Set an organization
        test_org_id = uuid.uuid4()
        set_current_organization_id(test_org_id)
        assert get_current_organization_id() == test_org_id
        
        # Clear organization
        clear_current_organization()
        assert get_current_organization_id() is None
    
    def test_domain_modules_importable(self):
        """Test that all domain modules can be imported."""
        domains = [
            'accounts',
            'contacts',
            'leads',
            'deals',
            'activities',
            'products',
            'marketing',
            'vendors',
            'sales',
            'workflow',
            'territories',
            'system',
            'shared',
        ]
        
        for domain in domains:
            module = __import__(f'crm_package.{domain}', fromlist=[domain])
            assert module is not None, f"Failed to import crm_package.{domain}"
    
    def test_services_selectors_structure(self):
        """Test that services and selectors can be imported."""
        # Test accounts as example
        from crm_package.accounts import services, selectors
        
        # Check that placeholder functions exist
        assert hasattr(services, 'create_account')
        assert hasattr(services, 'update_account')
        assert hasattr(selectors, 'get_account_by_id')
        assert hasattr(selectors, 'list_accounts')
    
    def test_shared_utilities(self):
        """Test that shared utilities can be imported."""
        from crm_package.shared import utils, enums, mixins, validators
        
        # Check utils
        assert hasattr(utils, 'clean_dict')
        assert hasattr(utils, 'chunk_list')
        
        # Check enums
        assert hasattr(enums, 'AccountType')
        assert hasattr(enums, 'LeadStatus')
        assert hasattr(enums, 'Priority')
        
        # Check validators
        assert hasattr(validators, 'validate_phone_number')
    
    def test_core_exceptions(self):
        """Test that core exceptions can be imported."""
        from crm_package.core import exceptions
        
        assert hasattr(exceptions, 'CRMBaseException')
        assert hasattr(exceptions, 'TenancyException')
        assert hasattr(exceptions, 'OrganizationAccessDenied')
    
    def test_core_constants(self):
        """Test that core constants can be imported."""
        from crm_package.core import constants
        
        assert hasattr(constants, 'API_VERSION')
        assert constants.API_VERSION == "v1"
        assert hasattr(constants, 'DEFAULT_PAGE_SIZE')
        assert hasattr(constants, 'PRIORITY_CHOICES')
    
    def test_api_router_imports(self):
        """Test that API router can be imported."""
        from crm_package import api_router
        
        # Should have urlpatterns (even if empty)
        assert hasattr(api_router, 'urlpatterns')
        assert isinstance(api_router.urlpatterns, list)


class TestTenancyContextIsolation:
    """Test that tenancy context is properly isolated."""
    
    def test_context_isolation_between_tests(self):
        """Ensure context doesn't leak between test runs."""
        from crm_package.core.tenancy import get_current_organization_id
        
        # Should always start clean
        assert get_current_organization_id() is None
    
    def test_context_set_get_clear(self):
        """Test full context lifecycle."""
        from crm_package.core.tenancy import (
            get_current_organization_id,
            set_current_organization_id,
            clear_current_organization,
        )
        import uuid
        
        # Set
        org1 = uuid.uuid4()
        set_current_organization_id(org1)
        assert get_current_organization_id() == org1
        
        # Override
        org2 = uuid.uuid4()
        set_current_organization_id(org2)
        assert get_current_organization_id() == org2
        
        # Clear
        clear_current_organization()
        assert get_current_organization_id() is None


class TestSharedUtilities:
    """Test shared utility functions."""
    
    def test_clean_dict_removes_none(self):
        """Test that clean_dict removes None values."""
        from crm_package.shared.utils import clean_dict
        
        data = {'a': 1, 'b': None, 'c': 'test', 'd': None}
        cleaned = clean_dict(data)
        
        assert 'a' in cleaned
        assert 'c' in cleaned
        assert 'b' not in cleaned
        assert 'd' not in cleaned
    
    def test_chunk_list(self):
        """Test list chunking utility."""
        from crm_package.shared.utils import chunk_list
        
        items = list(range(10))
        chunks = chunk_list(items, 3)
        
        assert len(chunks) == 4
        assert chunks[0] == [0, 1, 2]
        assert chunks[1] == [3, 4, 5]
        assert chunks[2] == [6, 7, 8]
        assert chunks[3] == [9]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
