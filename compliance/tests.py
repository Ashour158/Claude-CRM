# compliance/tests.py
# Tests for compliance features

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from core.models import Company, UserCompanyAccess
from compliance.models import (
    CompliancePolicy, DataResidency, DataSubjectRequest,
    SecretVault, AccessReview, RetentionPolicy
)
from compliance.policy_validator import PolicyValidator
from compliance.encryption import SecretEncryption, PIIEncryption, DataMasking

User = get_user_model()


class PolicyValidatorTests(TestCase):
    """Tests for policy validator"""
    
    def test_valid_policy(self):
        """Test validation of valid policy"""
        validator = PolicyValidator()
        
        policy_config = {
            'name': 'GDPR Policy',
            'version': '1.0.0',
            'rules': [
                {
                    'id': 'rule1',
                    'type': 'data_retention',
                    'action': 'delete'
                }
            ]
        }
        
        is_valid, errors = validator.validate(policy_config)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_invalid_policy_missing_name(self):
        """Test validation fails when name is missing"""
        validator = PolicyValidator()
        
        policy_config = {
            'version': '1.0.0',
            'rules': []
        }
        
        is_valid, errors = validator.validate(policy_config)
        
        self.assertFalse(is_valid)
        self.assertIn("Policy must have a 'name' field", errors)


class EncryptionTests(TestCase):
    """Tests for encryption utilities"""
    
    def test_secret_encryption_decryption(self):
        """Test secret encryption and decryption"""
        encryption = SecretEncryption()
        
        plaintext = "my-secret-api-key-12345"
        encrypted = encryption.encrypt(plaintext)
        decrypted = encryption.decrypt(encrypted)
        
        self.assertEqual(plaintext, decrypted)
    
    def test_pii_field_encryption(self):
        """Test PII field encryption"""
        email = "test@example.com"
        
        encrypted = PIIEncryption.encrypt_field(email, 'email')
        decrypted = PIIEncryption.decrypt_field(encrypted, 'email')
        
        self.assertEqual(email, decrypted)
        self.assertTrue(PIIEncryption.is_encrypted(encrypted))
    
    def test_data_masking(self):
        """Test data masking utilities"""
        # Test email masking
        email = "test@example.com"
        masked = DataMasking.mask_email(email)
        self.assertNotEqual(email, masked)
        self.assertIn('@', masked)
        
        # Test phone masking
        phone = "1234567890"
        masked_phone = DataMasking.mask_phone(phone)
        self.assertEqual(masked_phone[-4:], phone[-4:])


class CompliancePolicyModelTests(TestCase):
    """Tests for CompliancePolicy model"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        self.user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123"
        )
    
    def test_create_policy(self):
        """Test creating a compliance policy"""
        policy = CompliancePolicy.objects.create(
            company=self.company,
            name="GDPR Policy",
            policy_type="gdpr",
            policy_config={
                'name': 'GDPR Policy',
                'version': '1.0.0',
                'rules': []
            }
        )
        
        self.assertEqual(policy.name, "GDPR Policy")
        self.assertEqual(policy.status, "draft")
        self.assertFalse(policy.is_enforced)


class DataResidencyModelTests(TestCase):
    """Tests for DataResidency model"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
    
    def test_create_residency_config(self):
        """Test creating data residency configuration"""
        residency = DataResidency.objects.create(
            company=self.company,
            primary_region="us-east-1",
            allowed_regions=["us-east-1", "us-west-2"],
            storage_prefix="test-company-data",
            enforce_region=True
        )
        
        self.assertEqual(residency.primary_region, "us-east-1")
        self.assertTrue(residency.enforce_region)


class DataSubjectRequestModelTests(TestCase):
    """Tests for DataSubjectRequest model"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
    
    def test_create_dsr_request(self):
        """Test creating DSR request"""
        due_date = timezone.now() + timedelta(days=30)
        
        dsr = DataSubjectRequest.objects.create(
            company=self.company,
            request_type="erasure",
            subject_email="user@example.com",
            due_date=due_date
        )
        
        self.assertEqual(dsr.request_type, "erasure")
        self.assertEqual(dsr.status, "pending")
        self.assertTrue(dsr.can_rollback)
        self.assertIsNotNone(dsr.request_id)
        self.assertTrue(dsr.request_id.startswith("DSR-"))


class SecretVaultModelTests(TestCase):
    """Tests for SecretVault model"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
        self.user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123"
        )
    
    def test_create_secret(self):
        """Test creating a secret"""
        encryption = SecretEncryption()
        encrypted_value = encryption.encrypt("my-api-key")
        
        secret = SecretVault.objects.create(
            company=self.company,
            name="API Key",
            secret_type="api_key",
            secret_value=encrypted_value,
            rotation_enabled=True,
            rotation_days=90,
            owner=self.user
        )
        
        self.assertEqual(secret.name, "API Key")
        self.assertTrue(secret.rotation_enabled)
        self.assertEqual(secret.rotation_days, 90)


class AccessReviewModelTests(TestCase):
    """Tests for AccessReview model"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
    
    def test_create_access_review(self):
        """Test creating an access review"""
        review = AccessReview.objects.create(
            company=self.company,
            review_period_start=timezone.now().date() - timedelta(days=90),
            review_period_end=timezone.now().date()
        )
        
        self.assertEqual(review.status, "pending")
        self.assertIsNotNone(review.review_id)
        self.assertTrue(review.review_id.startswith("AR-"))


class RetentionPolicyModelTests(TestCase):
    """Tests for RetentionPolicy model"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
    
    def test_create_retention_policy(self):
        """Test creating a retention policy"""
        policy = RetentionPolicy.objects.create(
            company=self.company,
            name="Lead Retention",
            entity_type="Lead",
            retention_days=365,
            deletion_method="soft"
        )
        
        self.assertEqual(policy.name, "Lead Retention")
        self.assertEqual(policy.retention_days, 365)
        self.assertTrue(policy.is_active)
