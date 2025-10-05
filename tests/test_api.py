# tests/test_api.py
# Comprehensive API testing

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from activities.models import Activity, Task
from core.models import Company, UserCompanyAccess
from crm.models import Account, Contact, Lead
from deals.models import Deal
from products.models import Product

User = get_user_model()

class TestAuthenticationAPI(APITestCase):
    """Test authentication API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123"
        )
        self.company = Company.objects.create(name="Test Company")
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )

    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse('core:register')
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123',
            'password2': 'newpass123',
            'company_name': 'New Company'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_user_login(self):
        """Test user login endpoint"""
        url = reverse('core:token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertIn('company', response.data)

    def test_token_refresh(self):
        """Test token refresh endpoint"""
        refresh = RefreshToken.for_user(self.user)
        url = reverse('core:token_refresh')
        data = {'refresh': str(refresh)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_user_profile(self):
        """Test user profile endpoint"""
        self.client.force_authenticate(user=self.user)
        url = reverse('core:user_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_health_check(self):
        """Test health check endpoint"""
        url = reverse('core:health_check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)

class TestCRMAPI(APITestCase):
    """Test CRM API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123"
        )
        self.company = Company.objects.create(name="Test Company")
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )
        self.client.force_authenticate(user=self.user)

    def test_account_list(self):
        """Test account list endpoint"""
        Account.objects.create(
            company=self.company,
            name="Test Account",
            type="customer",
            owner=self.user
        )
        url = reverse('crm:account-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_account_create(self):
        """Test account creation endpoint"""
        url = reverse('crm:account-list')
        data = {
            'name': 'New Account',
            'type': 'customer',
            'industry': 'Technology',
            'email': 'account@example.com',
            'phone': '+1234567890'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Account')

    def test_contact_list(self):
        """Test contact list endpoint"""
        account = Account.objects.create(
            company=self.company,
            name="Test Account"
        )
        Contact.objects.create(
            company=self.company,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            account=account,
            owner=self.user
        )
        url = reverse('crm:contact-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_contact_create(self):
        """Test contact creation endpoint"""
        account = Account.objects.create(
            company=self.company,
            name="Test Account"
        )
        url = reverse('crm:contact-list')
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'phone': '+1234567890',
            'account': account.id,
            'title': 'Manager'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'Jane')

    def test_lead_list(self):
        """Test lead list endpoint"""
        Lead.objects.create(
            company=self.company,
            first_name="Lead",
            last_name="Person",
            email="lead@example.com",
            company_name="Lead Company",
            source="website",
            rating="hot",
            owner=self.user
        )
        url = reverse('crm:lead-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_lead_create(self):
        """Test lead creation endpoint"""
        url = reverse('crm:lead-list')
        data = {
            'first_name': 'New',
            'last_name': 'Lead',
            'email': 'newlead@example.com',
            'company_name': 'New Lead Company',
            'source': 'referral',
            'rating': 'warm',
            'phone': '+1234567890'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'New')

class TestActivityAPI(APITestCase):
    """Test activity API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123"
        )
        self.company = Company.objects.create(name="Test Company")
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )
        self.client.force_authenticate(user=self.user)

    def test_activity_list(self):
        """Test activity list endpoint"""
        Activity.objects.create(
            company=self.company,
            activity_type="call",
            subject="Test Call",
            activity_date="2024-01-01 10:00:00",
            assigned_to=self.user
        )
        url = reverse('activities:activity-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_activity_create(self):
        """Test activity creation endpoint"""
        url = reverse('activities:activity-list')
        data = {
            'activity_type': 'meeting',
            'subject': 'Test Meeting',
            'description': 'Test meeting description',
            'activity_date': '2024-01-01 14:00:00',
            'duration_minutes': 60,
            'priority': 'high'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['activity_type'], 'meeting')

    def test_task_list(self):
        """Test task list endpoint"""
        Task.objects.create(
            company=self.company,
            title="Test Task",
            description="Test task description",
            task_type="follow_up",
            due_date="2024-01-01 17:00:00",
            assigned_to=self.user
        )
        url = reverse('activities:task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_task_create(self):
        """Test task creation endpoint"""
        url = reverse('activities:task-list')
        data = {
            'title': 'New Task',
            'description': 'New task description',
            'task_type': 'research',
            'due_date': '2024-01-02 17:00:00',
            'priority': 'medium'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Task')

class TestDealAPI(APITestCase):
    """Test deal API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123"
        )
        self.company = Company.objects.create(name="Test Company")
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )
        self.account = Account.objects.create(
            company=self.company,
            name="Test Account"
        )
        self.contact = Contact.objects.create(
            company=self.company,
            first_name="John",
            last_name="Doe",
            account=self.account
        )
        self.client.force_authenticate(user=self.user)

    def test_deal_list(self):
        """Test deal list endpoint"""
        Deal.objects.create(
            company=self.company,
            name="Test Deal",
            account=self.account,
            contact=self.contact,
            amount=10000.00,
            stage="prospecting",
            owner=self.user
        )
        url = reverse('deals:deal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_deal_create(self):
        """Test deal creation endpoint"""
        url = reverse('deals:deal-list')
        data = {
            'name': 'New Deal',
            'account': self.account.id,
            'contact': self.contact.id,
            'amount': 15000.00,
            'stage': 'qualification',
            'expected_close_date': '2024-03-01',
            'probability': 75
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Deal')

    def test_deal_pipeline(self):
        """Test deal pipeline endpoint"""
        Deal.objects.create(
            company=self.company,
            name="Deal 1",
            account=self.account,
            contact=self.contact,
            amount=10000.00,
            stage="prospecting",
            owner=self.user
        )
        Deal.objects.create(
            company=self.company,
            name="Deal 2",
            account=self.account,
            contact=self.contact,
            amount=20000.00,
            stage="qualification",
            owner=self.user
        )
        url = reverse('deals:deal-pipeline')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stages', response.data)

class TestProductAPI(APITestCase):
    """Test product API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123"
        )
        self.company = Company.objects.create(name="Test Company")
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )
        self.client.force_authenticate(user=self.user)

    def test_product_list(self):
        """Test product list endpoint"""
        Product.objects.create(
            company=self.company,
            name="Test Product",
            sku="TEST-001",
            description="Test product description",
            unit_price=100.00
        )
        url = reverse('products:product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_product_create(self):
        """Test product creation endpoint"""
        url = reverse('products:product-list')
        data = {
            'name': 'New Product',
            'sku': 'NEW-001',
            'description': 'New product description',
            'unit_price': 150.00,
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Product')

class TestAPIFiltering(APITestCase):
    """Test API filtering and search functionality"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123"
        )
        self.company = Company.objects.create(name="Test Company")
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )
        self.client.force_authenticate(user=self.user)

    def test_account_filtering(self):
        """Test account filtering by type and industry"""
        Account.objects.create(
            company=self.company,
            name="Customer Account",
            type="customer",
            industry="Technology",
            owner=self.user
        )
        Account.objects.create(
            company=self.company,
            name="Prospect Account",
            type="prospect",
            industry="Healthcare",
            owner=self.user
        )

        # Filter by type
        url = reverse('crm:account-list')
        response = self.client.get(url, {'type': 'customer'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Filter by industry
        response = self.client.get(url, {'industry': 'Technology'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_contact_search(self):
        """Test contact search functionality"""
        Contact.objects.create(
            company=self.company,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            owner=self.user
        )
        Contact.objects.create(
            company=self.company,
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            owner=self.user
        )

        # Search by name
        url = reverse('crm:contact-list')
        response = self.client.get(url, {'search': 'John'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # Search by email
        response = self.client.get(url, {'search': 'jane@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

class TestAPIPagination(APITestCase):
    """Test API pagination functionality"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123"
        )
        self.company = Company.objects.create(name="Test Company")
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )
        self.client.force_authenticate(user=self.user)

    def test_account_pagination(self):
        """Test account pagination"""
        # Create multiple accounts
        for i in range(25):
            Account.objects.create(
                company=self.company,
                name=f"Account {i}",
                type="customer",
                owner=self.user
            )

        url = reverse('crm:account-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertEqual(len(response.data['results']), 20)  # Default page size

    def test_contact_pagination(self):
        """Test contact pagination"""
        # Create multiple contacts
        for i in range(25):
            Contact.objects.create(
                company=self.company,
                first_name=f"Contact{i}",
                last_name="User",
                email=f"contact{i}@example.com",
                owner=self.user
            )

        url = reverse('crm:contact-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertEqual(len(response.data['results']), 20)  # Default page size

class TestAPIErrorHandling(APITestCase):
    """Test API error handling and validation"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123"
        )
        self.company = Company.objects.create(name="Test Company")
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )
        self.client.force_authenticate(user=self.user)

    def test_invalid_data_validation(self):
        """Test API validation with invalid data"""
        url = reverse('crm:account-list')
        data = {
            'name': '',  # Empty name should fail
            'type': 'invalid_type',  # Invalid type
            'email': 'invalid-email'  # Invalid email format
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        self.client.logout()
        url = reverse('crm:account-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_not_found_error(self):
        """Test 404 error for non-existent resources"""
        url = reverse('crm:account-detail', kwargs={'pk': '99999999-9999-9999-9999-999999999999'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
