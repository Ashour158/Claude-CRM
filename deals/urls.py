# deals/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from deals.views import (
    PipelineStageViewSet, DealViewSet, DealProductViewSet,
    DealActivityViewSet, DealForecastViewSet
)

router = DefaultRouter()
router.register(r'pipeline-stages', PipelineStageViewSet, basename='pipeline-stage')
router.register(r'deals', DealViewSet, basename='deal')
router.register(r'deal-products', DealProductViewSet, basename='deal-product')
router.register(r'deal-activities', DealActivityViewSet, basename='deal-activity')
router.register(r'deal-forecasts', DealForecastViewSet, basename='deal-forecast')

urlpatterns = [
    path('', include(router.urls)),
]