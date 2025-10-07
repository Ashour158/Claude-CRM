# data_import/urls.py
# URL configuration for data import module

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ImportTemplateViewSet, ImportJobViewSet,
    ImportStagingRecordViewSet, DuplicateRuleViewSet
)

router = DefaultRouter()
router.register(r'templates', ImportTemplateViewSet, basename='import-template')
router.register(r'jobs', ImportJobViewSet, basename='import-job')
router.register(r'staging', ImportStagingRecordViewSet, basename='import-staging')
router.register(r'duplicate-rules', DuplicateRuleViewSet, basename='duplicate-rule')

urlpatterns = [
    path('', include(router.urls)),
]
