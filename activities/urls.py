# activities/urls.py
# Activities URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from activities.api.views import TimelineEventViewSet

router = DefaultRouter()
router.register(r'activities', views.ActivityViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'timeline', TimelineEventViewSet, basename='timeline')

urlpatterns = [
    path('', include(router.urls)),
]