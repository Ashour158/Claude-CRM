# tests/conftest.py
# Pytest configuration and fixtures

import pytest
import os
import django

# Setup Django FIRST before any other imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Now import Django and DRF components
from django.conf import settings
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import tempfile
import shutil

# Import models after Django setup
from core.models import Company, UserCompanyAccess
from crm.models import Account, Contact, Lead
from activities.models import Activity, Task
from deals.models import Deal
from products.models import Product
import factory
from factory.django import DjangoModelFactory

User = get_user_model()

# Factory classes for test data generation
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True


class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company
    
    name = factory.Faker('company')
    code = factory.LazyFunction(lambda: f'COMP-{factory.Faker("uuid4").evaluate(None, None, {"locale": None})[0:8]}')
    domain = factory.LazyAttribute(lambda obj: f"{obj.name.lower().replace(' ', '')}.com")
    is_active = True


# Alias for organization (Company is the actual model used, not Organization)
OrganizationFactory = CompanyFactory


class AccountFactory(DjangoModelFactory):
    class Meta:
        model = Account
    
    name = factory.Faker('company')
    type = factory.Iterator(['customer', 'prospect', 'partner'])
    industry = factory.Faker('word')
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    is_active = True

class ContactFactory(DjangoModelFactory):
    class Meta:
        model = Contact
    
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    title = factory.Faker('job')
    is_active = True

class LeadFactory(DjangoModelFactory):
    class Meta:
        model = Lead
    
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    company_name = factory.Faker('company')
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    source = factory.Iterator(['website', 'referral', 'cold_call'])
    rating = factory.Iterator(['hot', 'warm', 'cold'])
    status = 'new'
    is_active = True

class ActivityFactory(DjangoModelFactory):
    class Meta:
        model = Activity
    
    activity_type = factory.Iterator(['call', 'email', 'meeting'])
    subject = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text')
    status = 'planned'
    priority = factory.Iterator(['low', 'medium', 'high'])

class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task
    
    title = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text')
    task_type = factory.Iterator(['call', 'email', 'meeting', 'follow_up'])
    status = 'not_started'
    priority = factory.Iterator(['low', 'medium', 'high'])

class DealFactory(DjangoModelFactory):
    class Meta:
        model = Deal
    
    name = factory.Faker('sentence', nb_words=3)
    amount = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    stage = factory.Iterator(['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won'])
    probability = factory.Faker('pyint', min_value=0, max_value=100)

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product
    
    name = factory.Faker('word')
    sku = factory.Sequence(lambda n: f"SKU-{n:06d}")
    description = factory.Faker('text')
    unit_price = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    is_active = True

# Pytest fixtures
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Setup database for tests"""
    with django_db_blocker.unblock():
        call_command('migrate', verbosity=0, interactive=False)

@pytest.fixture
def user():
    """Create a test user"""
    return UserFactory()

@pytest.fixture
def company():
    """Create a test company"""
    return CompanyFactory()


# Alias fixtures for compatibility
@pytest.fixture
def organization():
    """Create a test organization (alias for company)"""
    return CompanyFactory()


@pytest.fixture
def user_factory():
    """Factory for creating users"""
    return UserFactory


@pytest.fixture(autouse=True)
def tenant_context(request, db):
    """
    Auto-use fixture that provides tenant context for tests.
    Sets up company isolation for multi-tenant operations.
    """
    # This fixture automatically runs for all tests
    # In a real implementation, this would set thread-local or context variables
    # for tenant isolation
    pass


@pytest.fixture
def user_with_company(user, company):
    """Create a user with company access"""
    UserCompanyAccess.objects.create(
        user=user,
        company=company,
        role='admin',
        is_active=True
    )
    return user, company

@pytest.fixture
def api_client():
    """Create API client"""
    return APIClient()

@pytest.fixture
def authenticated_api_client(user_with_company):
    """Create authenticated API client"""
    user, company = user_with_company
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client

@pytest.fixture
def account(company, user):
    """Create a test account"""
    account = AccountFactory(company=company, owner=user)
    return account

@pytest.fixture
def contact(company, user, account):
    """Create a test contact"""
    contact = ContactFactory(company=company, owner=user, account=account)
    return contact

@pytest.fixture
def lead(company, user):
    """Create a test lead"""
    lead = LeadFactory(company=company, owner=user)
    return lead

@pytest.fixture
def activity(company, user):
    """Create a test activity"""
    activity = ActivityFactory(company=company, assigned_to=user)
    return activity

@pytest.fixture
def task(company, user):
    """Create a test task"""
    task = TaskFactory(company=company, assigned_to=user)
    return task

@pytest.fixture
def deal(company, user, account, contact):
    """Create a test deal"""
    deal = DealFactory(company=company, owner=user, account=account, contact=contact)
    return deal

@pytest.fixture
def product(company):
    """Create a test product"""
    product = ProductFactory(company=company)
    return product

@pytest.fixture
def multiple_accounts(company, user):
    """Create multiple test accounts"""
    return AccountFactory.create_batch(5, company=company, owner=user)

@pytest.fixture
def multiple_contacts(company, user, account):
    """Create multiple test contacts"""
    return ContactFactory.create_batch(5, company=company, owner=user, account=account)

@pytest.fixture
def multiple_leads(company, user):
    """Create multiple test leads"""
    return LeadFactory.create_batch(5, company=company, owner=user)

@pytest.fixture
def multiple_deals(company, user, account, contact):
    """Create multiple test deals"""
    return DealFactory.create_batch(5, company=company, owner=user, account=account, contact=contact)

@pytest.fixture
def temp_media_dir():
    """Create temporary media directory"""
    temp_dir = tempfile.mkdtemp()
    original_media_root = settings.MEDIA_ROOT
    settings.MEDIA_ROOT = temp_dir
    yield temp_dir
    settings.MEDIA_ROOT = original_media_root
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_cache():
    """Mock cache for testing"""
    from django.core.cache import cache
    cache.clear()
    return cache

@pytest.fixture
def mock_email_backend():
    """Mock email backend for testing"""
    from django.core import mail
    mail.outbox = []
    return mail

# Test data fixtures
@pytest.fixture
def sample_crm_data(company, user):
    """Create comprehensive test data"""
    # Create accounts
    accounts = AccountFactory.create_batch(3, company=company, owner=user)
    
    # Create contacts for each account
    contacts = []
    for account in accounts:
        contacts.extend(ContactFactory.create_batch(2, company=company, owner=user, account=account))
    
    # Create leads
    leads = LeadFactory.create_batch(5, company=company, owner=user)
    
    # Create deals
    deals = []
    for account in accounts:
        deals.extend(DealFactory.create_batch(2, company=company, owner=user, account=account))
    
    # Create activities
    activities = ActivityFactory.create_batch(10, company=company, assigned_to=user)
    
    # Create tasks
    tasks = TaskFactory.create_batch(10, company=company, assigned_to=user)
    
    # Create products
    products = ProductFactory.create_batch(5, company=company)
    
    return {
        'accounts': accounts,
        'contacts': contacts,
        'leads': leads,
        'deals': deals,
        'activities': activities,
        'tasks': tasks,
        'products': products
    }

# Performance testing fixtures
@pytest.fixture
def performance_data(company, user):
    """Create large dataset for performance testing"""
    # Create 100 accounts
    accounts = AccountFactory.create_batch(100, company=company, owner=user)
    
    # Create 500 contacts
    contacts = []
    for account in accounts[:50]:  # 2 contacts per account
        contacts.extend(ContactFactory.create_batch(2, company=company, owner=user, account=account))
    
    # Create 200 leads
    leads = LeadFactory.create_batch(200, company=company, owner=user)
    
    # Create 100 deals
    deals = []
    for account in accounts[:50]:
        deals.extend(DealFactory.create_batch(2, company=company, owner=user, account=account))
    
    return {
        'accounts': accounts,
        'contacts': contacts,
        'leads': leads,
        'deals': deals
    }

# Security testing fixtures
@pytest.fixture
def malicious_data():
    """Create malicious test data"""
    return {
        'xss_script': '<script>alert("XSS")</script>',
        'sql_injection': "'; DROP TABLE users; --",
        'path_traversal': '../../../etc/passwd',
        'command_injection': '; rm -rf /',
        'html_injection': '<img src=x onerror=alert(1)>',
        'json_injection': '{"malicious": "data"}',
        'xml_injection': '<?xml version="1.0"?><root><data>test</data></root>',
        'ldap_injection': '*)(uid=*',
        'no_sql_injection': '{"$where": "this.password == this.username"}',
        'template_injection': '{{7*7}}'
    }

# API testing fixtures
@pytest.fixture
def api_test_data(company, user):
    """Create data for API testing"""
    account = AccountFactory(company=company, owner=user)
    contact = ContactFactory(company=company, owner=user, account=account)
    lead = LeadFactory(company=company, owner=user)
    deal = DealFactory(company=company, owner=user, account=account, contact=contact)
    activity = ActivityFactory(company=company, assigned_to=user)
    task = TaskFactory(company=company, assigned_to=user)
    product = ProductFactory(company=company)
    
    return {
        'account': account,
        'contact': contact,
        'lead': lead,
        'deal': deal,
        'activity': activity,
        'task': task,
        'product': product
    }

# Database testing fixtures
@pytest.fixture
def db_transaction():
    """Database transaction for testing"""
    from django.db import transaction
    with transaction.atomic():
        yield

@pytest.fixture
def db_rollback():
    """Database rollback for testing"""
    from django.db import transaction
    with transaction.atomic():
        yield
        transaction.set_rollback(True)

# Cache testing fixtures
@pytest.fixture
def cache_test_data():
    """Cache test data"""
    return {
        'string_value': 'test_string',
        'int_value': 123,
        'float_value': 123.45,
        'bool_value': True,
        'list_value': [1, 2, 3, 4, 5],
        'dict_value': {'key1': 'value1', 'key2': 'value2'},
        'none_value': None
    }

# External service testing fixtures
@pytest.fixture
def mock_external_services():
    """Mock external services"""
    import responses
    
    with responses.RequestsMock() as rsps:
        # Mock external API responses
        rsps.add(
            responses.GET,
            'https://api.external.com/data',
            json={'status': 'success', 'data': 'test'},
            status=200
        )
        
        rsps.add(
            responses.POST,
            'https://api.external.com/webhook',
            json={'status': 'received'},
            status=200
        )
        
        yield rsps

# Custom pytest markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )
    config.addinivalue_line(
        "markers", "model: mark test as model test"
    )
    config.addinivalue_line(
        "markers", "view: mark test as view test"
    )
    config.addinivalue_line(
        "markers", "serializer: mark test as serializer test"
    )
    config.addinivalue_line(
        "markers", "middleware: mark test as middleware test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "cache: mark test as requiring cache"
    )
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as regression test"
    )

# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test file location
    for item in items:
        # Add markers based on test file path
        if 'test_models' in str(item.fspath):
            item.add_marker(pytest.mark.model)
        elif 'test_api' in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif 'test_views' in str(item.fspath):
            item.add_marker(pytest.mark.view)
        elif 'test_serializers' in str(item.fspath):
            item.add_marker(pytest.mark.serializer)
        elif 'test_middleware' in str(item.fspath):
            item.add_marker(pytest.mark.middleware)
        elif 'test_security' in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif 'test_performance' in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        
        # Add slow marker for tests with 'slow' in name
        if 'slow' in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Add integration marker for tests with 'integration' in name
        if 'integration' in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Add unit marker for tests with 'unit' in name
        if 'unit' in item.name:
            item.add_marker(pytest.mark.unit)
