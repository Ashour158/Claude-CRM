# events/urls.py
# Event-Driven Architecture URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EventTypeViewSet, EventViewSet, EventHandlerViewSet,
    EventExecutionViewSet, EventSubscriptionViewSet, EventStreamViewSet
)

router = DefaultRouter()
router.register(r'types', EventTypeViewSet)
router.register(r'events', EventViewSet)
router.register(r'handlers', EventHandlerViewSet)
router.register(r'executions', EventExecutionViewSet)
router.register(r'subscriptions', EventSubscriptionViewSet)
router.register(r'streams', EventStreamViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
