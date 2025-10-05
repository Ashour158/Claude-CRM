# marketing/views.py
# Marketing views

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Campaign, EmailTemplate, MarketingList, MarketingListContact,
    EmailCampaign, EmailActivity, LeadScore, MarketingAutomation,
    MarketingAutomationExecution
)
from .serializers import (
    CampaignSerializer, EmailTemplateSerializer, MarketingListSerializer,
    MarketingListContactSerializer, EmailCampaignSerializer, EmailActivitySerializer,
    LeadScoreSerializer, MarketingAutomationSerializer, MarketingAutomationExecutionSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response

class CampaignViewSet(viewsets.ModelViewSet):
    """Campaign viewset"""
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['campaign_type', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_date', 'start_date']
    ordering = ['-created_date']
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start campaign"""
        campaign = self.get_object()
        campaign.status = 'active'
        campaign.save()
        return Response({'message': 'Campaign started successfully'})
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause campaign"""
        campaign = self.get_object()
        campaign.status = 'paused'
        campaign.save()
        return Response({'message': 'Campaign paused successfully'})

class EmailTemplateViewSet(viewsets.ModelViewSet):
    """Email template viewset"""
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template_type', 'is_active', 'is_public']
    search_fields = ['name', 'subject']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class MarketingListViewSet(viewsets.ModelViewSet):
    """Marketing list viewset"""
    queryset = MarketingList.objects.all()
    serializer_class = MarketingListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['list_type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """Get list contacts"""
        marketing_list = self.get_object()
        contacts = marketing_list.list_contacts.all()
        serializer = MarketingListContactSerializer(contacts, many=True)
        return Response(serializer.data)

class MarketingListContactViewSet(viewsets.ModelViewSet):
    """Marketing list contact viewset"""
    queryset = MarketingListContact.objects.all()
    serializer_class = MarketingListContactSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['marketing_list', 'is_active', 'is_unsubscribed']
    ordering_fields = ['added_date']
    ordering = ['-added_date']

class EmailCampaignViewSet(viewsets.ModelViewSet):
    """Email campaign viewset"""
    queryset = EmailCampaign.objects.all()
    serializer_class = EmailCampaignSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'campaign', 'marketing_list']
    search_fields = ['name', 'subject']
    ordering_fields = ['created_at', 'send_date']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send email campaign"""
        campaign = self.get_object()
        campaign.status = 'sending'
        campaign.save()
        return Response({'message': 'Email campaign sending started'})

class EmailActivityViewSet(viewsets.ModelViewSet):
    """Email activity viewset"""
    queryset = EmailActivity.objects.all()
    serializer_class = EmailActivitySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['email_campaign', 'contact', 'activity_type']
    ordering_fields = ['activity_date']
    ordering = ['-activity_date']

class LeadScoreViewSet(viewsets.ModelViewSet):
    """Lead score viewset"""
    queryset = LeadScore.objects.all()
    serializer_class = LeadScoreSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['lead']
    ordering_fields = ['score_date', 'score']
    ordering = ['-score_date']

class MarketingAutomationViewSet(viewsets.ModelViewSet):
    """Marketing automation viewset"""
    queryset = MarketingAutomation.objects.all()
    serializer_class = MarketingAutomationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['workflow_type', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate automation"""
        automation = self.get_object()
        automation.status = 'active'
        automation.save()
        return Response({'message': 'Automation activated successfully'})

class MarketingAutomationExecutionViewSet(viewsets.ModelViewSet):
    """Marketing automation execution viewset"""
    queryset = MarketingAutomationExecution.objects.all()
    serializer_class = MarketingAutomationExecutionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['automation', 'contact', 'lead', 'status']
    ordering_fields = ['triggered_date']
    ordering = ['-triggered_date']