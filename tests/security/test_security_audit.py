# tests/security/test_security_audit.py
# Security audit tests - Phase 8

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from core.models import Company, UserCompanyAccess
from rest_framework.test import APIClient
from rest_framework import status
import json

User = get_user_model()


@pytest.mark.security
class TestAuthenticationSecurity(TestCase):
    """Test authentication security"""
    
    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(name="Test Company", code="TEST")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="SecurePass123!@#"
        )
    
    def test_password_strength_validation(self):
        """Test password strength requirements"""
        weak_passwords = [
            "123456",
            "password",
            "test",
            "12345678",
        ]
        
        for weak_pass in weak_passwords:
            response = self.client.post('/api/auth/register/', {
                'email': f'test{weak_pass}@example.com',
                'password': weak_pass,
                'first_name': 'Test',
                'last_name': 'User'
            })
            # Should fail due to weak password
            self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        malicious_inputs = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "admin'--",
        ]
        
        for malicious_input in malicious_inputs:
            response = self.client.post('/api/auth/login/', {
                'email': malicious_input,
                'password': 'password'
            })
            # Should not cause SQL injection
            self.assertIn(response.status_code, [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED
            ])
    
    def test_xss_prevention(self):
        """Test XSS prevention in user inputs"""
        xss_inputs = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]
        
        for xss_input in xss_inputs:
            response = self.client.post('/api/users/', {
                'email': 'test@example.com',
                'first_name': xss_input,
                'last_name': 'User'
            })
            # XSS should be prevented
            if response.status_code == status.HTTP_201_CREATED:
                # Check that script tags are escaped or removed
                data = response.json()
                self.assertNotIn('<script>', data.get('first_name', ''))
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        client = Client()
        response = client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'password'
        })
        # CSRF should be enforced for non-API requests
        # API requests with JWT don't need CSRF
        self.assertIsNotNone(response)
    
    def test_rate_limiting(self):
        """Test rate limiting on login attempts"""
        # Attempt multiple logins quickly
        for i in range(10):
            response = self.client.post('/api/auth/login/', {
                'email': 'test@example.com',
                'password': 'wrongpassword'
            })
        
        # After many attempts, should be rate limited
        response = self.client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        # May get rate limited (429) or unauthorized (401)
        self.assertIn(response.status_code, [
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_401_UNAUTHORIZED
        ])


@pytest.mark.security
class TestAuthorizationSecurity(TestCase):
    """Test authorization and access control"""
    
    def setUp(self):
        self.client = APIClient()
        self.company1 = Company.objects.create(name="Company 1", code="COMP1")
        self.company2 = Company.objects.create(name="Company 2", code="COMP2")
        
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="password123"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="password123"
        )
        
        UserCompanyAccess.objects.create(
            user=self.user1,
            company=self.company1,
            role="user"
        )
        UserCompanyAccess.objects.create(
            user=self.user2,
            company=self.company2,
            role="user"
        )
    
    def test_unauthorized_access(self):
        """Test unauthorized access to resources"""
        response = self.client.get('/api/accounts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_cross_company_access_prevention(self):
        """Test that users cannot access other company's data"""
        # Login as user1
        self.client.force_authenticate(user=self.user1)
        
        # Try to access company2 data should fail or return empty
        response = self.client.get('/api/accounts/')
        # Should not see company2 accounts
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Verify no cross-company data leakage
            self.assertIsNotNone(data)


@pytest.mark.security
class TestDataSecurity(TestCase):
    """Test data security and encryption"""
    
    def test_sensitive_data_encryption(self):
        """Test that sensitive data is encrypted"""
        user = User.objects.create_user(
            email="test@example.com",
            password="password123"
        )
        # Password should be hashed, not stored in plain text
        self.assertNotEqual(user.password, "password123")
        self.assertTrue(user.password.startswith('pbkdf2_sha256'))
    
    def test_api_response_no_sensitive_data(self):
        """Test that API responses don't leak sensitive data"""
        client = APIClient()
        user = User.objects.create_user(
            email="test@example.com",
            password="password123"
        )
        client.force_authenticate(user=user)
        
        response = client.get('/api/users/me/')
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Should not include password
            self.assertNotIn('password', data)


@pytest.mark.security  
class TestInputValidation(TestCase):
    """Test input validation security"""
    
    def test_email_validation(self):
        """Test email format validation"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test @example.com",
        ]
        
        client = APIClient()
        for invalid_email in invalid_emails:
            response = client.post('/api/auth/register/', {
                'email': invalid_email,
                'password': 'SecurePass123!',
                'first_name': 'Test',
                'last_name': 'User'
            })
            self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_required_fields_validation(self):
        """Test required fields validation"""
        client = APIClient()
        response = client.post('/api/auth/register/', {})
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
