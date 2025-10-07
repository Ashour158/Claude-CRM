# ai_assistant/urls.py
# AI Assistant URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIAssistantViewSet, AIInteractionViewSet, 
    PredictiveModelViewSet, PredictionViewSet, 
    AnomalyDetectionViewSet
)

router = DefaultRouter()
router.register(r'assistants', AIAssistantViewSet)
router.register(r'interactions', AIInteractionViewSet)
router.register(r'models', PredictiveModelViewSet)
router.register(r'predictions', PredictionViewSet)
router.register(r'anomalies', AnomalyDetectionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
