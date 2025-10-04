# ========================================
# Django Models - Core CRM Entities
# File: crm/models/core.py
# ========================================

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

# ========================================
# CUSTOM USER MANAGER
# ========================================

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superadmin', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

# ========================================
# BASE MODELS
# ========================================

class BaseModel(models.Model):
    """Abstract base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class CompanyIsolatedModel(BaseModel):
    """Abstract model for company-isolated data (multi-tenant)"""
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='%(class)s_set')
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_created')
    updated_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_updated')
    
    class Meta:
        abstract = True

# ========================================
# COMPANY & USERS
# ========================================

class Company(BaseModel):
    """Multi-tenant company/organization"""
    
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    code = models.CharField(max_length=50, unique=True)
    tax_id = models.CharField(max_length=100, blank=True)
    
    # Contact
    email = models.EmailField(blank=True)
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
    currency = models.CharField(max_length=3, default='USD')
    timezone = models.CharField(max_length=50, default='UTC')
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    fiscal_year_start_month = models.IntegerField(default=1)
    
    # Branding
    logo_url = models.TextField(blank=True)
    primary_color = models.CharField(max_length=7, default='#0066CC')
    
    # Status
    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(max_length=50, blank=True)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'companies'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """Custom user model"""
    
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Personal Info
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    
    # Profile
    avatar_url = models.TextField(blank=True)
    title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    # Authentication
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True)
    password_reset_token = models.CharField(max_length=255, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    
    # 2FA
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=255, blank=True)
    
    # Session
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    login_count = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_superadmin = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        ordering = ['email']
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    @property
    def is_staff(self):
        return self.is_superadmin

class UserCompanyAccess(BaseModel):
    """Many-to-many relationship between users and companies"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('sales_rep', 'Sales Representative'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_access')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='user_access')
    
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    
    # Permissions
    can_create = models.BooleanField(default=True)
    can_read = models.BooleanField(default=True)
    can_update = models.BooleanField(default=True)
    can_delete = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)
    
    # Status
    is_primary = models.BooleanField(default=False)  # Primary company for user
    is_active = models.BooleanField(default=True)
    
    # Audit
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='access_granted')
    granted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_company_access'
        unique_together = ['user', 'company']
        ordering = ['-is_primary', 'company__name']
    
    def __str__(self):
        return f"{self.user.email} - {self.company.name} ({self.role})"

class UserSession(BaseModel):
    """User session management"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    
    token = models.CharField(max_length=500, unique=True)
    refresh_token = models.CharField(max_length=500, blank=True)
    expires_at = models.DateTimeField()
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-created_at']

# ========================================
# TERRITORY MANAGEMENT
# ========================================

class Territory(CompanyIsolatedModel):
    """Sales territories with hierarchy"""
    
    TYPE_CHOICES = [
        ('geographic', 'Geographic'),
        ('product', 'Product-based'),
        ('customer_segment', 'Customer Segment'),
        ('industry', 'Industry'),
    ]
    
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_territories')
    
    # Geographic criteria
    countries = ArrayField(models.CharField(max_length=3), blank=True, null=True)
    states = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    cities = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    postal_codes = ArrayField(models.CharField(max_length=20), blank=True, null=True)
    
    # Product criteria
    product_categories = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    product_ids = ArrayField(models.UUIDField(), blank=True, null=True)
    
    # Customer criteria
    customer_types = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    revenue_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    revenue_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    industries = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    
    # Settings
    currency = models.CharField(max_length=3, blank=True)
    quota_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quota_period = models.CharField(max_length=20, blank=True)  # monthly, quarterly, annual
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'territories'
        unique_together = ['company', 'code']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class TerritoryRule(CompanyIsolatedModel):
    """Automated territory assignment rules"""
    
    territory = models.ForeignKey(Territory, on_delete=models.CASCADE, related_name='rules')
    
    name = models.CharField(max_length=255)
    priority = models.IntegerField(default=0)  # Higher runs first
    
    conditions = models.JSONField()  # Flexible rule conditions
    
    auto_assign = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'territory_rules'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} (Priority: {self.priority})"

# ========================================
# CRM CORE ENTITIES
# ========================================

class Account(CompanyIsolatedModel):
    """Companies/Organizations (Customers)"""
    
    TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('prospect', 'Prospect'),
        ('partner', 'Partner'),
        ('competitor', 'Competitor'),
    ]
    
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    website = models.URLField(blank=True)
    
    account_type = models.CharField(max_length=50, choices=TYPE_CHOICES, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    employee_count = models.IntegerField(null=True, blank=True)
    
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    
    # Billing Address
    billing_address_line1 = models.CharField(max_length=255, blank=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)
    
    # Shipping Address
    shipping_address_line1 = models.CharField(max_length=255, blank=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)
    
    # Relationships
    parent_account = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subsidiaries')
    territory = models.ForeignKey(Territory, on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_accounts')
    
    # Settings
    payment_terms = models.IntegerField(default=30)  # Days
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    
    custom_fields = models.JSONField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'accounts'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Contact(CompanyIsolatedModel):
    """Individual people"""
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=255, blank=True)  # Auto-generated
    title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    
    # Social
    linkedin_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)
    
    # Relationships
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    reports_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_contacts')
    
    # Address
    mailing_address_line1 = models.CharField(max_length=255, blank=True)
    mailing_address_line2 = models.CharField(max_length=255, blank=True)
    mailing_city = models.CharField(max_length=100, blank=True)
    mailing_state = models.CharField(max_length=100, blank=True)
    mailing_postal_code = models.CharField(max_length=20, blank=True)
    mailing_country = models.CharField(max_length=100, blank=True)
    
    # Preferences
    email_opt_out = models.BooleanField(default=False)
    do_not_call = models.BooleanField(default=False)
    
    custom_fields = models.JSONField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'contacts'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return self.full_name or f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate full_name
        self.full_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)

class Lead(CompanyIsolatedModel):
    """Sales leads/prospects"""
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('unqualified', 'Unqualified'),
        ('converted', 'Converted'),
    ]
    
    RATING_CHOICES = [
        ('hot', 'Hot'),
        ('warm', 'Warm'),
        ('cold', 'Cold'),
    ]
    
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    lead_source = models.CharField(max_length=100, blank=True)
    lead_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new')
    rating = models.CharField(max_length=20, choices=RATING_CHOICES, blank=True)
    
    lead_score = models.IntegerField(default=0)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Business Info
    industry = models.CharField(max_length=100, blank=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    employee_count = models.IntegerField(null=True, blank=True)
    
    # Relationships
    territory = models.ForeignKey(Territory, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_leads')
    
    # Conversion
    converted_at = models.DateTimeField(null=True, blank=True)
    converted_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='converted_from_leads')
    converted_contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='converted_from_leads')
    converted_deal_id = models.UUIDField(null=True, blank=True)
    
    description = models.TextField(blank=True)
    custom_fields = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'leads'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.full_name or f"{self.first_name} {self.last_name}" or self.company_name

# ========================================
# TO BE CONTINUED IN NEXT FILE
# Next: Deals, Activities, Products, Quotes
# ========================================