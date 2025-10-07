# analytics/views_extended.py
# API views for extended analytics features

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from analytics.metrics_catalog import (
    MetricDefinition,
    MetricComputationDAG
)
from analytics.time_series import (
    TimeSeriesSnapshot,
    TimeSeriesPipeline
)
from analytics.anomaly_detection import (
    AnomalyDetectionRule,
    AnomalyDetection
)
from analytics.report_scheduling import (
    ReportSchedule,
    ReportSnapshot
)
from analytics.data_quality import (
    DataQualityRule,
    DataQualityCheck,
    DataQualityAlert,
    DataQualityDashboard
)
from analytics.serializers_extended import (
    MetricDefinitionSerializer,
    MetricComputationDAGSerializer,
    TimeSeriesSnapshotSerializer,
    TimeSeriesPipelineSerializer,
    AnomalyDetectionRuleSerializer,
    AnomalyDetectionSerializer,
    ReportScheduleSerializer,
    ReportSnapshotSerializer,
    DataQualityRuleSerializer,
    DataQualityCheckSerializer,
    DataQualityAlertSerializer,
    DataQualityDashboardSerializer
)
from analytics.services import (
    TimeSeriesService,
    AnomalyDetectionService,
    DataQualityService
)


class MetricDefinitionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MetricDefinition
    Provides CRUD operations and introspection
    """
    serializer_class = MetricDefinitionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MetricDefinition.objects.filter(
            company=self.request.user.company
        )
    
    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            owner=self.request.user
        )
    
    @action(detail=True, methods=['get'])
    def lineage(self, request, pk=None):
        """Get metric lineage"""
        metric = self.get_object()
        lineage = metric.get_lineage()
        return Response({'lineage': lineage})
    
    @action(detail=True, methods=['get'])
    def dependency_graph(self, request, pk=None):
        """Get metric dependency graph"""
        metric = self.get_object()
        graph = metric.get_dependency_graph()
        return Response({'graph': graph})
    
    @action(detail=False, methods=['get'])
    def catalog(self, request):
        """Get full metrics catalog with metadata"""
        metrics = self.get_queryset()
        
        catalog = {
            'metrics': MetricDefinitionSerializer(metrics, many=True).data,
            'categories': MetricDefinition.objects.filter(
                company=request.user.company
            ).values_list('category', flat=True).distinct(),
            'total_count': metrics.count()
        }
        
        return Response(catalog)


class MetricComputationDAGViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MetricComputationDAG
    Manages computation graphs and execution
    """
    serializer_class = MetricComputationDAGSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MetricComputationDAG.objects.filter(
            company=self.request.user.company
        )
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate DAG structure"""
        dag = self.get_object()
        is_valid, message = dag.validate_dag()
        return Response({
            'valid': is_valid,
            'message': message
        })
    
    @action(detail=True, methods=['post'])
    def compute(self, request, pk=None):
        """Execute DAG computation"""
        dag = self.get_object()
        
        # Validate DAG first
        is_valid, message = dag.validate_dag()
        if not is_valid:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute metrics in topological order
        execution_order = dag.topological_sort()
        results = []
        
        for metric_name in execution_order:
            try:
                metric = MetricDefinition.objects.get(
                    name=metric_name,
                    company=dag.company
                )
                # Create snapshot
                service = TimeSeriesService()
                snapshot = service.create_snapshot(
                    metric=metric,
                    snapshot_date=timezone.now().date()
                )
                results.append({
                    'metric': metric_name,
                    'success': True,
                    'snapshot_id': snapshot.id
                })
            except Exception as e:
                results.append({
                    'metric': metric_name,
                    'success': False,
                    'error': str(e)
                })
        
        # Update last computed timestamp
        dag.last_computed = timezone.now()
        dag.save(update_fields=['last_computed'])
        
        return Response({
            'dag_id': dag.id,
            'execution_order': execution_order,
            'results': results
        })


class TimeSeriesSnapshotViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TimeSeriesSnapshot
    Provides time series data access
    """
    serializer_class = TimeSeriesSnapshotSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = TimeSeriesSnapshot.objects.filter(
            company=self.request.user.company
        )
        
        # Filter by metric
        metric_id = self.request.query_params.get('metric')
        if metric_id:
            queryset = queryset.filter(metric_id=metric_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(snapshot_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(snapshot_date__lte=end_date)
        
        return queryset.order_by('-snapshot_date')
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class TimeSeriesPipelineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TimeSeriesPipeline
    Manages time series data pipelines
    """
    serializer_class = TimeSeriesPipelineSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TimeSeriesPipeline.objects.filter(
            company=self.request.user.company
        )
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Execute pipeline manually"""
        pipeline = self.get_object()
        results = pipeline.run_pipeline()
        
        return Response({
            'pipeline_id': pipeline.id,
            'results': results,
            'executed_at': timezone.now().isoformat()
        })


class AnomalyDetectionRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AnomalyDetectionRule
    Manages anomaly detection rules
    """
    serializer_class = AnomalyDetectionRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AnomalyDetectionRule.objects.filter(
            company=self.request.user.company
        )
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def detect(self, request, pk=None):
        """Run anomaly detection on recent snapshots"""
        rule = self.get_object()
        
        # Get date range from request
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        # Run detection
        service = AnomalyDetectionService()
        anomalies = service.batch_detect(rule, start_date, end_date)
        
        return Response({
            'rule_id': rule.id,
            'anomalies_detected': len(anomalies),
            'anomalies': AnomalyDetectionSerializer(anomalies, many=True).data
        })


class AnomalyDetectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AnomalyDetection
    Access detected anomalies
    """
    serializer_class = AnomalyDetectionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = AnomalyDetection.objects.filter(
            company=self.request.user.company
        )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by severity
        severity_filter = self.request.query_params.get('severity')
        if severity_filter:
            queryset = queryset.filter(severity=severity_filter)
        
        return queryset.order_by('-detected_at')
    
    @action(detail=True, methods=['post'])
    def investigate(self, request, pk=None):
        """Mark anomaly as under investigation"""
        anomaly = self.get_object()
        anomaly.status = 'investigating'
        anomaly.investigated_by = request.user
        anomaly.investigated_at = timezone.now()
        anomaly.save()
        
        return Response(AnomalyDetectionSerializer(anomaly).data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve anomaly"""
        anomaly = self.get_object()
        anomaly.status = 'resolved'
        anomaly.resolution_notes = request.data.get('notes', '')
        anomaly.save()
        
        return Response(AnomalyDetectionSerializer(anomaly).data)


class ReportScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ReportSchedule
    Manages scheduled reports
    """
    serializer_class = ReportScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ReportSchedule.objects.filter(
            company=self.request.user.company
        )
    
    def perform_create(self, serializer):
        schedule = serializer.save(company=self.request.user.company)
        # Calculate initial next_run
        schedule.next_run = schedule.calculate_next_run()
        schedule.save(update_fields=['next_run'])
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute scheduled report immediately"""
        schedule = self.get_object()
        success, snapshot = schedule.execute()
        
        return Response({
            'success': success,
            'snapshot': ReportSnapshotSerializer(snapshot).data
        })


class ReportSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ReportSnapshot
    Access report snapshots (read-only)
    """
    serializer_class = ReportSnapshotSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ReportSnapshot.objects.filter(
            company=self.request.user.company
        )
        
        # Filter by report
        report_id = self.request.query_params.get('report')
        if report_id:
            queryset = queryset.filter(report_id=report_id)
        
        # Filter by schedule
        schedule_id = self.request.query_params.get('schedule')
        if schedule_id:
            queryset = queryset.filter(schedule_id=schedule_id)
        
        return queryset.order_by('-generated_at')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download report file"""
        snapshot = self.get_object()
        
        # TODO: Implement actual file download
        # For now, return file path
        return Response({
            'file_path': snapshot.file_path,
            'download_url': snapshot.get_download_url()
        })


class DataQualityRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DataQualityRule
    Manages data quality rules
    """
    serializer_class = DataQualityRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DataQualityRule.objects.filter(
            company=self.request.user.company
        )
    
    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            owner=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def evaluate(self, request, pk=None):
        """Evaluate data quality rule"""
        rule = self.get_object()
        incremental = request.data.get('incremental', True)
        
        # Evaluate rule
        start_time = timezone.now()
        result = rule.evaluate(incremental=incremental)
        execution_time = (timezone.now() - start_time).total_seconds() * 1000
        
        # Create check record
        check = DataQualityCheck.objects.create(
            rule=rule,
            execution_time_ms=int(execution_time),
            status='passed' if result.get('records_failed', 0) == 0 else 'failed',
            total_records=result.get('total_records', 0),
            records_checked=result.get('records_checked', 0),
            records_passed=result.get('records_passed', 0),
            records_failed=result.get('records_failed', 0),
            failure_percentage=(
                result.get('records_failed', 0) / result.get('records_checked', 1) * 100
                if result.get('records_checked', 0) > 0 else 0
            ),
            check_details=result,
            failed_records_sample=result.get('failed_records_sample', []),
            company=rule.company
        )
        
        # Create alert if needed
        if check.should_alert():
            alert = check.create_alert()
        
        # Update rule last_run
        rule.last_run = timezone.now()
        if incremental:
            rule.last_evaluated_timestamp = timezone.now()
        rule.save(update_fields=['last_run', 'last_evaluated_timestamp'])
        
        return Response(DataQualityCheckSerializer(check).data)


class DataQualityCheckViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for DataQualityCheck
    Access data quality check results
    """
    serializer_class = DataQualityCheckSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = DataQualityCheck.objects.filter(
            company=self.request.user.company
        )
        
        # Filter by rule
        rule_id = self.request.query_params.get('rule')
        if rule_id:
            queryset = queryset.filter(rule_id=rule_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-executed_at')


class DataQualityAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DataQualityAlert
    Manage data quality alerts
    """
    serializer_class = DataQualityAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = DataQualityAlert.objects.filter(
            company=self.request.user.company
        )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge alert"""
        alert = self.get_object()
        alert.acknowledge(request.user)
        return Response(DataQualityAlertSerializer(alert).data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve alert"""
        alert = self.get_object()
        notes = request.data.get('notes', '')
        alert.resolve(request.user, notes)
        return Response(DataQualityAlertSerializer(alert).data)


class DataQualityDashboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DataQualityDashboard
    Manage data quality dashboards
    """
    serializer_class = DataQualityDashboardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DataQualityDashboard.objects.filter(
            company=self.request.user.company
        )
    
    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            owner=self.request.user
        )
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get dashboard summary"""
        dashboard = self.get_object()
        summary = dashboard.get_summary()
        return Response(summary)
