# crm/models/leads.py
# Lead model - Sales prospects before conversion

from django.db import models
from django.core.validators import EmailValidator
from core.models import CompanyIsolatedModel, User
from territories.models import Territory

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
    lead_source = models.CharField(
        max_length=100,
        choices=SOURCE_CHOICES,
        blank=True,
        db_index=True
    )
    lead_status = models.CharField(
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
        'Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_from_leads'
    )
    converted_contact = models.ForeignKey(
        'Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_from_leads'
    )
    converted_deal = models.ForeignKey(
        'Deal',
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
        db_table = 'leads'
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'lead_status']),
            models.Index(fields=['company', 'rating']),
            models.Index(fields=['company', 'lead_source']),
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
        return self.lead_status == 'qualified'
    
    @property
    def days_since_creation(self):
        """Calculate days since lead was created"""
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        return delta.days
    
    @property
    def activities_count(self):
        """Count of activities"""
        from crm.models.activities import Activity
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
        if self.company_name:
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
    
    def auto_assign_territory(self):
        """Auto-assign territory based on location"""
        if not self.territory and self.country:
            # Try to find matching territory
            territories = Territory.objects.filter(
                company=self.company,
                is_active=True,
                type='geographic'
            )
            
            for territory in territories:
                if territory.countries and self.country in territory.countries:
                    self.territory = territory
                    self.save()
                    break
    
    def convert(self, create_deal=True, deal_amount=None):
        """
        Convert lead to Account + Contact + Deal
        Returns tuple: (account, contact, deal)
        """
        from crm.models import Account, Contact, Deal
        from django.utils import timezone
        
        # Create Account
        account, created = Account.objects.get_or_create(
            company=self.company,
            name=self.company_name or f"{self.first_name} {self.last_name}",
            defaults={
                'email': self.email,
                'phone': self.phone,
                'website': self.website,
                'industry': self.industry,
                'annual_revenue': self.annual_revenue,
                'employee_count': self.employee_count,
                'billing_address_line1': self.address_line1,
                'billing_address_line2': self.address_line2,
                'billing_city': self.city,
                'billing_state': self.state,
                'billing_postal_code': self.postal_code,
                'billing_country': self.country,
                'territory': self.territory,
                'owner': self.owner,
                'account_type': 'prospect',
                'created_by': self.owner,
            }
        )
        
        # Create Contact
        contact = Contact.objects.create(
            company=self.company,
            first_name=self.first_name,
            last_name=self.last_name,
            title=self.title,
            email=self.email,
            phone=self.phone,
            mobile=self.mobile,
            account=account,
            owner=self.owner,
            mailing_address_line1=self.address_line1,
            mailing_address_line2=self.address_line2,
            mailing_city=self.city,
            mailing_state=self.state,
            mailing_postal_code=self.postal_code,
            mailing_country=self.country,
            is_primary=True,
            created_by=self.owner,
        )
        
        # Create Deal if requested
        deal = None
        if create_deal:
            deal = Deal.objects.create(
                company=self.company,
                name=f"Deal with {account.name}",
                account=account,
                contact=contact,
                amount=deal_amount or self.budget or 0,
                territory=self.territory,
                owner=self.owner,
                lead_source=self.lead_source,
                description=self.description,
                created_by=self.owner,
            )
        
        # Mark lead as converted
        self.lead_status = 'converted'
        self.converted_at = timezone.now()
        self.converted_account = account
        self.converted_contact = contact
        self.converted_deal = deal
        self.save()
        
        return account, contact, deal