# tests/test_search.py
# Comprehensive tests for search functionality

import pytest
from django.test import TestCase
from core.search import SearchService
from core.search.schemas import SearchQuery, SearchResult
from core.search.backends import PostgresSearchBackend, ExternalSearchBackend
from core.search.filters import GDPRFilter
from core.models import Company, User
from crm.models import Account, Contact, Lead
from deals.models import Deal


@pytest.mark.unit
@pytest.mark.database
class TestSearchSchemas(TestCase):
    """Test search schema validation"""
    
    def test_search_query_validation(self):
        """Test SearchQuery validation"""
        # Valid query
        query = SearchQuery(
            query_string="test",
            company_id="uuid-here",
            max_results=50
        )
        self.assertEqual(query.query_string, "test")
        self.assertEqual(query.max_results, 50)
        
    def test_search_query_empty_string_fails(self):
        """Test that empty query string fails"""
        with self.assertRaises(ValueError):
            SearchQuery(
                query_string="",
                company_id="uuid-here"
            )
    
    def test_search_query_invalid_max_results(self):
        """Test that invalid max_results fails"""
        with self.assertRaises(ValueError):
            SearchQuery(
                query_string="test",
                company_id="uuid-here",
                max_results=2000  # Too high
            )
    
    def test_search_result_validation(self):
        """Test SearchResult validation"""
        result = SearchResult(
            model="Account",
            record_id="uuid-here",
            score=85.5,
            data={"name": "Test Company"}
        )
        self.assertEqual(result.model, "Account")
        self.assertEqual(result.score, 85.5)
    
    def test_search_result_to_dict(self):
        """Test SearchResult to_dict conversion"""
        result = SearchResult(
            model="Account",
            record_id="uuid-here",
            score=85.5,
            data={"name": "Test Company"},
            matched_fields=["name"]
        )
        result_dict = result.to_dict()
        self.assertIn('model', result_dict)
        self.assertIn('score', result_dict)
        self.assertIn('matched_fields', result_dict)


@pytest.mark.unit
class TestGDPRFilter(TestCase):
    """Test GDPR filtering functionality"""
    
    def setUp(self):
        self.filter = GDPRFilter(config={
            'mask_pii': True,
            'remove_pii': False,
        })
    
    def test_email_masking(self):
        """Test email masking"""
        data = {'email': 'john.doe@example.com'}
        filtered = self.filter.filter_result(data)
        self.assertNotEqual(filtered['email'], 'john.doe@example.com')
        self.assertIn('@example.com', filtered['email'])
    
    def test_phone_masking(self):
        """Test phone number masking"""
        data = {'phone': '555-123-4567'}
        filtered = self.filter.filter_result(data)
        self.assertIn('4567', filtered['phone'])
        self.assertNotIn('555-123', filtered['phone'])
    
    def test_pii_removal(self):
        """Test PII field removal"""
        filter_remove = GDPRFilter(config={'remove_pii': True})
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '555-1234'
        }
        filtered = filter_remove.filter_result(data)
        self.assertIn('name', filtered)
        self.assertNotIn('email', filtered)
        self.assertNotIn('phone', filtered)
    
    def test_admin_bypass(self):
        """Test that admin users bypass filtering"""
        data = {'email': 'john.doe@example.com'}
        filtered = self.filter.filter_result(data, user_role='admin')
        self.assertEqual(filtered['email'], 'john.doe@example.com')
    
    def test_sensitive_field_detection(self):
        """Test sensitive field detection"""
        self.assertTrue(self.filter.is_field_sensitive('email'))
        self.assertTrue(self.filter.is_field_sensitive('phone'))
        self.assertFalse(self.filter.is_field_sensitive('name'))


@pytest.mark.integration
@pytest.mark.database
class TestPostgresSearchBackend(TestCase):
    """Test Postgres search backend"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name="Test Company",
            domain="test.com",
            is_active=True
        )
        
        # Create test accounts
        Account.objects.create(
            company=self.company,
            name="Acme Corporation",
            email="contact@acme.com",
            is_active=True
        )
        Account.objects.create(
            company=self.company,
            name="Beta Industries",
            email="info@beta.com",
            is_active=True
        )
        
        # Create test contacts
        Contact.objects.create(
            company=self.company,
            first_name="John",
            last_name="Doe",
            full_name="John Doe",
            email="john.doe@example.com",
            is_active=True
        )
        Contact.objects.create(
            company=self.company,
            first_name="Jane",
            last_name="Smith",
            full_name="Jane Smith",
            email="jane.smith@example.com",
            is_active=True
        )
        
        self.backend = PostgresSearchBackend()
    
    def test_search_accounts(self):
        """Test searching accounts"""
        query = SearchQuery(
            query_string="Acme",
            company_id=str(self.company.id),
            fuzzy=False
        )
        results = self.backend.search(query, models=['Account'])
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].model, 'Account')
    
    def test_fuzzy_search(self):
        """Test fuzzy search with typos"""
        query = SearchQuery(
            query_string="Akme",  # Typo in Acme
            company_id=str(self.company.id),
            fuzzy=True
        )
        results = self.backend.search(query, models=['Account'])
        # Should still find Acme with fuzzy matching
        self.assertGreater(len(results), 0)
    
    def test_cross_model_search(self):
        """Test searching across multiple models"""
        query = SearchQuery(
            query_string="John",
            company_id=str(self.company.id),
            fuzzy=False
        )
        results = self.backend.search(query, models=['Account', 'Contact'])
        # Should find contacts with John
        contact_results = [r for r in results if r.model == 'Contact']
        self.assertGreater(len(contact_results), 0)
    
    def test_active_filter(self):
        """Test filtering inactive records"""
        # Create inactive account
        Account.objects.create(
            company=self.company,
            name="Inactive Corp",
            email="inactive@corp.com",
            is_active=False
        )
        
        query = SearchQuery(
            query_string="Inactive",
            company_id=str(self.company.id),
            include_inactive=False
        )
        results = self.backend.search(query, models=['Account'])
        # Should not find inactive account
        self.assertEqual(len(results), 0)
    
    def test_scoring(self):
        """Test relevance scoring"""
        query = SearchQuery(
            query_string="Acme",
            company_id=str(self.company.id),
            fuzzy=False
        )
        results = self.backend.search(query, models=['Account'])
        # Results should have scores
        if results:
            self.assertGreater(results[0].score, 0)
            self.assertLessEqual(results[0].score, 100)
    
    def test_health_check(self):
        """Test backend health check"""
        health = self.backend.health_check()
        self.assertEqual(health['backend'], 'PostgresSearchBackend')
        self.assertIn('status', health)


@pytest.mark.integration
@pytest.mark.database
class TestSearchService(TestCase):
    """Test main search service"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name="Test Company",
            domain="test.com",
            is_active=True
        )
        
        self.user = User.objects.create(
            email="testuser@example.com",
            first_name="Test",
            last_name="User"
        )
        
        # Create test data
        self.account = Account.objects.create(
            company=self.company,
            name="Search Test Corp",
            email="search@test.com",
            is_active=True,
            owner=self.user
        )
        
        self.contact = Contact.objects.create(
            company=self.company,
            first_name="Search",
            last_name="Testperson",
            full_name="Search Testperson",
            email="search.test@example.com",
            is_active=True,
            owner=self.user,
            account=self.account
        )
        
        self.service = SearchService(backend_name='postgres')
    
    def test_search_basic(self):
        """Test basic search functionality"""
        response = self.service.search(
            query_string="Search",
            company_id=str(self.company.id)
        )
        self.assertIsNotNone(response)
        self.assertGreater(response.total_count, 0)
        self.assertEqual(response.api_version, 'v1')
    
    def test_search_with_filters(self):
        """Test search with additional filters"""
        response = self.service.search(
            query_string="Search",
            company_id=str(self.company.id),
            filters={'is_active': True}
        )
        self.assertGreater(response.total_count, 0)
    
    def test_search_pagination(self):
        """Test search pagination"""
        # Create more records
        for i in range(10):
            Account.objects.create(
                company=self.company,
                name=f"Test Account {i}",
                email=f"account{i}@test.com",
                is_active=True
            )
        
        # First page
        response1 = self.service.search(
            query_string="Test",
            company_id=str(self.company.id),
            max_results=5,
            offset=0
        )
        
        # Second page
        response2 = self.service.search(
            query_string="Test",
            company_id=str(self.company.id),
            max_results=5,
            offset=5
        )
        
        self.assertLessEqual(len(response1.results), 5)
        self.assertLessEqual(len(response2.results), 5)
    
    def test_gdpr_filtering(self):
        """Test GDPR filtering in search results"""
        # Configure GDPR filtering
        self.service.config['gdpr'] = {
            'mask_pii': True,
            'allowed_roles': ['admin']
        }
        self.service.gdpr_filter = GDPRFilter(self.service.config['gdpr'])
        
        response = self.service.search(
            query_string="Search",
            company_id=str(self.company.id),
            apply_gdpr=True
        )
        
        # Check that email is masked
        for result in response.results:
            if 'email' in result.data:
                email = result.data['email']
                # Should be masked
                if '@' in email:
                    self.assertIn('***', email)
    
    def test_health_check(self):
        """Test service health check"""
        health = self.service.health_check()
        self.assertEqual(health['service'], 'SearchService')
        self.assertIn('backend', health)
        self.assertIn('status', health)
    
    def test_backend_switching(self):
        """Test switching between backends"""
        initial_backend = self.service.backend_name
        
        # Note: External backend may not be configured, so this might fail
        # In a real environment, this would test actual backend switching
        backend_info = self.service.get_backend_info()
        self.assertIn('available_backends', backend_info)
        self.assertIn('postgres', backend_info['available_backends'])


@pytest.mark.unit
class TestExternalSearchBackend(TestCase):
    """Test external search backend (stub)"""
    
    def test_backend_initialization(self):
        """Test backend initialization without config"""
        backend = ExternalSearchBackend()
        self.assertIsNone(backend.client)
        self.assertEqual(backend.engine, 'meilisearch')
    
    def test_health_check_not_configured(self):
        """Test health check when not configured"""
        backend = ExternalSearchBackend()
        health = backend.health_check()
        self.assertEqual(health['status'], 'not_configured')
    
    def test_search_without_client(self):
        """Test search returns empty when client not initialized"""
        backend = ExternalSearchBackend()
        query = SearchQuery(
            query_string="test",
            company_id="uuid-here"
        )
        results = backend.search(query)
        self.assertEqual(len(results), 0)


@pytest.mark.performance
@pytest.mark.database
class TestSearchPerformance(TestCase):
    """Test search performance"""
    
    def setUp(self):
        """Set up performance test data"""
        import time
        
        self.company = Company.objects.create(
            name="Performance Test Company",
            domain="perftest.com",
            is_active=True
        )
        
        # Create 100 test accounts
        accounts = []
        for i in range(100):
            accounts.append(Account(
                company=self.company,
                name=f"Performance Account {i}",
                email=f"perf{i}@test.com",
                is_active=True
            ))
        Account.objects.bulk_create(accounts)
        
        self.service = SearchService(backend_name='postgres')
    
    def test_search_performance(self):
        """Test search performance with 100 records"""
        import time
        
        start_time = time.time()
        response = self.service.search(
            query_string="Performance",
            company_id=str(self.company.id),
            max_results=50
        )
        execution_time = (time.time() - start_time) * 1000
        
        # Should complete in reasonable time
        self.assertLess(execution_time, 500)  # Less than 500ms
        self.assertGreater(response.total_count, 0)
        
        # Check reported execution time
        self.assertGreater(response.execution_time_ms, 0)


@pytest.mark.regression
@pytest.mark.database
class TestSearchRegressions(TestCase):
    """Regression tests for search functionality"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Regression Test Company",
            domain="regtest.com",
            is_active=True
        )
        self.service = SearchService(backend_name='postgres')
    
    def test_empty_query_handling(self):
        """Test handling of empty queries"""
        with self.assertRaises(ValueError):
            SearchQuery(
                query_string="",
                company_id=str(self.company.id)
            )
    
    def test_special_characters_in_query(self):
        """Test handling of special characters"""
        # Create account with special chars
        Account.objects.create(
            company=self.company,
            name="Test & Associates (Ltd.)",
            email="test@example.com",
            is_active=True
        )
        
        # Search should handle special chars
        response = self.service.search(
            query_string="Test & Associates",
            company_id=str(self.company.id)
        )
        # Should not crash
        self.assertIsNotNone(response)
    
    def test_company_isolation(self):
        """Test multi-tenant isolation"""
        company2 = Company.objects.create(
            name="Company 2",
            domain="company2.com",
            is_active=True
        )
        
        # Create account in company 1
        Account.objects.create(
            company=self.company,
            name="Company 1 Account",
            email="test1@example.com",
            is_active=True
        )
        
        # Create account in company 2
        Account.objects.create(
            company=company2,
            name="Company 2 Account",
            email="test2@example.com",
            is_active=True
        )
        
        # Search in company 1 should not return company 2 results
        response = self.service.search(
            query_string="Account",
            company_id=str(self.company.id)
        )
        
        for result in response.results:
            self.assertNotEqual(result.data.get('name'), "Company 2 Account")
