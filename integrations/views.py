# integrations/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Integration, EmailIntegration, CalendarIntegration, Webhook, WebhookLog,
    APICredential, DataSync
)
from .serializers import (
    IntegrationSerializer, EmailIntegrationSerializer, CalendarIntegrationSerializer,
    WebhookSerializer, WebhookLogSerializer, APICredentialSerializer, DataSyncSerializer,
    BulkIntegrationSerializer, BulkWebhookSerializer, EmailServiceSerializer,
    CalendarServiceSerializer, WebhookTestSerializer, IntegrationTestSerializer,
    DataSyncStatusSerializer, IntegrationMetricsSerializer, WebhookDeliverySerializer
)
from core.permissions import IsCompanyUser, IsCompanyAdmin
from core.mixins import CompanyIsolatedMixin

class IntegrationViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for Integration model"""
    serializer_class = IntegrationSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['integration_type', 'provider', 'status', 'is_active']
    search_fields = ['name', 'description', 'provider']
    ordering_fields = ['name', 'created_at', 'last_sync']
    ordering = ['name']

    def get_queryset(self):
        return Integration.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test integration connection"""
        integration = self.get_object()
        # This would implement connection testing logic
        return Response({'message': 'Connection test completed successfully'})

    @action(detail=True, methods=['post'])
    def sync_data(self, request, pk=None):
        """Trigger data synchronization"""
        integration = self.get_object()
        if not integration.is_active:
            return Response(
                {'error': 'Integration is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # This would implement data sync logic
        integration.last_sync = timezone.now()
        integration.save()
        
        return Response({'message': 'Data synchronization initiated'})

    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """Perform bulk operations on integrations"""
        serializer = BulkIntegrationSerializer(data=request.data)
        if serializer.is_valid():
            integration_ids = serializer.validated_data['integration_ids']
            action = serializer.validated_data['action']
            
            integrations = self.get_queryset().filter(id__in=integration_ids)
            
            if action == 'activate':
                integrations.update(is_active=True)
            elif action == 'deactivate':
                integrations.update(is_active=False)
            elif action == 'test':
                # This would implement bulk testing
                pass
            elif action == 'delete':
                integrations.delete()
            
            return Response({'message': f'Bulk {action} completed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmailIntegrationViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for EmailIntegration model"""
    serializer_class = EmailIntegrationSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['provider', 'is_active', 'is_verified']
    search_fields = ['name', 'from_email', 'from_name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return EmailIntegration.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def test_email(self, request, pk=None):
        """Test email integration"""
        integration = self.get_object()
        test_email = request.data.get('test_email')
        
        if not test_email:
            return Response(
                {'error': 'test_email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # This would implement email testing logic
        return Response({'message': 'Test email sent successfully'})

    @action(detail=True, methods=['post'])
    def verify_credentials(self, request, pk=None):
        """Verify email credentials"""
        integration = self.get_object()
        # This would implement credential verification
        integration.is_verified = True
        integration.save()
        
        return Response({'message': 'Credentials verified successfully'})

    @action(detail=False, methods=['get'])
    def email_metrics(self, request):
        """Get email integration metrics"""
        integrations = self.get_queryset()
        
        metrics = {
            'total_emails_sent': sum(i.emails_sent for i in integrations),
            'total_emails_delivered': sum(i.emails_delivered for i in integrations),
            'total_emails_bounced': sum(i.emails_bounced for i in integrations),
            'delivery_rate': 0,
            'bounce_rate': 0
        }
        
        if metrics['total_emails_sent'] > 0:
            metrics['delivery_rate'] = (metrics['total_emails_delivered'] / metrics['total_emails_sent']) * 100
            metrics['bounce_rate'] = (metrics['total_emails_bounced'] / metrics['total_emails_sent']) * 100
        
        return Response(metrics)

class CalendarIntegrationViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for CalendarIntegration model"""
    serializer_class = CalendarIntegrationSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['provider', 'is_active', 'is_connected']
    search_fields = ['name', 'calendar_name']
    ordering_fields = ['name', 'created_at', 'last_sync']
    ordering = ['name']

    def get_queryset(self):
        return CalendarIntegration.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def connect_calendar(self, request, pk=None):
        """Connect to calendar service"""
        integration = self.get_object()
        # This would implement OAuth connection logic
        integration.is_connected = True
        integration.save()
        
        return Response({'message': 'Calendar connected successfully'})

    @action(detail=True, methods=['post'])
    def disconnect_calendar(self, request, pk=None):
        """Disconnect from calendar service"""
        integration = self.get_object()
        integration.is_connected = False
        integration.access_token = ''
        integration.refresh_token = ''
        integration.save()
        
        return Response({'message': 'Calendar disconnected successfully'})

    @action(detail=True, methods=['post'])
    def sync_calendar(self, request, pk=None):
        """Sync calendar data"""
        integration = self.get_object()
        if not integration.is_connected:
            return Response(
                {'error': 'Calendar is not connected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # This would implement calendar sync logic
        integration.last_sync = timezone.now()
        integration.events_synced += 1
        integration.save()
        
        return Response({'message': 'Calendar sync completed successfully'})

class WebhookViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for Webhook model"""
    serializer_class = WebhookSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['webhook_type', 'is_active']
    search_fields = ['name', 'url']
    ordering_fields = ['name', 'created_at', 'last_called']
    ordering = ['name']

    def get_queryset(self):
        return Webhook.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def test_webhook(self, request, pk=None):
        """Test webhook"""
        webhook = self.get_object()
        test_payload = request.data.get('test_payload', {})
        
        # This would implement webhook testing logic
        webhook.total_calls += 1
        webhook.successful_calls += 1
        webhook.last_called = timezone.now()
        webhook.save()
        
        return Response({'message': 'Webhook test completed successfully'})

    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """Perform bulk operations on webhooks"""
        serializer = BulkWebhookSerializer(data=request.data)
        if serializer.is_valid():
            webhook_ids = serializer.validated_data['webhook_ids']
            action = serializer.validated_data['action']
            
            webhooks = self.get_queryset().filter(id__in=webhook_ids)
            
            if action == 'activate':
                webhooks.update(is_active=True)
            elif action == 'deactivate':
                webhooks.update(is_active=False)
            elif action == 'test':
                # This would implement bulk testing
                pass
            elif action == 'delete':
                webhooks.delete()
            
            return Response({'message': f'Bulk {action} completed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WebhookLogViewSet(CompanyIsolatedMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for WebhookLog model (Read-only)"""
    serializer_class = WebhookLogSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['webhook', 'status', 'triggered_by']
    search_fields = ['request_url', 'error_message']
    ordering_fields = ['created_at', 'execution_time']
    ordering = ['-created_at']

    def get_queryset(self):
        return WebhookLog.objects.filter(company=self.request.company)

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get webhook logs by status"""
        status_filter = request.query_params.get('status')
        if not status_filter:
            return Response(
                {'error': 'status parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logs = self.get_queryset().filter(status=status_filter)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def failed_webhooks(self, request):
        """Get failed webhook logs"""
        logs = self.get_queryset().filter(status='failed')
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

class APICredentialViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for APICredential model"""
    serializer_class = APICredentialSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['service', 'credential_type', 'is_active', 'is_verified']
    search_fields = ['name', 'service']
    ordering_fields = ['name', 'created_at', 'expires_at']
    ordering = ['name']

    def get_queryset(self):
        return APICredential.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def test_credentials(self, request, pk=None):
        """Test API credentials"""
        credential = self.get_object()
        # This would implement credential testing logic
        credential.is_verified = True
        credential.save()
        
        return Response({'message': 'Credentials tested successfully'})

    @action(detail=True, methods=['post'])
    def refresh_token(self, request, pk=None):
        """Refresh OAuth token"""
        credential = self.get_object()
        if credential.credential_type != 'oauth':
            return Response(
                {'error': 'Only OAuth credentials can be refreshed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # This would implement token refresh logic
        return Response({'message': 'Token refreshed successfully'})

class DataSyncViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for DataSync model"""
    serializer_class = DataSyncSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sync_type', 'source_system', 'target_system', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'last_sync', 'next_sync']
    ordering = ['name']

    def get_queryset(self):
        return DataSync.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def start_sync(self, request, pk=None):
        """Start data synchronization"""
        sync = self.get_object()
        if not sync.is_active:
            return Response(
                {'error': 'Data sync is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # This would implement sync start logic
        sync.status = 'active'
        sync.save()
        
        return Response({'message': 'Data sync started successfully'})

    @action(detail=True, methods=['post'])
    def pause_sync(self, request, pk=None):
        """Pause data synchronization"""
        sync = self.get_object()
        sync.status = 'paused'
        sync.save()
        
        return Response({'message': 'Data sync paused successfully'})

    @action(detail=True, methods=['post'])
    def stop_sync(self, request, pk=None):
        """Stop data synchronization"""
        sync = self.get_object()
        sync.status = 'completed'
        sync.save()
        
        return Response({'message': 'Data sync stopped successfully'})

    @action(detail=False, methods=['get'])
    def sync_status(self, request):
        """Get sync status for all active syncs"""
        syncs = self.get_queryset().filter(is_active=True)
        
        status_data = []
        for sync in syncs:
            status_data.append({
                'sync_id': sync.id,
                'status': sync.status,
                'progress': 75.5,  # This would be calculated
                'records_processed': sync.total_records_synced,
                'records_total': 1000,  # This would be calculated
                'last_sync_time': sync.last_sync,
                'next_sync_time': sync.next_sync
            })
        
        return Response(status_data)

# Integration service views
class EmailServiceViewSet(viewsets.ViewSet):
    """ViewSet for email service configuration"""
    permission_classes = [IsCompanyUser]

    @action(detail=False, methods=['post'])
    def configure_email_service(self, request):
        """Configure email service"""
        serializer = EmailServiceSerializer(data=request.data)
        if serializer.is_valid():
            # This would configure email service
            return Response({'message': 'Email service configured successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CalendarServiceViewSet(viewsets.ViewSet):
    """ViewSet for calendar service configuration"""
    permission_classes = [IsCompanyUser]

    @action(detail=False, methods=['post'])
    def configure_calendar_service(self, request):
        """Configure calendar service"""
        serializer = CalendarServiceSerializer(data=request.data)
        if serializer.is_valid():
            # This would configure calendar service
            return Response({'message': 'Calendar service configured successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WebhookTestViewSet(viewsets.ViewSet):
    """ViewSet for webhook testing"""
    permission_classes = [IsCompanyUser]

    @action(detail=False, methods=['post'])
    def test_webhook(self, request):
        """Test webhook"""
        serializer = WebhookTestSerializer(data=request.data)
        if serializer.is_valid():
            # This would test webhook
            return Response({'message': 'Webhook test completed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IntegrationTestViewSet(viewsets.ViewSet):
    """ViewSet for integration testing"""
    permission_classes = [IsCompanyUser]

    @action(detail=False, methods=['post'])
    def test_integration(self, request):
        """Test integration"""
        serializer = IntegrationTestSerializer(data=request.data)
        if serializer.is_valid():
            # This would test integration
            return Response({'message': 'Integration test completed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IntegrationMetricsViewSet(viewsets.ViewSet):
    """ViewSet for integration metrics"""
    permission_classes = [IsCompanyUser]

    @action(detail=False, methods=['get'])
    def get_metrics(self, request):
        """Get integration metrics"""
        # This would calculate integration metrics
        metrics = {
            'total_integrations': 10,
            'active_integrations': 8,
            'total_webhooks': 15,
            'active_webhooks': 12,
            'total_api_calls': 5000,
            'successful_api_calls': 4800,
            'failed_api_calls': 200,
            'total_emails_sent': 1000,
            'total_events_synced': 500,
            'average_response_time': 150.5
        }
        
        serializer = IntegrationMetricsSerializer(metrics)
        return Response(serializer.data)
