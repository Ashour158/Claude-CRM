# omnichannel/urls.py
# Omnichannel Communication URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CommunicationChannelViewSet, ConversationViewSet, MessageViewSet,
    ConversationTemplateViewSet, ConversationRuleViewSet, ConversationMetricViewSet,
    ConversationAnalyticsViewSet
)

router = DefaultRouter()
router.register(r'channels', CommunicationChannelViewSet)
router.register(r'conversations', ConversationViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'templates', ConversationTemplateViewSet)
router.register(r'rules', ConversationRuleViewSet)
router.register(r'metrics', ConversationMetricViewSet)
router.register(r'analytics', ConversationAnalyticsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
