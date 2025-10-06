# analytics/views.py
# Analytics views

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import timedelta
from .models import (
    Dashboard, Report, KPI, KPIMeasurement, SalesForecast,
    ActivityAnalytics, SalesAnalytics, LeadAnalytics,
    FactDealStageTransition, FactActivity, FactLeadConversion,
    AnalyticsExportJob
)
from .serializers import (
    DashboardSerializer, ReportSerializer, KPISerializer, KPIMeasurementSerializer,
    SalesForecastSerializer, ActivityAnalyticsSerializer, SalesAnalyticsSerializer,
    LeadAnalyticsSerializer, FactDealStageTransitionSerializer, FactActivitySerializer,
    FactLeadConversionSerializer, AnalyticsExportJobSerializer
)

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


class FactDealStageTransitionViewSet(viewsets.ReadOnlyModelViewSet):
    """Fact deal stage transition viewset (read-only for analysis)"""
    queryset = FactDealStageTransition.objects.all()
    serializer_class = FactDealStageTransitionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['deal', 'to_stage', 'owner', 'region']
    ordering_fields = ['transition_date']
    ordering = ['-transition_date']
    
    @action(detail=False, methods=['get'])
    def pipeline_velocity(self, request):
        """
        Calculate pipeline velocity metrics.
        Returns average days in each stage and overall cycle time.
        """
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Filter by region if specified
        filters = {'transition_date__gte': start_date}
        region = request.query_params.get('region')
        if region:
            filters['region'] = region
        
        # Calculate average days per stage
        stage_metrics = FactDealStageTransition.objects.filter(
            **filters
        ).values('to_stage').annotate(
            avg_days=Avg('days_in_previous_stage'),
            transition_count=Count('id'),
            total_value=Sum('deal_amount')
        ).order_by('to_stage')
        
        # Calculate overall velocity (deals moving through pipeline)
        total_transitions = FactDealStageTransition.objects.filter(**filters).count()
        won_deals = FactDealStageTransition.objects.filter(
            to_stage='closed_won',
            **filters
        ).count()
        
        return Response({
            'period_days': days,
            'start_date': start_date.date(),
            'stage_metrics': list(stage_metrics),
            'total_transitions': total_transitions,
            'won_deals': won_deals,
            'win_rate': (won_deals / total_transitions * 100) if total_transitions > 0 else 0
        })


class FactActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """Fact activity viewset (read-only for analysis)"""
    queryset = FactActivity.objects.all()
    serializer_class = FactActivitySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['activity_type', 'assigned_to', 'is_completed', 'region']
    ordering_fields = ['activity_date']
    ordering = ['-activity_date']
    
    @action(detail=False, methods=['get'])
    def activity_volume(self, request):
        """
        Calculate activity volume metrics.
        Returns activity counts by type, completion rates, and trends.
        """
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Filter by user or region if specified
        filters = {'activity_date__gte': start_date}
        user_id = request.query_params.get('user_id')
        if user_id:
            filters['assigned_to_id'] = user_id
        region = request.query_params.get('region')
        if region:
            filters['region'] = region
        
        # Volume by activity type
        volume_by_type = FactActivity.objects.filter(
            **filters
        ).values('activity_type').annotate(
            total_count=Count('id'),
            completed_count=Count('id', filter=Q(is_completed=True)),
            avg_duration=Avg('duration_minutes')
        ).order_by('-total_count')
        
        # Overall metrics
        total_activities = FactActivity.objects.filter(**filters).count()
        completed_activities = FactActivity.objects.filter(
            is_completed=True,
            **filters
        ).count()
        
        return Response({
            'period_days': days,
            'start_date': start_date.date(),
            'total_activities': total_activities,
            'completed_activities': completed_activities,
            'completion_rate': (completed_activities / total_activities * 100) if total_activities > 0 else 0,
            'volume_by_type': list(volume_by_type)
        })


class FactLeadConversionViewSet(viewsets.ReadOnlyModelViewSet):
    """Fact lead conversion viewset (read-only for analysis)"""
    queryset = FactLeadConversion.objects.all()
    serializer_class = FactLeadConversionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event_type', 'owner', 'lead_source', 'region']
    ordering_fields = ['event_date']
    ordering = ['-event_date']
    
    @action(detail=False, methods=['get'])
    def conversion_funnel(self, request):
        """
        Calculate conversion funnel metrics.
        Returns conversion rates at each stage of the lead lifecycle.
        """
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Filter by region if specified
        filters = {'event_date__gte': start_date}
        region = request.query_params.get('region')
        if region:
            filters['region'] = region
        
        # Count events by type
        funnel_metrics = FactLeadConversion.objects.filter(
            **filters
        ).values('event_type').annotate(
            event_count=Count('id'),
            avg_days_since_creation=Avg('days_since_creation'),
            total_value=Sum('conversion_value')
        ).order_by('event_type')
        
        # Calculate conversion rates
        created_count = FactLeadConversion.objects.filter(
            event_type='created', **filters
        ).count()
        qualified_count = FactLeadConversion.objects.filter(
            event_type='qualified', **filters
        ).count()
        converted_count = FactLeadConversion.objects.filter(
            event_type='converted', **filters
        ).count()
        
        return Response({
            'period_days': days,
            'start_date': start_date.date(),
            'funnel_metrics': list(funnel_metrics),
            'conversion_rates': {
                'created_to_qualified': (qualified_count / created_count * 100) if created_count > 0 else 0,
                'qualified_to_converted': (converted_count / qualified_count * 100) if qualified_count > 0 else 0,
                'created_to_converted': (converted_count / created_count * 100) if created_count > 0 else 0,
            }
        })


class AnalyticsExportJobViewSet(viewsets.ModelViewSet):
    """Analytics export job viewset"""
    queryset = AnalyticsExportJob.objects.all()
    serializer_class = AnalyticsExportJobSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'export_type', 'data_source']
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Set the owner when creating an export job"""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending or running export job"""
        export_job = self.get_object()
        if export_job.status in ['pending', 'running']:
            export_job.status = 'cancelled'
            export_job.save()
            return Response({'message': 'Export job cancelled'})
        return Response(
            {'error': 'Can only cancel pending or running jobs'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Get download URL for completed export"""
        export_job = self.get_object()
        if export_job.status != 'completed':
            return Response(
                {'error': 'Export not yet completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not export_job.output_file:
            return Response(
                {'error': 'Export file not available'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({
            'download_url': export_job.output_file.url if export_job.output_file else None,
            'total_records': export_job.total_records
        })

