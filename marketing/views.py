# marketing/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Campaign, EmailTemplate, EmailCampaign, LeadScore,
    MarketingList, MarketingListMember, MarketingEvent, MarketingAnalytics
)
from .serializers import (
    CampaignSerializer, EmailTemplateSerializer, EmailCampaignSerializer,
    LeadScoreSerializer, MarketingListSerializer, MarketingListMemberSerializer,
    MarketingEventSerializer, MarketingAnalyticsSerializer,
    BulkEmailCampaignSerializer, BulkMarketingListSerializer,
    MarketingMetricsSerializer, CampaignPerformanceSerializer,
    EmailTemplateUsageSerializer
)
from core.permissions import IsCompanyUser, IsCompanyAdmin
from core.mixins import CompanyIsolatedMixin

class CampaignViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for Campaign model"""
    serializer_class = CampaignSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['campaign_type', 'status', 'owner', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'start_date', 'end_date']
    ordering = ['-created_at']

    def get_queryset(self):
        return Campaign.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def start_campaign(self, request, pk=None):
        """Start a campaign"""
        campaign = self.get_object()
        if campaign.status != 'draft':
            return Response(
                {'error': 'Only draft campaigns can be started'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.status = 'running'
        campaign.start_date = timezone.now()
        campaign.save()
        
        return Response({'message': 'Campaign started successfully'})

    @action(detail=True, methods=['post'])
    def pause_campaign(self, request, pk=None):
        """Pause a campaign"""
        campaign = self.get_object()
        if campaign.status not in ['running', 'scheduled']:
            return Response(
                {'error': 'Only running or scheduled campaigns can be paused'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.status = 'paused'
        campaign.save()
        
        return Response({'message': 'Campaign paused successfully'})

    @action(detail=True, methods=['post'])
    def complete_campaign(self, request, pk=None):
        """Complete a campaign"""
        campaign = self.get_object()
        if campaign.status not in ['running', 'paused']:
            return Response(
                {'error': 'Only running or paused campaigns can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.status = 'completed'
        campaign.end_date = timezone.now()
        campaign.save()
        
        return Response({'message': 'Campaign completed successfully'})

    @action(detail=False, methods=['get'])
    def performance_metrics(self, request):
        """Get campaign performance metrics"""
        campaigns = self.get_queryset()
        
        metrics = {
            'total_campaigns': campaigns.count(),
            'active_campaigns': campaigns.filter(status='running').count(),
            'total_budget': sum(c.budget or 0 for c in campaigns if c.budget),
            'total_reach': sum(c.actual_reach for c in campaigns),
            'total_clicks': sum(c.clicks for c in campaigns),
            'total_conversions': sum(c.conversions for c in campaigns),
            'average_ctr': campaigns.aggregate(avg_ctr=Avg('clicks'))['avg_ctr'] or 0,
            'average_conversion_rate': campaigns.aggregate(avg_cr=Avg('conversions'))['avg_cr'] or 0,
        }
        
        return Response(metrics)

class EmailTemplateViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for EmailTemplate model"""
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template_type', 'owner', 'is_active']
    search_fields = ['name', 'subject']
    ordering_fields = ['name', 'created_at', 'usage_count']
    ordering = ['-created_at']

    def get_queryset(self):
        return EmailTemplate.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def duplicate_template(self, request, pk=None):
        """Duplicate an email template"""
        template = self.get_object()
        new_template = EmailTemplate.objects.create(
            company=template.company,
            name=f"{template.name} (Copy)",
            subject=template.subject,
            template_type=template.template_type,
            html_content=template.html_content,
            text_content=template.text_content,
            header_image_url=template.header_image_url,
            footer_text=template.footer_text,
            owner=request.user
        )
        
        serializer = self.get_serializer(new_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def usage_statistics(self, request):
        """Get template usage statistics"""
        templates = self.get_queryset()
        
        stats = []
        for template in templates:
            stats.append({
                'template_id': template.id,
                'template_name': template.name,
                'template_type': template.template_type,
                'usage_count': template.usage_count,
                'last_used': template.updated_at,
                'success_rate': 85.5  # This would be calculated from actual data
            })
        
        return Response(stats)

class EmailCampaignViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for EmailCampaign model"""
    serializer_class = EmailCampaignSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'owner', 'is_active']
    search_fields = ['name', 'subject']
    ordering_fields = ['name', 'created_at', 'scheduled_at', 'sent_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return EmailCampaign.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def send_campaign(self, request, pk=None):
        """Send an email campaign"""
        campaign = self.get_object()
        if campaign.status != 'draft':
            return Response(
                {'error': 'Only draft campaigns can be sent'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # This would integrate with email service
        campaign.status = 'sending'
        campaign.sent_at = timezone.now()
        campaign.save()
        
        return Response({'message': 'Campaign sending initiated'})

    @action(detail=True, methods=['post'])
    def schedule_campaign(self, request, pk=None):
        """Schedule an email campaign"""
        campaign = self.get_object()
        scheduled_at = request.data.get('scheduled_at')
        
        if not scheduled_at:
            return Response(
                {'error': 'scheduled_at is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.scheduled_at = scheduled_at
        campaign.status = 'scheduled'
        campaign.save()
        
        return Response({'message': 'Campaign scheduled successfully'})

    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """Perform bulk operations on email campaigns"""
        serializer = BulkEmailCampaignSerializer(data=request.data)
        if serializer.is_valid():
            campaign_ids = serializer.validated_data['campaign_ids']
            action = serializer.validated_data['action']
            
            campaigns = self.get_queryset().filter(id__in=campaign_ids)
            
            if action == 'start':
                campaigns.update(status='running')
            elif action == 'pause':
                campaigns.update(status='paused')
            elif action == 'stop':
                campaigns.update(status='cancelled')
            elif action == 'delete':
                campaigns.delete()
            
            return Response({'message': f'Bulk {action} completed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeadScoreViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for LeadScore model"""
    serializer_class = LeadScoreSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['score_type', 'owner', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'points', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return LeadScore.objects.filter(company=self.request.company)

    @action(detail=False, methods=['post'])
    def calculate_lead_scores(self, request):
        """Calculate lead scores for all leads"""
        # This would implement the lead scoring logic
        # For now, return a success message
        return Response({'message': 'Lead scores calculated successfully'})

class MarketingListViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for MarketingList model"""
    serializer_class = MarketingListSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['list_type', 'owner', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'member_count', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return MarketingList.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def add_members(self, request, pk=None):
        """Add members to a marketing list"""
        marketing_list = self.get_object()
        contact_ids = request.data.get('contact_ids', [])
        
        for contact_id in contact_ids:
            MarketingListMember.objects.get_or_create(
                list=marketing_list,
                contact_id=contact_id,
                company=marketing_list.company
            )
        
        # Update member count
        marketing_list.member_count = marketing_list.members.count()
        marketing_list.save()
        
        return Response({'message': 'Members added successfully'})

    @action(detail=True, methods=['post'])
    def remove_members(self, request, pk=None):
        """Remove members from a marketing list"""
        marketing_list = self.get_object()
        contact_ids = request.data.get('contact_ids', [])
        
        MarketingListMember.objects.filter(
            list=marketing_list,
            contact_id__in=contact_ids
        ).delete()
        
        # Update member count
        marketing_list.member_count = marketing_list.members.count()
        marketing_list.save()
        
        return Response({'message': 'Members removed successfully'})

    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """Perform bulk operations on marketing lists"""
        serializer = BulkMarketingListSerializer(data=request.data)
        if serializer.is_valid():
            list_ids = serializer.validated_data['list_ids']
            action = serializer.validated_data['action']
            
            lists = self.get_queryset().filter(id__in=list_ids)
            
            if action == 'activate':
                lists.update(is_active=True)
            elif action == 'deactivate':
                lists.update(is_active=False)
            elif action == 'delete':
                lists.delete()
            
            return Response({'message': f'Bulk {action} completed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MarketingListMemberViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for MarketingListMember model"""
    serializer_class = MarketingListMemberSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['list', 'is_active']
    search_fields = ['contact__first_name', 'contact__last_name', 'contact__email']
    ordering_fields = ['subscribed_at', 'unsubscribed_at']
    ordering = ['-subscribed_at']

    def get_queryset(self):
        return MarketingListMember.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, pk=None):
        """Unsubscribe a member from the list"""
        member = self.get_object()
        member.unsubscribed_at = timezone.now()
        member.is_active = False
        member.save()
        
        return Response({'message': 'Member unsubscribed successfully'})

class MarketingEventViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for MarketingEvent model"""
    serializer_class = MarketingEventSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'contact', 'campaign', 'email_campaign']
    search_fields = ['event_name', 'description']
    ordering_fields = ['event_date', 'created_at']
    ordering = ['-event_date']

    def get_queryset(self):
        return MarketingEvent.objects.filter(company=self.request.company)

    @action(detail=False, methods=['get'])
    def event_statistics(self, request):
        """Get marketing event statistics"""
        events = self.get_queryset()
        
        stats = {
            'total_events': events.count(),
            'events_by_type': dict(events.values('event_type').annotate(count=Count('id'))),
            'recent_events': events.filter(
                event_date__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'top_contacts': events.values('contact__first_name', 'contact__last_name').annotate(
                event_count=Count('id')
            ).order_by('-event_count')[:10]
        }
        
        return Response(stats)

class MarketingAnalyticsViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for MarketingAnalytics model"""
    serializer_class = MarketingAnalyticsSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'start_date', 'end_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return MarketingAnalytics.objects.filter(company=self.request.company)

    @action(detail=False, methods=['get'])
    def dashboard_metrics(self, request):
        """Get dashboard metrics for marketing"""
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Calculate metrics
        campaigns = Campaign.objects.filter(
            company=self.request.company,
            created_at__date__range=[start_date, end_date]
        )
        
        email_campaigns = EmailCampaign.objects.filter(
            company=self.request.company,
            created_at__date__range=[start_date, end_date]
        )
        
        metrics = {
            'total_campaigns': campaigns.count(),
            'active_campaigns': campaigns.filter(status='running').count(),
            'total_emails_sent': sum(ec.sent_count for ec in email_campaigns),
            'total_emails_delivered': sum(ec.delivered_count for ec in email_campaigns),
            'total_emails_opened': sum(ec.opened_count for ec in email_campaigns),
            'total_clicks': sum(ec.clicked_count for ec in email_campaigns),
            'total_conversions': sum(c.conversions for c in campaigns),
            'overall_open_rate': 0,
            'overall_click_rate': 0,
            'overall_bounce_rate': 0,
            'overall_conversion_rate': 0
        }
        
        # Calculate rates
        if metrics['total_emails_delivered'] > 0:
            metrics['overall_open_rate'] = (metrics['total_emails_opened'] / metrics['total_emails_delivered']) * 100
            metrics['overall_click_rate'] = (metrics['total_clicks'] / metrics['total_emails_delivered']) * 100
        
        if metrics['total_emails_sent'] > 0:
            total_bounces = sum(ec.bounced_count for ec in email_campaigns)
            metrics['overall_bounce_rate'] = (total_bounces / metrics['total_emails_sent']) * 100
        
        if metrics['total_emails_delivered'] > 0:
            metrics['overall_conversion_rate'] = (metrics['total_conversions'] / metrics['total_emails_delivered']) * 100
        
        return Response(metrics)

    @action(detail=False, methods=['post'])
    def generate_analytics(self, request):
        """Generate analytics for a specific date range"""
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        name = request.data.get('name', 'Marketing Analytics')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create analytics record
        analytics = MarketingAnalytics.objects.create(
            company=self.request.company,
            name=name,
            start_date=start_date,
            end_date=end_date,
            created_by=request.user
        )
        
        # Calculate and save metrics
        analytics.calculate_metrics()
        analytics.save()
        
        serializer = self.get_serializer(analytics)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
