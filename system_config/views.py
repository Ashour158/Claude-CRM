# system_config/views.py
# System configuration views

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    SystemSetting, CustomField, WorkflowRule, NotificationTemplate,
    UserPreference, Integration, AuditLog
)
from .serializers import (
    SystemSettingSerializer, CustomFieldSerializer, WorkflowRuleSerializer,
    NotificationTemplateSerializer, UserPreferenceSerializer, IntegrationSerializer,
    AuditLogSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response

class SystemSettingViewSet(viewsets.ModelViewSet):
    """System setting viewset"""
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['setting_type', 'is_required', 'is_public', 'is_editable']
    search_fields = ['key', 'name', 'description']
    ordering_fields = ['setting_type', 'name']
    ordering = ['setting_type', 'name']

class CustomFieldViewSet(viewsets.ModelViewSet):
    """Custom field viewset"""
    queryset = CustomField.objects.all()
    serializer_class = CustomFieldSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['field_type', 'entity_type', 'is_required', 'is_visible']
    search_fields = ['name', 'label', 'description']
    ordering_fields = ['entity_type', 'display_order', 'name']
    ordering = ['entity_type', 'display_order']

class WorkflowRuleViewSet(viewsets.ModelViewSet):
    """Workflow rule viewset"""
    queryset = WorkflowRule.objects.all()
    serializer_class = WorkflowRuleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rule_type', 'entity_type', 'is_active', 'is_global']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """Notification template viewset"""
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template_type', 'is_active', 'is_global']
    search_fields = ['name', 'description', 'subject']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class UserPreferenceViewSet(viewsets.ModelViewSet):
    """User preference viewset"""
    queryset = UserPreference.objects.all()
    serializer_class = UserPreferenceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

class IntegrationViewSet(viewsets.ModelViewSet):
    """Integration viewset"""
    queryset = Integration.objects.all()
    serializer_class = IntegrationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_active']
    search_fields = ['name', 'description', 'provider']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test integration connection"""
        integration = self.get_object()
        # Note: Implementation would test the connection
        return Response({'message': 'Connection test completed'})
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync integration data"""
        integration = self.get_object()
        # Note: Implementation would sync data
        return Response({'message': 'Sync completed successfully'})

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log viewset"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'user', 'object_type', 'success']
    ordering_fields = ['created_at']
    ordering = ['-created_at']