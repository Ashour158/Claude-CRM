# marketing/models.py
# Marketing and campaign management models

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
from crm.models import Lead, Contact, Account
import uuid

User = get_user_model()

class Campaign(CompanyIsolatedModel):
    """Marketing campaigns"""
    
    CAMPAIGN_TYPES = [
        ('email', 'Email Campaign'),
        ('social_media', 'Social Media'),
        ('content', 'Content Marketing'),
        ('paid_ads', 'Paid Advertising'),
        ('events', 'Events'),
        ('webinar', 'Webinar'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    campaign_type = models.CharField(
        max_length=20,
        choices=CAMPAIGN_TYPES,
        default='email'
    )
    
    # Campaign Details
    objective = models.TextField(blank=True, help_text="Campaign objective")
    target_audience = models.TextField(blank=True, help_text="Target audience description")
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Dates
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_campaigns'
    )
    
    # Performance Metrics
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_converted = models.IntegerField(default=0)
    
    # Rates
    delivery_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Delivery rate percentage"
    )
    open_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Open rate percentage"
    )
    click_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Click rate percentage"
    )
    conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Conversion rate percentage"
    )
    
    class Meta:
        db_table = 'campaign'
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['company', 'name']),
            models.Index(fields=['company', 'campaign_type']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'owner']),
        ]
    
    def __str__(self):
        return self.name
    
    def calculate_rates(self):
        """Calculate campaign performance rates"""
        if self.total_sent > 0:
            self.delivery_rate = (self.total_delivered / self.total_sent) * 100
        if self.total_delivered > 0:
            self.open_rate = (self.total_opened / self.total_delivered) * 100
        if self.total_opened > 0:
            self.click_rate = (self.total_clicked / self.total_opened) * 100
        if self.total_clicked > 0:
            self.conversion_rate = (self.total_converted / self.total_clicked) * 100

class EmailTemplate(CompanyIsolatedModel):
    """Email templates for campaigns"""
    
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('newsletter', 'Newsletter'),
        ('promotional', 'Promotional'),
        ('follow_up', 'Follow Up'),
        ('nurture', 'Nurture Sequence'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPES,
        default='custom'
    )
    
    # Content
    html_content = models.TextField(blank=True)
    text_content = models.TextField(blank=True)
    preview_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Email preview text"
    )
    
    # Template Settings
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_email_templates'
    )
    
    class Meta:
        db_table = 'email_template'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class MarketingList(CompanyIsolatedModel):
    """Marketing lists for campaigns"""
    
    LIST_TYPES = [
        ('static', 'Static List'),
        ('dynamic', 'Dynamic List'),
        ('segment', 'Segment'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    list_type = models.CharField(
        max_length=20,
        choices=LIST_TYPES,
        default='static'
    )
    
    # List Configuration
    criteria = models.JSONField(
        default=dict,
        help_text="List criteria for dynamic lists"
    )
    filters = models.JSONField(
        default=dict,
        help_text="List filters"
    )
    
    # Statistics
    total_contacts = models.IntegerField(default=0)
    active_contacts = models.IntegerField(default=0)
    unsubscribed_contacts = models.IntegerField(default=0)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_marketing_lists'
    )
    
    class Meta:
        db_table = 'marketing_list'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class MarketingListContact(CompanyIsolatedModel):
    """Contacts in marketing lists"""
    
    marketing_list = models.ForeignKey(
        MarketingList,
        on_delete=models.CASCADE,
        related_name='list_contacts'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='marketing_lists'
    )
    added_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_unsubscribed = models.BooleanField(default=False)
    unsubscribed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'marketing_list_contact'
        unique_together = ('marketing_list', 'contact')
    
    def __str__(self):
        return f"{self.marketing_list.name} - {self.contact.full_name}"

class EmailCampaign(CompanyIsolatedModel):
    """Email campaigns"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Campaign Details
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='email_campaigns'
    )
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_campaigns'
    )
    marketing_list = models.ForeignKey(
        MarketingList,
        on_delete=models.CASCADE,
        related_name='email_campaigns'
    )
    
    # Content
    html_content = models.TextField(blank=True)
    text_content = models.TextField(blank=True)
    preview_text = models.CharField(max_length=255, blank=True)
    
    # Scheduling
    send_date = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Performance Metrics
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_bounced = models.IntegerField(default=0)
    total_unsubscribed = models.IntegerField(default=0)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_email_campaigns'
    )
    
    class Meta:
        db_table = 'email_campaign'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class EmailActivity(CompanyIsolatedModel):
    """Email activity tracking"""
    
    ACTIVITY_TYPES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('unsubscribed', 'Unsubscribed'),
        ('complained', 'Complained'),
    ]
    
    email_campaign = models.ForeignKey(
        EmailCampaign,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='email_activities'
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES
    )
    activity_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    link_url = models.URLField(blank=True, help_text="Clicked link URL")
    
    class Meta:
        db_table = 'email_activity'
        ordering = ['-activity_date']
    
    def __str__(self):
        return f"{self.email_campaign.name} - {self.contact.full_name} - {self.get_activity_type_display()}"

class LeadScore(CompanyIsolatedModel):
    """Lead scoring configuration and history"""
    
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='scores'
    )
    score = models.IntegerField(
        default=0,
        help_text="Lead score (0-100)"
    )
    score_date = models.DateTimeField(auto_now_add=True)
    score_reason = models.TextField(blank=True, help_text="Reason for score change")
    
    # Score Factors
    email_score = models.IntegerField(default=0)
    phone_score = models.IntegerField(default=0)
    company_score = models.IntegerField(default=0)
    industry_score = models.IntegerField(default=0)
    revenue_score = models.IntegerField(default=0)
    budget_score = models.IntegerField(default=0)
    activity_score = models.IntegerField(default=0)
    engagement_score = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'lead_score'
        ordering = ['-score_date']
    
    def __str__(self):
        return f"{self.lead.full_name} - Score: {self.score}"

class MarketingAutomation(CompanyIsolatedModel):
    """Marketing automation workflows"""
    
    WORKFLOW_TYPES = [
        ('welcome', 'Welcome Series'),
        ('nurture', 'Nurture Sequence'),
        ('abandoned_cart', 'Abandoned Cart'),
        ('re_engagement', 'Re-engagement'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    workflow_type = models.CharField(
        max_length=20,
        choices=WORKFLOW_TYPES,
        default='custom'
    )
    
    # Workflow Configuration
    trigger_conditions = models.JSONField(
        default=dict,
        help_text="Workflow trigger conditions"
    )
    steps = models.JSONField(
        default=list,
        help_text="Workflow steps"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_triggered = models.IntegerField(default=0)
    total_completed = models.IntegerField(default=0)
    total_dropped = models.IntegerField(default=0)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_automations'
    )
    
    class Meta:
        db_table = 'marketing_automation'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class MarketingAutomationExecution(CompanyIsolatedModel):
    """Marketing automation execution tracking"""
    
    automation = models.ForeignKey(
        MarketingAutomation,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='automation_executions'
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='automation_executions'
    )
    
    # Execution Details
    triggered_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    current_step = models.IntegerField(default=0)
    total_steps = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('paused', 'Paused'),
            ('stopped', 'Stopped'),
        ],
        default='running'
    )
    
    class Meta:
        db_table = 'marketing_automation_execution'
        ordering = ['-triggered_date']
    
    def __str__(self):
        return f"{self.automation.name} - {self.contact.full_name}"