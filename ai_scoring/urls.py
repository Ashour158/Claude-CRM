# ai_scoring/urls.py
# AI Lead Scoring and Model Training URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ScoringModelViewSet, ModelTrainingViewSet, ModelPredictionViewSet,
    ModelDriftViewSet, ModelValidationViewSet, ModelFeatureViewSet,
    ModelInsightViewSet
)

router = DefaultRouter()
router.register(r'models', ScoringModelViewSet)
router.register(r'training', ModelTrainingViewSet)
router.register(r'predictions', ModelPredictionViewSet)
router.register(r'drift', ModelDriftViewSet)
router.register(r'validation', ModelValidationViewSet)
router.register(r'features', ModelFeatureViewSet)
router.register(r'insights', ModelInsightViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
