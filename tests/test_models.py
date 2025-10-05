# tests/test_models.py
# Comprehensive model testing

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from activities.models import Activity, Task
from core.models import Company, UserCompanyAccess
from crm.models import Account, Contact, Lead
from deals.models import Deal
from products.models import Product

User = get_user_model()

class TestCoreModels(TestCase):
    """Test core authentication and multi-tenant models"""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            domain="test.com"
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        self.user_access = UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )

    def test_user_creation(self):
        """Test user model creation and validation"""
        user = User.objects.create_user(
            email="newuser@example.com",
            first_name="New",
            last_name="User"
        )
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.get_full_name(), "New User")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_company_creation(self):
        """Test company model creation"""
        company = Company.objects.create(
            name="New Company",
            domain="newcompany.com"
        )
        self.assertEqual(company.name, "New Company")
        self.assertTrue(company.is_active)

    def test_user_company_access(self):
        """Test user company access relationship"""
        self.assertEqual(self.user_access.user, self.user)
        self.assertEqual(self.user_access.company, self.company)
        self.assertEqual(self.user_access.role, "admin")
        self.assertTrue(self.user_access.is_active)

class TestCRMModels(TestCase):
    """Test CRM core models"""

    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )

    def test_account_creation(self):
        """Test account model creation and validation"""
        account = Account.objects.create(
            company=self.company,
            name="Test Account",
            type="customer",
            industry="Technology",
            owner=self.user
        )
        self.assertEqual(account.name, "Test Account")
        self.assertEqual(account.type, "customer")
        self.assertEqual(account.owner, self.user)
        self.assertTrue(account.is_active)

    def test_contact_creation(self):
        """Test contact model creation"""
        account = Account.objects.create(
            company=self.company,
            name="Test Account"
        )
        contact = Contact.objects.create(
            company=self.company,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            account=account,
            owner=self.user
        )
        self.assertEqual(contact.full_name, "John Doe")
        self.assertEqual(contact.account, account)
        self.assertTrue(contact.is_active)

    def test_lead_creation(self):
        """Test lead model creation and scoring"""
        lead = Lead.objects.create(
            company=self.company,
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            company_name="Lead Company",
            source="website",
            rating="hot",
            owner=self.user
        )
        self.assertEqual(lead.full_name, "Jane Smith")
        self.assertEqual(lead.rating, "hot")
        self.assertEqual(lead.status, "new")

        # Test lead scoring
        score = lead.calculate_lead_score()
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

class TestActivityModels(TestCase):
    """Test activity and task models"""

    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )

    def test_activity_creation(self):
        """Test activity model creation"""
        activity = Activity.objects.create(
            company=self.company,
            activity_type="call",
            subject="Test Call",
            description="Test call description",
            activity_date="2024-01-01 10:00:00",
            assigned_to=self.user
        )
        self.assertEqual(activity.activity_type, "call")
        self.assertEqual(activity.subject, "Test Call")
        self.assertEqual(activity.assigned_to, self.user)
        self.assertEqual(activity.status, "planned")

    def test_task_creation(self):
        """Test task model creation"""
        task = Task.objects.create(
            company=self.company,
            title="Test Task",
            description="Test task description",
            task_type="follow_up",
            due_date="2024-01-01 17:00:00",
            assigned_to=self.user
        )
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.task_type, "follow_up")
        self.assertEqual(task.status, "not_started")
        self.assertEqual(task.progress_percentage, 0)

class TestDealModels(TestCase):
    """Test deal and pipeline models"""

    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
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

    def test_deal_creation(self):
        """Test deal model creation"""
        deal = Deal.objects.create(
            company=self.company,
            name="Test Deal",
            account=self.account,
            contact=self.contact,
            amount=10000.00,
            stage="prospecting",
            owner=self.user
        )
        self.assertEqual(deal.name, "Test Deal")
        self.assertEqual(deal.amount, 10000.00)
        self.assertEqual(deal.stage, "prospecting")
        self.assertEqual(deal.owner, self.user)

class TestProductModels(TestCase):
    """Test product and pricing models"""

    def setUp(self):
        self.company = Company.objects.create(name="Test Company")

    def test_product_creation(self):
        """Test product model creation"""
        product = Product.objects.create(
            company=self.company,
            name="Test Product",
            sku="TEST-001",
            description="Test product description",
            unit_price=100.00,
            is_active=True
        )
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.sku, "TEST-001")
        self.assertEqual(product.unit_price, 100.00)
        self.assertTrue(product.is_active)

class TestModelValidation(TestCase):
    """Test model validation and constraints"""

    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

    def test_email_validation(self):
        """Test email field validation"""
        with self.assertRaises(ValidationError):
            contact = Contact(
                company=self.company,
                first_name="Test",
                last_name="User",
                email="invalid-email"
            )
            contact.full_clean()

    def test_required_fields(self):
        """Test required field validation"""
        with self.assertRaises(ValidationError):
            account = Account(company=self.company)
            account.full_clean()

    def test_unique_constraints(self):
        """Test unique field constraints"""
        # Create first user
        User.objects.create_user(
            email="unique@example.com",
            first_name="First",
            last_name="User"
        )

        # Try to create second user with same email
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="unique@example.com",
                first_name="Second",
                last_name="User"
            )

class TestModelMethods(TestCase):
    """Test model methods and properties"""

    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )

    def test_account_methods(self):
        """Test account model methods"""
        account = Account.objects.create(
            company=self.company,
            name="Test Account",
            billing_address_line1="123 Main St",
            billing_city="Test City",
            billing_state="TS",
            billing_postal_code="12345",
            billing_country="US"
        )

        # Test get_full_address method
        address = account.get_full_address('billing')
        self.assertIn("123 Main St", address)
        self.assertIn("Test City", address)
        self.assertIn("12345", address)

    def test_contact_methods(self):
        """Test contact model methods"""
        account = Account.objects.create(
            company=self.company,
            name="Test Account"
        )
        contact = Contact.objects.create(
            company=self.company,
            first_name="John",
            last_name="Doe",
            account=account,
            mailing_address_line1="456 Oak St",
            mailing_city="Contact City",
            mailing_state="CS",
            mailing_postal_code="54321",
            mailing_country="US"
        )

        # Test get_full_address method
        address = contact.get_full_address('mailing')
        self.assertIn("456 Oak St", address)
        self.assertIn("Contact City", address)

    def test_lead_methods(self):
        """Test lead model methods"""
        lead = Lead.objects.create(
            company=self.company,
            first_name="Jane",
            last_name="Smith",
            company_name="Lead Company",
            rating="hot"
        )

        # Test is_hot property
        self.assertTrue(lead.is_hot)

        # Test calculate_lead_score method
        score = lead.calculate_lead_score()
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

class TestModelRelationships(TestCase):
    """Test model relationships and foreign keys"""

    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        UserCompanyAccess.objects.create(
            user=self.user,
            company=self.company,
            role="admin"
        )

    def test_account_contact_relationship(self):
        """Test account-contact relationship"""
        account = Account.objects.create(
            company=self.company,
            name="Test Account"
        )
        contact = Contact.objects.create(
            company=self.company,
            first_name="John",
            last_name="Doe",
            account=account
        )

        # Test forward relationship
        self.assertEqual(contact.account, account)

        # Test reverse relationship
        self.assertIn(contact, account.contacts.all())

    def test_contact_activities_relationship(self):
        """Test contact-activities relationship"""
        account = Account.objects.create(
            company=self.company,
            name="Test Account"
        )
        contact = Contact.objects.create(
            company=self.company,
            first_name="John",
            last_name="Doe",
            account=account
        )

        activity = Activity.objects.create(
            company=self.company,
            activity_type="call",
            subject="Test Call",
            activity_date="2024-01-01 10:00:00",
            content_object=contact
        )

        # Test generic foreign key relationship
        self.assertEqual(activity.content_object, contact)
