# audit/views.py
# Views for audit module

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import AuditLog, AuditLogExport, ComplianceReport, AuditPolicy
from .serializers import (
    AuditLogSerializer, AuditLogExportSerializer,
    ComplianceReportSerializer, AuditPolicySerializer
)

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to audit logs"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'entity_type', 'user', 'is_sensitive', 'requires_review', 'reviewed']
    search_fields = ['user_email', 'entity_name', 'entity_id', 'action_description']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Mark an audit log entry as reviewed"""
        log = self.get_object()
        log.reviewed = True
        log.reviewed_by = request.user
        from django.utils import timezone
        log.reviewed_at = timezone.now()
        log.save()
        return Response({'status': 'reviewed'})
    
    @action(detail=False, methods=['get'])
    def by_entity(self, request):
        """Get audit logs for a specific entity"""
        entity_type = request.query_params.get('entity_type')
        entity_id = request.query_params.get('entity_id')
        if entity_type and entity_id:
            logs = self.queryset.filter(entity_type=entity_type, entity_id=entity_id)
            page = self.paginate_queryset(logs)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(logs, many=True)
            return Response(serializer.data)
        return Response({'error': 'entity_type and entity_id required'}, status=400)

class AuditLogExportViewSet(viewsets.ModelViewSet):
    queryset = AuditLogExport.objects.all()
    serializer_class = AuditLogExportSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'format']
    search_fields = ['name']
    ordering_fields = ['requested_at']
    ordering = ['-requested_at']
    
    @action(detail=True, methods=['post'])
    def start_export(self, request, pk=None):
        """Start the export process"""
        export = self.get_object()
        export.status = 'processing'
        export.save()
        # Add export processing logic here
        return Response({'status': 'processing'})

class ComplianceReportViewSet(viewsets.ModelViewSet):
    queryset = ComplianceReport.objects.all()
    serializer_class = ComplianceReportSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'is_published']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'period_start']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a compliance report"""
        report = self.get_object()
        report.is_published = True
        from django.utils import timezone
        report.published_at = timezone.now()
        report.save()
        return Response({'status': 'published'})

class AuditPolicyViewSet(viewsets.ModelViewSet):
    queryset = AuditPolicy.objects.all()
    serializer_class = AuditPolicySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'alert_on_violation']
    search_fields = ['name', 'description']
    ordering_fields = ['priority', 'name']
    ordering = ['-priority']
