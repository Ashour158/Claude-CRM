# analytics/views.py
# Analytics views

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Dashboard, Report, KPI, KPIMeasurement, SalesForecast,
    ActivityAnalytics, SalesAnalytics, LeadAnalytics
)
from .serializers import (
    DashboardSerializer, ReportSerializer, KPISerializer, KPIMeasurementSerializer,
    SalesForecastSerializer, ActivityAnalyticsSerializer, SalesAnalyticsSerializer,
    LeadAnalyticsSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response

class DashboardViewSet(viewsets.ModelViewSet):
    """Dashboard viewset"""
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_default', 'is_public']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class ReportViewSet(viewsets.ModelViewSet):
    """Report viewset"""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['report_type', 'is_public', 'is_scheduled']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Run report"""
        report = self.get_object()
        # Note: Implementation would run the report and return data
        return Response({'message': 'Report executed successfully'})

class KPIViewSet(viewsets.ModelViewSet):
    """KPI viewset"""
    queryset = KPI.objects.all()
    serializer_class = KPISerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['kpi_type', 'is_public']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class KPIMeasurementViewSet(viewsets.ModelViewSet):
    """KPI measurement viewset"""
    queryset = KPIMeasurement.objects.all()
    serializer_class = KPIMeasurementSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kpi']
    ordering_fields = ['period_end', 'value']
    ordering = ['-period_end']

class SalesForecastViewSet(viewsets.ModelViewSet):
    """Sales forecast viewset"""
    queryset = SalesForecast.objects.all()
    serializer_class = SalesForecastSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['forecast_type']
    ordering_fields = ['period_end', 'forecasted_amount']
    ordering = ['-period_end']

class ActivityAnalyticsViewSet(viewsets.ModelViewSet):
    """Activity analytics viewset"""
    queryset = ActivityAnalytics.objects.all()
    serializer_class = ActivityAnalyticsSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user']
    ordering_fields = ['period_end']
    ordering = ['-period_end']

class SalesAnalyticsViewSet(viewsets.ModelViewSet):
    """Sales analytics viewset"""
    queryset = SalesAnalytics.objects.all()
    serializer_class = SalesAnalyticsSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user']
    ordering_fields = ['period_end']
    ordering = ['-period_end']

class LeadAnalyticsViewSet(viewsets.ModelViewSet):
    """Lead analytics viewset"""
    queryset = LeadAnalytics.objects.all()
    serializer_class = LeadAnalyticsSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user']
    ordering_fields = ['period_end']
    ordering = ['-period_end']
