# core/models.py
# Authentication and Multi-Tenant Core Models

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import EmailValidator

# ========================================
# CUSTOM USER MANAGER
# ========================================

class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_superadmin', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_superadmin') is not True:
            raise ValueError('Superuser must have is_superadmin=True')
        
        return self.create_user(email, password, **extra_fields)

# ========================================
# COMPANY MODEL (Tenant)
# ========================================

class Company(models.Model):
    """
    Multi-tenant company/organization model.
    Each company represents a separate tenant with isolated data.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Company name")
    legal_name = models.CharField(max_length=255, blank=True, help_text="Legal business name")
    code = models.CharField(max_length=50, unique=True, help_text="Unique company code")
    tax_id = models.CharField(max_length=100, blank=True, help_text="Tax ID/EIN")
    
    # Contact Information
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Settings
    currency = models.CharField(max_length=3, default='USD', help_text="ISO currency code")
    timezone = models.CharField(max_length=50, default='UTC')
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    fiscal_year_start_month = models.IntegerField(default=1, help_text="1-12")
    
    # Branding
    logo_url = models.TextField(blank=True, help_text="URL to company logo")
    primary_color = models.CharField(max_length=7, default='#0066CC', help_text="Hex color code")
    
    # Status
    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(max_length=50, blank=True)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies_created'
    )
    updated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies_updated'
    )
    
    class Meta:
        db_table = 'companies'
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Auto-generate code if not provided
        if not self.code:
            self.code = self.name.upper().replace(' ', '_')[:50]
        super().save(*args, **kwargs)

# ========================================
# USER MODEL
# ========================================

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with email-based authentication.
    Supports multi-company access.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Authentication
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Personal Information
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    
    # Profile
    avatar_url = models.TextField(blank=True)
    title = models.CharField(max_length=100, blank=True, help_text="Job title")
    department = models.CharField(max_length=100, blank=True)
    
    # Email Verification
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True)
    
    # Password Reset
    password_reset_token = models.CharField(max_length=255, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    
    # Two-Factor Authentication
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=255, blank=True)
    
    # Session Tracking
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    login_count = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_superadmin = models.BooleanField(
        default=False,
        help_text="Superadmin has access to all companies and settings"
    )
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['email']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Returns the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    @property
    def is_staff(self):
        """Required for Django admin"""
        return self.is_superadmin
    
    def get_companies(self):
        """Get all companies this user has access to"""
        return Company.objects.filter(
            user_access__user=self,
            user_access__is_active=True
        )
    
    def get_primary_company(self):
        """Get user's primary company"""
        access = self.company_access.filter(
            is_primary=True,
            is_active=True
        ).first()
        return access.company if access else None
    
    def has_company_access(self, company):
        """Check if user has access to a company"""
        return self.company_access.filter(
            company=company,
            is_active=True
        ).exists()

# ========================================
# USER COMPANY ACCESS (Many-to-Many)
# ========================================

class UserCompanyAccess(models.Model):
    """
    Maps users to companies with roles and permissions.
    Allows users to access multiple companies.
    """
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Sales Manager'),
        ('sales_rep', 'Sales Representative'),
        ('viewer', 'Viewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='company_access'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='user_access'
    )
    
    # Role
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    
    # Permissions
    can_create = models.BooleanField(default=True)
    can_read = models.BooleanField(default=True)
    can_update = models.BooleanField(default=True)
    can_delete = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)
    
    # Status
    is_primary = models.BooleanField(
        default=False,
        help_text="User's default/primary company"
    )
    is_active = models.BooleanField(default=True)
    
    # Audit
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_grants_given'
    )
    granted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_company_access'
        verbose_name = 'User Company Access'
        verbose_name_plural = 'User Company Access'
        unique_together = [['user', 'company']]
        ordering = ['-is_primary', 'company__name']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['company']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.company.name} ({self.role})"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary companies for this user
        if self.is_primary:
            UserCompanyAccess.objects.filter(
                user=self.user,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)

# ========================================
# USER SESSION MODEL
# ========================================

class UserSession(models.Model):
    """
    Tracks user sessions for multi-device login management
    and security monitoring
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Active company for this session"
    )
    
    # Token Management
    token = models.CharField(max_length=500, unique=True)
    refresh_token = models.CharField(max_length=500, blank=True)
    expires_at = models.DateTimeField()
    
    # Session Info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def is_valid(self):
        """Check if session is still valid"""
        return timezone.now() < self.expires_at
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired sessions"""
        cls.objects.filter(expires_at__lt=timezone.now()).delete()

# ========================================
# BASE MODEL FOR COMPANY-ISOLATED DATA
# ========================================

class CompanyIsolatedModel(models.Model):
    """
    Abstract base model for all models that need company isolation.
    Automatically adds company foreign key and audit fields.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # Ensure company is set (will be set by middleware/view)
        if not self.company_id and hasattr(self, '_current_company'):
            self.company = self._current_company
        super().save(*args, **kwargs)