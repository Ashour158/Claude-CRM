# marketing/serializers.py
# Marketing serializers

from rest_framework import serializers
from .models import (
    Campaign, EmailTemplate, MarketingList, MarketingListContact,
    EmailCampaign, EmailActivity, LeadScore, MarketingAutomation,
    MarketingAutomationExecution
)
from core.serializers import UserSerializer
from crm.serializers import ContactSerializer, LeadSerializer

class CampaignSerializer(serializers.ModelSerializer):
    """Campaign serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class EmailTemplateSerializer(serializers.ModelSerializer):
    """Email template serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = EmailTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class MarketingListSerializer(serializers.ModelSerializer):
    """Marketing list serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = MarketingList
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class MarketingListContactSerializer(serializers.ModelSerializer):
    """Marketing list contact serializer"""
    contact = ContactSerializer(read_only=True)
    
    class Meta:
        model = MarketingListContact
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class EmailCampaignSerializer(serializers.ModelSerializer):
    """Email campaign serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = EmailCampaign
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class EmailActivitySerializer(serializers.ModelSerializer):
    """Email activity serializer"""
    contact = ContactSerializer(read_only=True)
    
    class Meta:
        model = EmailActivity
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class LeadScoreSerializer(serializers.ModelSerializer):
    """Lead score serializer"""
    
    class Meta:
        model = LeadScore
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class MarketingAutomationSerializer(serializers.ModelSerializer):
    """Marketing automation serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = MarketingAutomation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class MarketingAutomationExecutionSerializer(serializers.ModelSerializer):
    """Marketing automation execution serializer"""
    contact = ContactSerializer(read_only=True)
    lead = LeadSerializer(read_only=True)
    
    class Meta:
        model = MarketingAutomationExecution
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']