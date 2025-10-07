# api_versioning/views.py
# Views for API versioning module

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import APIVersion, APIEndpoint, APIClient, APIRequestLog
from .serializers import (
    APIVersionSerializer, APIEndpointSerializer,
    APIClientSerializer, APIRequestLogSerializer
)

class APIVersionViewSet(viewsets.ModelViewSet):
    queryset = APIVersion.objects.all()
    serializer_class = APIVersionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_default', 'is_active']
    search_fields = ['version_number', 'version_name']
    ordering_fields = ['version_number', 'release_date', 'request_count']
    ordering = ['-version_number']
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set this version as the default"""
        version = self.get_object()
        APIVersion.objects.update(is_default=False)
        version.is_default = True
        version.save()
        return Response({'status': 'set as default'})

class APIEndpointViewSet(viewsets.ModelViewSet):
    queryset = APIEndpoint.objects.all()
    serializer_class = APIEndpointSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['api_version', 'method', 'is_active']
    search_fields = ['path', 'description']
    ordering_fields = ['path']
    ordering = ['path']

class APIClientViewSet(viewsets.ModelViewSet):
    queryset = APIClient.objects.all()
    serializer_class = APIClientSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['client_type', 'is_active', 'preferred_version']
    search_fields = ['name', 'client_id']
    ordering_fields = ['name', 'total_requests', 'last_request']
    ordering = ['-created_at']

class APIRequestLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = APIRequestLog.objects.all()
    serializer_class = APIRequestLogSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['api_version', 'api_client', 'method', 'status_code']
    search_fields = ['path', 'user__email']
    ordering_fields = ['timestamp', 'response_time_ms']
    ordering = ['-timestamp']
