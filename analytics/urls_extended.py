# analytics/urls_extended.py
# URL routes for extended analytics features

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from analytics.views_extended import (
    MetricDefinitionViewSet,
    MetricComputationDAGViewSet,
    TimeSeriesSnapshotViewSet,
    TimeSeriesPipelineViewSet,
    AnomalyDetectionRuleViewSet,
    AnomalyDetectionViewSet,
    ReportScheduleViewSet,
    ReportSnapshotViewSet,
    DataQualityRuleViewSet,
    DataQualityCheckViewSet,
    DataQualityAlertViewSet,
    DataQualityDashboardViewSet
)

router = DefaultRouter()

# Metrics Catalog
router.register(r'metrics', MetricDefinitionViewSet, basename='metric')
router.register(r'metric-dags', MetricComputationDAGViewSet, basename='metric-dag')

# Time Series
router.register(r'time-series-snapshots', TimeSeriesSnapshotViewSet, basename='time-series-snapshot')
router.register(r'time-series-pipelines', TimeSeriesPipelineViewSet, basename='time-series-pipeline')

# Anomaly Detection
router.register(r'anomaly-rules', AnomalyDetectionRuleViewSet, basename='anomaly-rule')
router.register(r'anomalies', AnomalyDetectionViewSet, basename='anomaly')

# Report Scheduling
router.register(r'report-schedules', ReportScheduleViewSet, basename='report-schedule')
router.register(r'report-snapshots', ReportSnapshotViewSet, basename='report-snapshot')

# Data Quality
router.register(r'data-quality-rules', DataQualityRuleViewSet, basename='data-quality-rule')
router.register(r'data-quality-checks', DataQualityCheckViewSet, basename='data-quality-check')
router.register(r'data-quality-alerts', DataQualityAlertViewSet, basename='data-quality-alert')
router.register(r'data-quality-dashboards', DataQualityDashboardViewSet, basename='data-quality-dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
