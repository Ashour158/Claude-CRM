# audit/views.py
# Audit Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q

from .models import AuditLog, AuditPolicy, AuditReview, ComplianceReport, AuditExport
from .serializers import (
    AuditLogSerializer, AuditPolicySerializer, AuditReviewSerializer,
    ComplianceReportSerializer, AuditExportSerializer
)

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log viewing"""
    
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'user', 'is_sensitive', 'requires_review']
    search_fields = ['description', 'request_path']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(company=self.request.user.company)
    
    @action(detail=False, methods=['get'])
    def by_entity(self, request):
        """Get audit logs for specific entity"""
        content_type_id = request.query_params.get('content_type_id')
        object_id = request.query_params.get('object_id')
        
        if not content_type_id or not object_id:
            return Response(
                {'error': 'content_type_id and object_id are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logs = self.get_queryset().filter(
            content_type_id=content_type_id,
            object_id=object_id
        )
        
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Mark audit log as reviewed"""
        audit_log = self.get_object()
        
        # Create or update review
        review, created = AuditReview.objects.get_or_create(
            audit_log=audit_log,
            defaults={
                'policy': None,  # Set appropriate policy
                'reviewer': request.user,
                'status': 'approved'
            }
        )
        
        if not created:
            review.status = 'approved'
            review.reviewer = request.user
            review.save()
        
        return Response({'message': 'Audit log marked as reviewed'})

class AuditPolicyViewSet(viewsets.ModelViewSet):
    """Audit policy management"""
    
    queryset = AuditPolicy.objects.all()
    serializer_class = AuditPolicySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['policy_type', 'is_active', 'compliance_standard']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'priority', 'created_at']
    ordering = ['priority', '-created_at']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        """Set company and created_by"""
        serializer.save(
            company=self.request.user.company,
            created_by=self.request.user
        )

class AuditReviewViewSet(viewsets.ModelViewSet):
    """Audit review management"""
    
    queryset = AuditReview.objects.all()
    serializer_class = AuditReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'reviewer', 'risk_assessment']
    search_fields = ['review_notes', 'compliance_notes']
    ordering_fields = ['assigned_at', 'reviewed_at', 'completed_at']
    ordering = ['-assigned_at']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(audit_log__company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def complete_review(self, request, pk=None):
        """Complete audit review"""
        review = self.get_object()
        
        review.status = 'approved'
        review.reviewed_at = timezone.now()
        review.completed_at = timezone.now()
        review.save()
        
        return Response({'message': 'Review completed'})

class ComplianceReportViewSet(viewsets.ModelViewSet):
    """Compliance report management"""
    
    queryset = ComplianceReport.objects.all()
    serializer_class = ComplianceReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['report_type', 'status', 'compliance_standard']
    search_fields = ['name', 'description']
    ordering_fields = ['generated_at', 'compliance_score']
    ordering = ['-generated_at']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        """Set company and generated_by"""
        serializer.save(
            company=self.request.user.company,
            generated_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def generate_report(self, request, pk=None):
        """Generate compliance report"""
        report = self.get_object()
        
        if report.status != 'generating':
            return Response(
                {'error': 'Report is not in generating status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Implement report generation logic
        # This would typically use background tasks
        
        report.status = 'completed'
        report.save()
        
        return Response({'message': 'Report generation started'})

class AuditExportViewSet(viewsets.ModelViewSet):
    """Audit export management"""
    
    queryset = AuditExport.objects.all()
    serializer_class = AuditExportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'format', 'include_sensitive']
    search_fields = ['name', 'description']
    ordering_fields = ['requested_at', 'completed_at']
    ordering = ['-requested_at']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        """Set company and requested_by"""
        serializer.save(
            company=self.request.user.company,
            requested_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def start_export(self, request, pk=None):
        """Start audit export"""
        export = self.get_object()
        
        if export.status != 'pending':
            return Response(
                {'error': 'Export is not in pending status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update export status
        export.status = 'processing'
        export.started_at = timezone.now()
        export.save()
        
        # Start background export process
        # This would typically use Celery or similar task queue
        
        return Response({'message': 'Export started'})
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download export file"""
        export = self.get_object()
        
        if export.status != 'completed' or not export.file_path:
            return Response(
                {'error': 'Export not ready for download'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return file download response
        # This would typically use Django's FileResponse
        
        return Response({'message': 'Download ready', 'file_path': export.file_path})
