# master_data/views.py
# Master data views

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    DataCategory, MasterDataField, DataQualityRule, DataQualityViolation,
    DataImport, DataExport, DataSynchronization
)
from .serializers import (
    DataCategorySerializer, MasterDataFieldSerializer, DataQualityRuleSerializer,
    DataQualityViolationSerializer, DataImportSerializer, DataExportSerializer,
    DataSynchronizationSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response

class DataCategoryViewSet(viewsets.ModelViewSet):
    """Data category viewset"""
    queryset = DataCategory.objects.all()
    serializer_class = DataCategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']

class MasterDataFieldViewSet(viewsets.ModelViewSet):
    """Master data field viewset"""
    queryset = MasterDataField.objects.all()
    serializer_class = MasterDataFieldSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['field_type', 'is_required', 'is_visible', 'is_editable']
    search_fields = ['name', 'label', 'description']
    ordering_fields = ['display_order', 'name']
    ordering = ['display_order']

class DataQualityRuleViewSet(viewsets.ModelViewSet):
    """Data quality rule viewset"""
    queryset = DataQualityRule.objects.all()
    serializer_class = DataQualityRuleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rule_type', 'severity', 'is_active', 'is_global']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Run data quality rule"""
        rule = self.get_object()
        # Note: Implementation would run the rule
        return Response({'message': 'Data quality rule executed'})

class DataQualityViolationViewSet(viewsets.ModelViewSet):
    """Data quality violation viewset"""
    queryset = DataQualityViolation.objects.all()
    serializer_class = DataQualityViolationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['rule', 'status', 'entity_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve data quality violation"""
        violation = self.get_object()
        violation.status = 'resolved'
        violation.save()
        return Response({'message': 'Violation resolved successfully'})

class DataImportViewSet(viewsets.ModelViewSet):
    """Data import viewset"""
    queryset = DataImport.objects.all()
    serializer_class = DataImportSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['import_type', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Run data import"""
        import_job = self.get_object()
        # Note: Implementation would run the import
        return Response({'message': 'Data import started'})

class DataExportViewSet(viewsets.ModelViewSet):
    """Data export viewset"""
    queryset = DataExport.objects.all()
    serializer_class = DataExportSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['export_type', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Run data export"""
        export_job = self.get_object()
        # Note: Implementation would run the export
        return Response({'message': 'Data export started'})

class DataSynchronizationViewSet(viewsets.ModelViewSet):
    """Data synchronization viewset"""
    queryset = DataSynchronization.objects.all()
    serializer_class = DataSynchronizationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sync_type', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Run data synchronization"""
        sync = self.get_object()
        # Note: Implementation would run the sync
        return Response({'message': 'Data synchronization started'})
