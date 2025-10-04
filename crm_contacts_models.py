# crm/models/contacts.py
# Contact model - Individual people

from django.db import models
from django.core.validators import EmailValidator
from core.models import CompanyIsolatedModel, User
from crm.models import Account

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
        db_table = 'contacts'
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
        from crm.models.activities import Activity
        return Activity.objects.filter(
            company=self.company,
            contact=self
        ).count()
    
    @property
    def deals_count(self):
        """Count of deals"""
        from crm.models.deals import Deal
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