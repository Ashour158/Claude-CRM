# marketing/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Campaign, EmailTemplate, EmailCampaign, LeadScore, 
    MarketingList, MarketingListMember, MarketingEvent, MarketingAnalytics
)
from crm.serializers import ContactSerializer

User = get_user_model()

class CampaignSerializer(serializers.ModelSerializer):
    """Serializer for Campaign model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    click_through_rate = serializers.ReadOnlyField()
    conversion_rate = serializers.ReadOnlyField()
    roi = serializers.ReadOnlyField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'campaign_type', 'status',
            'start_date', 'end_date', 'budget', 'currency',
            'owner', 'owner_name', 'target_audience_size', 'actual_reach',
            'clicks', 'conversions', 'cost_per_click', 'cost_per_conversion',
            'click_through_rate', 'conversion_rate', 'roi',
            'notes', 'tags', 'metadata', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for EmailTemplate model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'subject', 'template_type',
            'html_content', 'text_content', 'header_image_url', 'footer_text',
            'owner', 'owner_name', 'usage_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']

class EmailCampaignSerializer(serializers.ModelSerializer):
    """Serializer for EmailCampaign model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    open_rate = serializers.ReadOnlyField()
    click_rate = serializers.ReadOnlyField()
    bounce_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = EmailCampaign
        fields = [
            'id', 'name', 'subject', 'status', 'template', 'template_name',
            'html_content', 'text_content', 'scheduled_at', 'sent_at',
            'owner', 'owner_name', 'total_recipients', 'sent_count',
            'delivered_count', 'opened_count', 'clicked_count',
            'unsubscribed_count', 'bounced_count', 'open_rate', 'click_rate',
            'bounce_rate', 'notes', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sent_at', 'created_at', 'updated_at']

class LeadScoreSerializer(serializers.ModelSerializer):
    """Serializer for LeadScore model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = LeadScore
        fields = [
            'id', 'name', 'description', 'score_type', 'criteria',
            'points', 'conditions', 'owner', 'owner_name', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class MarketingListSerializer(serializers.ModelSerializer):
    """Serializer for MarketingList model"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = MarketingList
        fields = [
            'id', 'name', 'description', 'list_type', 'criteria',
            'owner', 'owner_name', 'member_count', 'tags', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'member_count', 'created_at', 'updated_at']

class MarketingListMemberSerializer(serializers.ModelSerializer):
    """Serializer for MarketingListMember model"""
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    contact_email = serializers.CharField(source='contact.email', read_only=True)
    
    class Meta:
        model = MarketingListMember
        fields = [
            'id', 'list', 'contact', 'contact_name', 'contact_email',
            'subscribed_at', 'unsubscribed_at', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'subscribed_at', 'created_at', 'updated_at']

class MarketingEventSerializer(serializers.ModelSerializer):
    """Serializer for MarketingEvent model"""
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    email_campaign_name = serializers.CharField(source='email_campaign.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = MarketingEvent
        fields = [
            'id', 'event_type', 'event_name', 'description', 'contact',
            'contact_name', 'campaign', 'campaign_name', 'email_campaign',
            'email_campaign_name', 'event_date', 'event_data',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class MarketingAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for MarketingAnalytics model"""
    
    class Meta:
        model = MarketingAnalytics
        fields = [
            'id', 'name', 'description', 'total_campaigns', 'active_campaigns',
            'total_emails_sent', 'total_emails_delivered', 'total_emails_opened',
            'total_clicks', 'total_conversions', 'total_unsubscribes',
            'total_bounces', 'overall_open_rate', 'overall_click_rate',
            'overall_bounce_rate', 'overall_conversion_rate', 'start_date',
            'end_date', 'metadata', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

# Bulk operation serializers
class BulkEmailCampaignSerializer(serializers.Serializer):
    """Serializer for bulk email campaign operations"""
    campaign_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of campaign IDs"
    )
    action = serializers.ChoiceField(
        choices=['start', 'pause', 'stop', 'delete'],
        help_text="Action to perform"
    )

class BulkMarketingListSerializer(serializers.Serializer):
    """Serializer for bulk marketing list operations"""
    list_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of marketing list IDs"
    )
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'delete'],
        help_text="Action to perform"
    )

# Analytics serializers
class MarketingMetricsSerializer(serializers.Serializer):
    """Serializer for marketing metrics"""
    total_campaigns = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    total_emails_sent = serializers.IntegerField()
    total_emails_delivered = serializers.IntegerField()
    total_emails_opened = serializers.IntegerField()
    total_clicks = serializers.IntegerField()
    total_conversions = serializers.IntegerField()
    overall_open_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    overall_click_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    overall_bounce_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    overall_conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

class CampaignPerformanceSerializer(serializers.Serializer):
    """Serializer for campaign performance metrics"""
    campaign_id = serializers.UUIDField()
    campaign_name = serializers.CharField()
    campaign_type = serializers.CharField()
    status = serializers.CharField()
    total_recipients = serializers.IntegerField()
    sent_count = serializers.IntegerField()
    delivered_count = serializers.IntegerField()
    opened_count = serializers.IntegerField()
    clicked_count = serializers.IntegerField()
    conversions = serializers.IntegerField()
    open_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    click_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    roi = serializers.DecimalField(max_digits=10, decimal_places=2)

class EmailTemplateUsageSerializer(serializers.Serializer):
    """Serializer for email template usage statistics"""
    template_id = serializers.UUIDField()
    template_name = serializers.CharField()
    template_type = serializers.CharField()
    usage_count = serializers.IntegerField()
    last_used = serializers.DateTimeField()
    success_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
