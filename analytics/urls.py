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

urlpatterns = [
    path('', include(router.urls)),
]
