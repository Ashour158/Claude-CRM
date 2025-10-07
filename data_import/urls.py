# data_import/urls.py
# Data Import URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ImportTemplateViewSet, ImportJobViewSet, StagedRecordViewSet,
    ImportLogViewSet, DuplicateMatchViewSet
)

router = DefaultRouter()
router.register(r'templates', ImportTemplateViewSet)
router.register(r'jobs', ImportJobViewSet)
router.register(r'staged-records', StagedRecordViewSet)
router.register(r'logs', ImportLogViewSet)
router.register(r'duplicates', DuplicateMatchViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
