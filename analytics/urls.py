# analytics/urls.py
# Analytics URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'dashboards', views.DashboardViewSet)
router.register(r'reports', views.ReportViewSet)
router.register(r'kpis', views.KPIViewSet)
router.register(r'kpi-measurements', views.KPIMeasurementViewSet)
router.register(r'sales-forecasts', views.SalesForecastViewSet)
router.register(r'activity-analytics', views.ActivityAnalyticsViewSet)
router.register(r'sales-analytics', views.SalesAnalyticsViewSet)
router.register(r'lead-analytics', views.LeadAnalyticsViewSet)

# Fact tables for analytics
router.register(r'fact-deal-stage-transitions', views.FactDealStageTransitionViewSet, basename='fact-deal-stage-transition')
router.register(r'fact-activities', views.FactActivityViewSet, basename='fact-activity')
router.register(r'fact-lead-conversions', views.FactLeadConversionViewSet, basename='fact-lead-conversion')

# Export jobs
router.register(r'export-jobs', views.AnalyticsExportJobViewSet, basename='analytics-export-job')

urlpatterns = [
    path('', include(router.urls)),
]
