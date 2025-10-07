# marketplace/views.py
# Views for marketplace module

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Plugin, PluginInstallation, PluginExecution, PluginReview
from .serializers import (
    PluginSerializer, PluginInstallationSerializer,
    PluginExecutionSerializer, PluginReviewSerializer
)

class PluginViewSet(viewsets.ModelViewSet):
    queryset = Plugin.objects.all()
    serializer_class = PluginSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['plugin_type', 'status', 'is_featured', 'is_verified', 'is_free']
    search_fields = ['name', 'description', 'developer_name']
    ordering_fields = ['name', 'rating_average', 'install_count', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def install(self, request, pk=None):
        """Install a plugin"""
        plugin = self.get_object()
        # Add installation logic here
        return Response({'status': 'installing'})
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get plugin reviews"""
        plugin = self.get_object()
        reviews = plugin.reviews.all()
        serializer = PluginReviewSerializer(reviews, many=True)
        return Response(serializer.data)

class PluginInstallationViewSet(viewsets.ModelViewSet):
    queryset = PluginInstallation.objects.all()
    serializer_class = PluginInstallationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['plugin', 'status', 'is_enabled']
    search_fields = ['plugin__name']
    ordering_fields = ['installed_at', 'last_updated']
    ordering = ['-installed_at']
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a plugin installation"""
        installation = self.get_object()
        installation.is_enabled = True
        installation.save()
        return Response({'status': 'activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a plugin installation"""
        installation = self.get_object()
        installation.is_enabled = False
        installation.save()
        return Response({'status': 'deactivated'})
    
    @action(detail=True, methods=['post'])
    def uninstall(self, request, pk=None):
        """Uninstall a plugin"""
        installation = self.get_object()
        installation.status = 'uninstalling'
        installation.save()
        return Response({'status': 'uninstalling'})

class PluginExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PluginExecution.objects.all()
    serializer_class = PluginExecutionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['installation', 'status', 'trigger_type']
    search_fields = ['installation__plugin__name']
    ordering_fields = ['started_at', 'duration_ms']
    ordering = ['-started_at']

class PluginReviewViewSet(viewsets.ModelViewSet):
    queryset = PluginReview.objects.all()
    serializer_class = PluginReviewSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['plugin', 'rating', 'is_verified_purchase']
    search_fields = ['title', 'review_text']
    ordering_fields = ['rating', 'helpful_count', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark a review as helpful"""
        review = self.get_object()
        review.helpful_count += 1
        review.save()
        return Response({'helpful_count': review.helpful_count})
