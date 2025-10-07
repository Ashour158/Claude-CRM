# data_import/views.py
# Data Import API Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import ImportTemplate, ImportJob, StagedRecord, ImportLog, DuplicateMatch
from .serializers import (
    ImportTemplateSerializer, ImportJobSerializer, StagedRecordSerializer,
    ImportLogSerializer, DuplicateMatchSerializer
)

class ImportTemplateViewSet(viewsets.ModelViewSet):
    """Import template management"""
    
    queryset = ImportTemplate.objects.all()
    serializer_class = ImportTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
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

class ImportJobViewSet(viewsets.ModelViewSet):
    """Import job management"""
    
    queryset = ImportJob.objects.all()
    serializer_class = ImportJobSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'template', 'file_type']
    search_fields = ['file_name']
    ordering_fields = ['created_at', 'status']
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
    def start_import(self, request, pk=None):
        """Start import job processing"""
        job = self.get_object()
        
        if job.status != 'pending':
            return Response(
                {'error': 'Job is not in pending status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update job status
        job.status = 'running'
        job.started_at = timezone.now()
        job.save()
        
        # Start background processing (implement actual import logic)
        # This would typically use Celery or similar task queue
        
        return Response({'message': 'Import job started'})
    
    @action(detail=True, methods=['get'])
    def staging_data(self, request, pk=None):
        """Get staged records for preview"""
        job = self.get_object()
        staged_records = job.staged_records.all()
        
        serializer = StagedRecordSerializer(staged_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get import job logs"""
        job = self.get_object()
        logs = job.logs.all()
        
        serializer = ImportLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def duplicates(self, request, pk=None):
        """Get duplicate matches"""
        job = self.get_object()
        duplicates = job.duplicate_matches.all()
        
        serializer = DuplicateMatchSerializer(duplicates, many=True)
        return Response(serializer.data)

class StagedRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """Staged record viewing"""
    
    queryset = StagedRecord.objects.all()
    serializer_class = StagedRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['job', 'is_valid', 'is_duplicate', 'import_status']
    ordering_fields = ['row_number', 'created_at']
    ordering = ['row_number']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(job__company=self.request.user.company)

class ImportLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Import log viewing"""
    
    queryset = ImportLog.objects.all()
    serializer_class = ImportLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['job', 'log_type']
    search_fields = ['message']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(job__company=self.request.user.company)

class DuplicateMatchViewSet(viewsets.ReadOnlyModelViewSet):
    """Duplicate match viewing"""
    
    queryset = DuplicateMatch.objects.all()
    serializer_class = DuplicateMatchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['job', 'resolution', 'match_algorithm']
    ordering_fields = ['similarity_score', 'created_at']
    ordering = ['-similarity_score']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(job__company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def resolve_duplicate(self, request, pk=None):
        """Resolve duplicate match"""
        duplicate = self.get_object()
        resolution = request.data.get('resolution')
        
        if resolution not in ['skip', 'update', 'merge', 'create']:
            return Response(
                {'error': 'Invalid resolution'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        duplicate.resolution = resolution
        duplicate.save()
        
        return Response({'message': f'Duplicate resolved as {resolution}'})
