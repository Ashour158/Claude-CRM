# tests/unit/test_models_comprehensive.py
# Comprehensive unit tests for models - Phase 8

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from core.models import Company, UserCompanyAccess
from datetime import datetime, timedelta
from decimal import Decimal

User = get_user_model()


@pytest.mark.unit
@pytest.mark.model
class TestUserModel(TestCase):
    """Comprehensive tests for User model"""
    
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST001"
        )
    
    def test_user_creation_with_email(self):
        """Test user creation with valid email"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertTrue(user.is_active)
    
    def test_user_creation_without_email_fails(self):
        """Test that user creation without email fails"""
        with self.assertRaises((ValueError, TypeError)):
            User.objects.create_user(email="", password="testpass123")
    
    def test_superuser_creation(self):
        """Test superuser creation"""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


@pytest.mark.unit
@pytest.mark.model
class TestCompanyModel(TestCase):
    """Comprehensive tests for Company model"""
    
    def test_company_creation(self):
        """Test company creation with valid data"""
        company = Company.objects.create(
            name="Test Company",
            code="TEST001",
            email="contact@test.com"
        )
        self.assertEqual(company.name, "Test Company")
        self.assertEqual(company.code, "TEST001")
        self.assertTrue(company.is_active)
    
    def test_company_string_representation(self):
        """Test company __str__ method"""
        company = Company.objects.create(name="Test Co", code="TEST")
        self.assertEqual(str(company), "Test Co")
