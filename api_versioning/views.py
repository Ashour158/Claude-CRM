# api_versioning/views.py
# API Versioning Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import APIVersion, APIEndpoint, APIClient, APIRequestLog, APIDeprecationNotice
from .serializers import (
    APIVersionSerializer, APIEndpointSerializer, APIClientSerializer,
    APIRequestLogSerializer, APIDeprecationNoticeSerializer
)

class APIVersionViewSet(viewsets.ModelViewSet):
    """API version management"""
    
    queryset = APIVersion.objects.all()
    serializer_class = APIVersionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_default', 'is_public']
    search_fields = ['version', 'name', 'description']
    ordering_fields = ['version', 'created_at', 'release_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        """Set company and created_by"""
        serializer.save(
            company=self.request.user.company,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set as default version"""
        version = self.get_object()
        
        # Unset other default versions
        APIVersion.objects.filter(
            company=request.user.company, 
            is_default=True
        ).update(is_default=False)
        
        # Set this as default
        version.is_default = True
        version.save()
        
        return Response({'message': f'Version {version.version} set as default'})
    
    @action(detail=True, methods=['get'])
    def endpoints(self, request, pk=None):
        """Get endpoints for this version"""
        version = self.get_object()
        endpoints = version.endpoints.all()
        
        serializer = APIEndpointSerializer(endpoints, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def clients(self, request, pk=None):
        """Get clients using this version"""
        version = self.get_object()
        clients = version.primary_clients.all() | version.supported_clients.all()
        
        serializer = APIClientSerializer(clients, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for this version"""
        version = self.get_object()
        
        # Get request statistics
        total_requests = version.request_logs.count()
        successful_requests = version.request_logs.filter(status_code__lt=400).count()
        error_requests = version.request_logs.filter(status_code__gte=400).count()
        
        # Get average response time
        avg_response_time = version.request_logs.aggregate(
            avg_time=models.Avg('response_time')
        )['avg_time'] or 0
        
        # Get unique clients
        unique_clients = version.request_logs.values('client').distinct().count()
        
        return Response({
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'error_requests': error_requests,
            'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            'average_response_time': round(avg_response_time, 2),
            'unique_clients': unique_clients
        })

class APIEndpointViewSet(viewsets.ModelViewSet):
    """API endpoint management"""
    
    queryset = APIEndpoint.objects.all()
    serializer_class = APIEndpointSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['version', 'method', 'is_active', 'is_deprecated']
    search_fields = ['path', 'description']
    ordering_fields = ['path', 'method', 'created_at']
    ordering = ['path', 'method']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(version__company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def deprecate(self, request, pk=None):
        """Deprecate endpoint"""
        endpoint = self.get_object()
        deprecation_notice = request.data.get('deprecation_notice', '')
        
        endpoint.is_deprecated = True
        endpoint.deprecation_notice = deprecation_notice
        endpoint.save()
        
        return Response({'message': f'Endpoint {endpoint.path} deprecated'})

class APIClientViewSet(viewsets.ModelViewSet):
    """API client management"""
    
    queryset = APIClient.objects.all()
    serializer_class = APIClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['client_type', 'is_active', 'primary_version']
    search_fields = ['name', 'description', 'contact_email']
    ordering_fields = ['name', 'created_at', 'last_used']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        """Set company and created_by"""
        serializer.save(
            company=self.request.user.company,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def regenerate_secret(self, request, pk=None):
        """Regenerate client secret"""
        client = self.get_object()
        
        # Generate new secret (implement actual secret generation)
        new_secret = f"secret_{client.client_id}_{timezone.now().timestamp()}"
        client.client_secret = new_secret
        client.save()
        
        return Response({'message': 'Client secret regenerated', 'new_secret': new_secret})
    
    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """Get client usage statistics"""
        client = self.get_object()
        
        # Get request statistics
        total_requests = client.request_logs.count()
        recent_requests = client.request_logs.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(days=30)
        ).count()
        
        # Get error rate
        error_requests = client.request_logs.filter(status_code__gte=400).count()
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Get average response time
        avg_response_time = client.request_logs.aggregate(
            avg_time=models.Avg('response_time')
        )['avg_time'] or 0
        
        return Response({
            'total_requests': total_requests,
            'recent_requests': recent_requests,
            'error_rate': round(error_rate, 2),
            'average_response_time': round(avg_response_time, 2),
            'last_used': client.last_used
        })

class APIRequestLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API request log viewing"""
    
    queryset = APIRequestLog.objects.all()
    serializer_class = APIRequestLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['client', 'version', 'status_code', 'method']
    search_fields = ['path', 'ip_address']
    ordering_fields = ['timestamp', 'response_time', 'status_code']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(client__company=self.request.user.company)

class APIDeprecationNoticeViewSet(viewsets.ModelViewSet):
    """API deprecation notice management"""
    
    queryset = APIDeprecationNotice.objects.all()
    serializer_class = APIDeprecationNoticeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['version', 'severity', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['deprecation_date', 'created_at']
    ordering = ['-deprecation_date']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(version__company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge deprecation notice"""
        notice = self.get_object()
        notice.acknowledged_by.add(request.user)
        
        return Response({'message': 'Deprecation notice acknowledged'})
