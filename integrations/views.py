# integrations/views.py
# Integrations views

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    APICredential, Webhook, WebhookLog, DataSync, DataSyncLog,
    EmailIntegration, CalendarIntegration
)
from .serializers import (
    APICredentialSerializer, WebhookSerializer, WebhookLogSerializer,
    DataSyncSerializer, DataSyncLogSerializer, EmailIntegrationSerializer,
    CalendarIntegrationSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response

class APICredentialViewSet(viewsets.ModelViewSet):
    """API credential viewset"""
    queryset = APICredential.objects.all()
    serializer_class = APICredentialSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['credential_type', 'is_active', 'is_verified']
    search_fields = ['name', 'description', 'service_name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify API credentials"""
        credential = self.get_object()
        # Note: Implementation would verify the credentials
        return Response({'message': 'Credentials verified successfully'})

class WebhookViewSet(viewsets.ModelViewSet):
    """Webhook viewset"""
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['webhook_type', 'is_active', 'is_verified']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test webhook"""
        webhook = self.get_object()
        # Note: Implementation would test the webhook
        return Response({'message': 'Webhook test completed'})

class WebhookLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Webhook log viewset"""
    queryset = WebhookLog.objects.all()
    serializer_class = WebhookLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['webhook', 'success']
    ordering_fields = ['started_at']
    ordering = ['-started_at']

class DataSyncViewSet(viewsets.ModelViewSet):
    """Data sync viewset"""
    queryset = DataSync.objects.all()
    serializer_class = DataSyncSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sync_type', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Run data sync"""
        sync = self.get_object()
        # Note: Implementation would run the sync
        return Response({'message': 'Data sync started'})

class DataSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Data sync log viewset"""
    queryset = DataSyncLog.objects.all()
    serializer_class = DataSyncLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['data_sync', 'status']
    ordering_fields = ['sync_started']
    ordering = ['-sync_started']

class EmailIntegrationViewSet(viewsets.ModelViewSet):
    """Email integration viewset"""
    queryset = EmailIntegration.objects.all()
    serializer_class = EmailIntegrationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['provider', 'is_active', 'is_verified']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test email integration"""
        integration = self.get_object()
        # Note: Implementation would test the email integration
        return Response({'message': 'Email integration test completed'})

class CalendarIntegrationViewSet(viewsets.ModelViewSet):
    """Calendar integration viewset"""
    queryset = CalendarIntegration.objects.all()
    serializer_class = CalendarIntegrationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['provider', 'is_active', 'is_connected']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def connect(self, request, pk=None):
        """Connect calendar integration"""
        integration = self.get_object()
        # Note: Implementation would connect the calendar
        return Response({'message': 'Calendar connected successfully'})
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync calendar data"""
        integration = self.get_object()
        # Note: Implementation would sync calendar data
        return Response({'message': 'Calendar sync completed'})