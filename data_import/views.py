# data_import/views.py
# Views for data import module

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import ImportTemplate, ImportJob, ImportStagingRecord, DuplicateRule
from .serializers import (
    ImportTemplateSerializer, ImportJobSerializer,
    ImportStagingRecordSerializer, DuplicateRuleSerializer
)

class ImportTemplateViewSet(viewsets.ModelViewSet):
    queryset = ImportTemplate.objects.all()
    serializer_class = ImportTemplateSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['entity_type', 'is_active', 'dedupe_enabled']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'usage_count']
    ordering = ['-created_at']

class ImportJobViewSet(viewsets.ModelViewSet):
    queryset = ImportJob.objects.all()
    serializer_class = ImportJobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'file_type', 'import_template']
    search_fields = ['name', 'file_name']
    ordering_fields = ['created_at', 'progress_percentage']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start processing an import job"""
        job = self.get_object()
        # Add import processing logic here
        job.status = 'processing'
        job.save()
        return Response({'status': 'started'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an import job"""
        job = self.get_object()
        job.status = 'cancelled'
        job.save()
        return Response({'status': 'cancelled'})

class ImportStagingRecordViewSet(viewsets.ModelViewSet):
    queryset = ImportStagingRecord.objects.all()
    serializer_class = ImportStagingRecordSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['import_job', 'status', 'is_valid', 'is_duplicate']
    search_fields = ['row_number']
    ordering_fields = ['row_number']
    ordering = ['row_number']

class DuplicateRuleViewSet(viewsets.ModelViewSet):
    queryset = DuplicateRule.objects.all()
    serializer_class = DuplicateRuleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['entity_type', 'match_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['priority', 'name']
    ordering = ['-priority']
