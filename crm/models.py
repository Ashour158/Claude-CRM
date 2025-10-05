# crm/models.py
# Complete CRM Models - Accounts, Contacts, Leads, Deals, Tags

from django.db import models
from django.core.validators import EmailValidator
from core.models import CompanyIsolatedModel, User
from territories.models import Territory

# ========================================
# TAG MODEL
# ========================================

class Tag(CompanyIsolatedModel):
    """Tag model for categorizing records"""
    
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'crm_tag'
        ordering = ['name']
    
    def __str__(self):
        return self.name

# ========================================
# ACCOUNT MODEL
# ========================================

class Account(CompanyIsolatedModel):
    """
    Account model represents a company/organization.
    This is a customer, prospect, partner, or competitor.
    """
    
    TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('prospect', 'Prospect'),
        ('partner', 'Partner'),
        ('competitor', 'Competitor'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, db_index=True)
    legal_name = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique account identifier"
    )
    website = models.URLField(blank=True)
    
    # Classification
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        blank=True,
        db_index=True
    )
    industry = models.CharField(max_length=100, blank=True, db_index=True)
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual revenue in company currency"
    )
    employee_count = models.IntegerField(null=True, blank=True)
    
    # Contact Information
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
    parent_account = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subsidiaries',
        help_text="Parent account for hierarchy"
    )
    territory = models.ForeignKey(
        Territory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accounts'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_accounts'
    )
    
    # Financial Settings
    payment_terms = models.IntegerField(
        default=30,
        help_text="Payment terms in days"
    )
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    tax_id = models.CharField(max_length=100, blank=True)
    
    # Custom Fields (JSON for flexibility)
    custom_fields = models.JSONField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Description/Notes
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'crm_account'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'name']),
            models.Index(fields=['company', 'type']),
            models.Index(fields=['company', 'owner']),
            models.Index(fields=['company', 'territory']),
            models.Index(fields=['company', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_full_address(self, address_type='billing'):
        """Get formatted address"""
        if address_type == 'billing':
            parts = [
                self.billing_address_line1,
                self.billing_address_line2,
                self.billing_city,
                self.billing_state,
                self.billing_postal_code,
                self.billing_country
            ]
        else:
            parts = [
                self.shipping_address_line1,
                self.shipping_address_line2,
                self.shipping_city,
                self.shipping_state,
                self.shipping_postal_code,
                self.shipping_country
            ]
        
        return ', '.join([p for p in parts if p])
    
    def save(self, *args, **kwargs):
        # Auto-generate account number if not provided
        if not self.account_number:
            # Simple auto-increment approach
            # In production, implement a more robust numbering system
            last_account = Account.objects.filter(
                company=self.company
            ).order_by('-created_at').first()
            
            if last_account and last_account.account_number:
                try:
                    last_num = int(last_account.account_number.split('-')[-1])
                    self.account_number = f"ACC-{last_num + 1:06d}"
                except:
                    self.account_number = f"ACC-000001"
            else:
                self.account_number = f"ACC-000001"
        
        super().save(*args, **kwargs)
    
    @property
    def contacts_count(self):
        """Count of contacts"""
        return self.contacts.count()
    
    @property
    def deals_count(self):
        """Count of deals"""
        return self.deals.count()
    
    @property
    def open_deals_value(self):
        """Total value of open deals"""
        from django.db.models import Sum
        result = self.deals.filter(status='open').aggregate(
            total=Sum('amount')
        )
        return result['total'] or 0

# ========================================
# CONTACT MODEL
# ========================================

class Contact(CompanyIsolatedModel):
    """
    Contact model represents an individual person.
    Contacts can be associated with accounts (companies).
    """
    
    # Basic Information
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    full_name = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Auto-generated full name"
    )
    title = models.CharField(max_length=100, blank=True, help_text="Job title")
    department = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    fax = models.CharField(max_length=50, blank=True)
    
    # Social Media
    linkedin_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)
    facebook_url = models.URLField(blank=True)
    
    # Relationships
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        help_text="Company/Account this contact belongs to"
    )
    reports_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
        help_text="Manager/supervisor of this contact"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_contacts',
        help_text="Sales rep who owns this contact"
    )
    
    # Mailing Address
    mailing_address_line1 = models.CharField(max_length=255, blank=True)
    mailing_address_line2 = models.CharField(max_length=255, blank=True)
    mailing_city = models.CharField(max_length=100, blank=True)
    mailing_state = models.CharField(max_length=100, blank=True)
    mailing_postal_code = models.CharField(max_length=20, blank=True)
    mailing_country = models.CharField(max_length=100, blank=True)
    
    # Other Address (if different from mailing)
    other_address_line1 = models.CharField(max_length=255, blank=True)
    other_address_line2 = models.CharField(max_length=255, blank=True)
    other_city = models.CharField(max_length=100, blank=True)
    other_state = models.CharField(max_length=100, blank=True)
    other_postal_code = models.CharField(max_length=20, blank=True)
    other_country = models.CharField(max_length=100, blank=True)
    
    # Preferences
    email_opt_out = models.BooleanField(
        default=False,
        help_text="Contact has opted out of email communications"
    )
    do_not_call = models.BooleanField(
        default=False,
        help_text="Contact prefers not to be called"
    )
    preferred_contact_method = models.CharField(
        max_length=50,
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('mobile', 'Mobile'),
            ('meeting', 'In-person Meeting'),
        ],
        blank=True
    )
    
    # Classification
    contact_type = models.CharField(
        max_length=50,
        choices=[
            ('decision_maker', 'Decision Maker'),
            ('influencer', 'Influencer'),
            ('technical', 'Technical Contact'),
            ('administrative', 'Administrative'),
            ('billing', 'Billing Contact'),
            ('other', 'Other'),
        ],
        blank=True,
        help_text="Role of this contact in sales process"
    )
    
    # Birthday and Important Dates
    date_of_birth = models.DateField(null=True, blank=True)
    assistant_name = models.CharField(max_length=100, blank=True)
    assistant_phone = models.CharField(max_length=50, blank=True)
    
    # Notes
    description = models.TextField(blank=True, help_text="Notes about this contact")
    
    # Custom Fields
    custom_fields = models.JSONField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary contact for the account"
    )
    
    class Meta:
        db_table = 'crm_contact'
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['company', 'last_name', 'first_name']),
            models.Index(fields=['company', 'account']),
            models.Index(fields=['company', 'owner']),
            models.Index(fields=['company', 'email']),
            models.Index(fields=['company', 'is_active']),
        ]
    
    def __str__(self):
        return self.full_name or f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate full_name
        self.full_name = f"{self.first_name} {self.last_name}".strip()
        
        # If this is set as primary contact, unset other primary contacts for this account
        if self.is_primary and self.account:
            Contact.objects.filter(
                account=self.account,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    def get_full_address(self, address_type='mailing'):
        """Get formatted address"""
        if address_type == 'mailing':
            parts = [
                self.mailing_address_line1,
                self.mailing_address_line2,
                self.mailing_city,
                self.mailing_state,
                self.mailing_postal_code,
                self.mailing_country
            ]
        else:
            parts = [
                self.other_address_line1,
                self.other_address_line2,
                self.other_city,
                self.other_state,
                self.other_postal_code,
                self.other_country
            ]
        
        return ', '.join([p for p in parts if p])
    
    @property
    def account_name(self):
        """Get account name"""
        return self.account.name if self.account else None
    
    @property
    def activities_count(self):
        """Count of activities"""
        from activities.models import Activity
        return Activity.objects.filter(
            company=self.company,
            contact=self
        ).count()
    
    @property
    def deals_count(self):
        """Count of deals"""
        from deals.models import Deal
        return Deal.objects.filter(
            company=self.company,
            contact=self
        ).count()
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

# ========================================
# LEAD MODEL
# ========================================

class Lead(CompanyIsolatedModel):
    """
    Lead model represents a potential customer.
    Leads can be converted to Account + Contact + Deal.
    """
    
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
    
    SOURCE_CHOICES = [
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('cold_call', 'Cold Call'),
        ('trade_show', 'Trade Show'),
        ('email_campaign', 'Email Campaign'),
        ('social_media', 'Social Media'),
        ('partner', 'Partner'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    first_name = models.CharField(max_length=100, blank=True, db_index=True)
    last_name = models.CharField(max_length=100, blank=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True, db_index=True)
    company_name = models.CharField(max_length=255, blank=True, db_index=True)
    title = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Lead Details
    source = models.CharField(
        max_length=100,
        choices=SOURCE_CHOICES,
        blank=True,
        db_index=True
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )
    rating = models.CharField(
        max_length=20,
        choices=RATING_CHOICES,
        blank=True,
        db_index=True,
        help_text="How hot is this lead?"
    )
    
    # Lead Scoring
    lead_score = models.IntegerField(
        default=0,
        help_text="Automated lead score (0-100)"
    )
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Business Information
    industry = models.CharField(max_length=100, blank=True, db_index=True)
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    employee_count = models.IntegerField(null=True, blank=True)
    
    # Relationships
    territory = models.ForeignKey(
        Territory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_leads',
        help_text="Sales rep who owns this lead"
    )
    
    # Conversion Tracking
    converted_at = models.DateTimeField(null=True, blank=True)
    converted_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_from_leads'
    )
    converted_contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_from_leads'
    )
    
    # Campaign Tracking
    campaign_name = models.CharField(max_length=255, blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    
    # Qualification
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated budget"
    )
    timeline = models.CharField(
        max_length=100,
        blank=True,
        help_text="Purchase timeline"
    )
    
    # Description/Notes
    description = models.TextField(blank=True)
    
    # Custom Fields
    custom_fields = models.JSONField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = 'crm_lead'
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'rating']),
            models.Index(fields=['company', 'source']),
            models.Index(fields=['company', 'owner']),
            models.Index(fields=['company', 'territory']),
            models.Index(fields=['company', 'email']),
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['company', '-created_at']),
        ]
    
    def __str__(self):
        if self.full_name:
            return self.full_name
        elif self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.company_name or f"Lead #{self.id}"
    
    def save(self, *args, **kwargs):
        # Auto-generate full_name
        if self.first_name or self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip()
        
        super().save(*args, **kwargs)
    
    def get_full_address(self):
        """Get formatted address"""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([p for p in parts if p])
    
    @property
    def is_hot(self):
        """Check if lead is hot"""
        return self.rating == 'hot' or self.lead_score >= 80
    
    @property
    def is_qualified(self):
        """Check if lead is qualified"""
        return self.status == 'qualified'
    
    @property
    def days_since_creation(self):
        """Calculate days since lead was created"""
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        return delta.days
    
    @property
    def activities_count(self):
        """Count of activities"""
        from activities.models import Activity
        return Activity.objects.filter(
            company=self.company,
            related_to_type='lead',
            related_to_id=self.id
        ).count()
    
    def calculate_lead_score(self):
        """
        Auto-calculate lead score based on various factors
        Score range: 0-100
        """
        score = 0
        
        # Email provided (+10)
        if self.email:
            score += 10
        
        # Phone provided (+5)
        if self.phone or self.mobile:
            score += 5
        
        # Company name provided (+10)
        if self.company:
            score += 10
        
        # Industry known (+5)
        if self.industry:
            score += 5
        
        # Revenue data (+10)
        if self.annual_revenue:
            score += 10
        
        # Budget provided (+15)
        if self.budget:
            score += 15
        
        # Rating boost
        if self.rating == 'hot':
            score += 20
        elif self.rating == 'warm':
            score += 10
        
        # Activity engagement (+15 if any activities)
        if self.activities_count > 0:
            score += 15
        
        # Recent activity boost
        if self.days_since_creation <= 7:
            score += 10
        
        return min(score, 100)  # Cap at 100
