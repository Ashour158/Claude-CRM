# marketing/models.py
from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class Campaign(CompanyIsolatedModel):
    """
    Marketing campaigns
    """
    CAMPAIGN_TYPES = [
        ('email', 'Email Campaign'),
        ('social', 'Social Media'),
        ('content', 'Content Marketing'),
        ('paid', 'Paid Advertising'),
        ('event', 'Event Marketing'),
        ('webinar', 'Webinar'),
        ('other', 'Other'),
    ]
    
    CAMPAIGN_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Campaign name")
    description = models.TextField(blank=True, help_text="Campaign description")
    campaign_type = models.CharField(
        max_length=20,
        choices=CAMPAIGN_TYPES,
        help_text="Type of campaign"
    )
    status = models.CharField(
        max_length=20,
        choices=CAMPAIGN_STATUS_CHOICES,
        default='draft'
    )
    
    # Campaign Details
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Campaign start date"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Campaign end date"
    )
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Campaign budget"
    )
    currency = models.CharField(max_length=3, default='USD', help_text="Currency")
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_campaigns',
        help_text="Campaign owner"
    )
    
    # Metrics
    target_audience_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Target audience size"
    )
    actual_reach = models.PositiveIntegerField(
        default=0,
        help_text="Actual reach"
    )
    clicks = models.PositiveIntegerField(
        default=0,
        help_text="Number of clicks"
    )
    conversions = models.PositiveIntegerField(
        default=0,
        help_text="Number of conversions"
    )
    cost_per_click = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost per click"
    )
    cost_per_conversion = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost per conversion"
    )
    
    # Additional Information
    notes = models.TextField(blank=True, help_text="Campaign notes")
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='campaigns')
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'campaign_type']),
            models.Index(fields=['company', 'owner']),
            models.Index(fields=['company', 'start_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_campaign_type_display()})"
    
    @property
    def click_through_rate(self):
        """Calculate click-through rate"""
        if self.actual_reach > 0:
            return (self.clicks / self.actual_reach) * 100
        return 0
    
    @property
    def conversion_rate(self):
        """Calculate conversion rate"""
        if self.clicks > 0:
            return (self.conversions / self.clicks) * 100
        return 0
    
    @property
    def roi(self):
        """Calculate return on investment"""
        if self.budget and self.budget > 0:
            # Assuming each conversion has a value of $100
            revenue = self.conversions * 100
            return ((revenue - float(self.budget)) / float(self.budget)) * 100
        return 0

class EmailTemplate(CompanyIsolatedModel):
    """
    Email templates for marketing campaigns
    """
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('newsletter', 'Newsletter'),
        ('promotional', 'Promotional'),
        ('follow_up', 'Follow Up'),
        ('abandoned_cart', 'Abandoned Cart'),
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Template name")
    subject = models.CharField(max_length=255, help_text="Email subject")
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPES,
        default='custom'
    )
    
    # Content
    html_content = models.TextField(help_text="HTML content")
    text_content = models.TextField(
        blank=True,
        help_text="Plain text content"
    )
    
    # Design
    header_image_url = models.URLField(
        blank=True,
        help_text="Header image URL"
    )
    footer_text = models.TextField(
        blank=True,
        help_text="Footer text"
    )
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_email_templates',
        help_text="Template owner"
    )
    
    # Usage Statistics
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times used"
    )
    
    # Additional Information
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

class EmailCampaign(CompanyIsolatedModel):
    """
    Email marketing campaigns
    """
    CAMPAIGN_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Campaign name")
    subject = models.CharField(max_length=255, help_text="Email subject")
    status = models.CharField(
        max_length=20,
        choices=CAMPAIGN_STATUS_CHOICES,
        default='draft'
    )
    
    # Template
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_campaigns',
        help_text="Email template"
    )
    
    # Content
    html_content = models.TextField(help_text="HTML content")
    text_content = models.TextField(
        blank=True,
        help_text="Plain text content"
    )
    
    # Scheduling
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled send time"
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual send time"
    )
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_email_campaigns',
        help_text="Campaign owner"
    )
    
    # Metrics
    total_recipients = models.PositiveIntegerField(
        default=0,
        help_text="Total recipients"
    )
    sent_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of emails sent"
    )
    delivered_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of emails delivered"
    )
    opened_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of emails opened"
    )
    clicked_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of clicks"
    )
    unsubscribed_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of unsubscribes"
    )
    bounced_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of bounces"
    )
    
    # Additional Information
    notes = models.TextField(blank=True, help_text="Campaign notes")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'owner']),
            models.Index(fields=['company', 'scheduled_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    @property
    def open_rate(self):
        """Calculate open rate"""
        if self.delivered_count > 0:
            return (self.opened_count / self.delivered_count) * 100
        return 0
    
    @property
    def click_rate(self):
        """Calculate click rate"""
        if self.delivered_count > 0:
            return (self.clicked_count / self.delivered_count) * 100
        return 0
    
    @property
    def bounce_rate(self):
        """Calculate bounce rate"""
        if self.sent_count > 0:
            return (self.bounced_count / self.sent_count) * 100
        return 0

class LeadScore(CompanyIsolatedModel):
    """
    Lead scoring rules and criteria
    """
    SCORE_TYPES = [
        ('behavioral', 'Behavioral'),
        ('demographic', 'Demographic'),
        ('firmographic', 'Firmographic'),
        ('engagement', 'Engagement'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Score rule name")
    description = models.TextField(blank=True, help_text="Score rule description")
    score_type = models.CharField(
        max_length=20,
        choices=SCORE_TYPES,
        help_text="Type of scoring"
    )
    
    # Scoring Criteria
    criteria = models.JSONField(
        default=dict,
        help_text="Scoring criteria configuration"
    )
    points = models.IntegerField(
        help_text="Points to add/subtract"
    )
    
    # Conditions
    conditions = models.JSONField(
        default=dict,
        help_text="Conditions for applying this score"
    )
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_lead_scores',
        help_text="Score rule owner"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.points} points)"

class MarketingList(CompanyIsolatedModel):
    """
    Marketing lists for campaigns
    """
    LIST_TYPES = [
        ('static', 'Static List'),
        ('dynamic', 'Dynamic List'),
        ('segmented', 'Segmented List'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="List name")
    description = models.TextField(blank=True, help_text="List description")
    list_type = models.CharField(
        max_length=20,
        choices=LIST_TYPES,
        default='static'
    )
    
    # Criteria for dynamic lists
    criteria = models.JSONField(
        default=dict,
        help_text="Criteria for dynamic lists"
    )
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_marketing_lists',
        help_text="List owner"
    )
    
    # Statistics
    member_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of members"
    )
    
    # Additional Information
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='marketing_lists')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.member_count} members)"

class MarketingListMember(CompanyIsolatedModel):
    """
    Members of marketing lists
    """
    list = models.ForeignKey(
        MarketingList,
        on_delete=models.CASCADE,
        related_name='members'
    )
    contact = models.ForeignKey(
        'crm.Contact',
        on_delete=models.CASCADE,
        related_name='marketing_list_memberships'
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When contact was added to list"
    )
    unsubscribed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When contact unsubscribed"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('list', 'contact')
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return f"{self.contact.full_name} - {self.list.name}"

class MarketingEvent(CompanyIsolatedModel):
    """
    Marketing events and activities
    """
    EVENT_TYPES = [
        ('email_sent', 'Email Sent'),
        ('email_opened', 'Email Opened'),
        ('email_clicked', 'Email Clicked'),
        ('email_bounced', 'Email Bounced'),
        ('unsubscribed', 'Unsubscribed'),
        ('form_submitted', 'Form Submitted'),
        ('page_visited', 'Page Visited'),
        ('download', 'Download'),
        ('webinar_attended', 'Webinar Attended'),
        ('event_attended', 'Event Attended'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        help_text="Type of marketing event"
    )
    event_name = models.CharField(
        max_length=255,
        help_text="Event name"
    )
    description = models.TextField(blank=True, help_text="Event description")
    
    # Related Objects
    contact = models.ForeignKey(
        'crm.Contact',
        on_delete=models.CASCADE,
        related_name='marketing_events'
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    email_campaign = models.ForeignKey(
        EmailCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    
    # Event Details
    event_date = models.DateTimeField(help_text="Event date and time")
    event_data = models.JSONField(
        default=dict,
        help_text="Additional event data"
    )
    
    # Assignment
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_marketing_events'
    )
    
    class Meta:
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['company', 'event_type']),
            models.Index(fields=['company', 'contact']),
            models.Index(fields=['company', 'event_date']),
        ]
    
    def __str__(self):
        return f"{self.event_name} - {self.contact.full_name}"

class MarketingAnalytics(CompanyIsolatedModel):
    """
    Marketing analytics and metrics
    """
    # Basic Information
    name = models.CharField(max_length=255, help_text="Analytics name")
    description = models.TextField(blank=True, help_text="Analytics description")
    
    # Metrics
    total_campaigns = models.PositiveIntegerField(default=0)
    active_campaigns = models.PositiveIntegerField(default=0)
    total_emails_sent = models.PositiveIntegerField(default=0)
    total_emails_delivered = models.PositiveIntegerField(default=0)
    total_emails_opened = models.PositiveIntegerField(default=0)
    total_clicks = models.PositiveIntegerField(default=0)
    total_conversions = models.PositiveIntegerField(default=0)
    total_unsubscribes = models.PositiveIntegerField(default=0)
    total_bounces = models.PositiveIntegerField(default=0)
    
    # Calculated Metrics
    overall_open_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Overall open rate percentage"
    )
    overall_click_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Overall click rate percentage"
    )
    overall_bounce_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Overall bounce rate percentage"
    )
    overall_conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Overall conversion rate percentage"
    )
    
    # Date Range
    start_date = models.DateField(help_text="Analytics start date")
    end_date = models.DateField(help_text="Analytics end date")
    
    # Additional Information
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('company', 'name', 'start_date', 'end_date')
    
    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
    
    def calculate_metrics(self):
        """Calculate all metrics"""
        if self.total_emails_delivered > 0:
            self.overall_open_rate = (self.total_emails_opened / self.total_emails_delivered) * 100
            self.overall_click_rate = (self.total_clicks / self.total_emails_delivered) * 100
        
        if self.total_emails_sent > 0:
            self.overall_bounce_rate = (self.total_bounces / self.total_emails_sent) * 100
        
        if self.total_emails_delivered > 0:
            self.overall_conversion_rate = (self.total_conversions / self.total_emails_delivered) * 100
