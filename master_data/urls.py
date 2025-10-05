# master_data/urls.py
# Master data URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'data-categories', views.DataCategoryViewSet)
router.register(r'master-data-fields', views.MasterDataFieldViewSet)
router.register(r'data-quality-rules', views.DataQualityRuleViewSet)
router.register(r'data-quality-violations', views.DataQualityViolationViewSet)
router.register(r'data-imports', views.DataImportViewSet)
router.register(r'data-exports', views.DataExportViewSet)
router.register(r'data-synchronizations', views.DataSynchronizationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
