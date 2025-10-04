# activities/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from activities.views import ActivityViewSet, TaskViewSet, EventViewSet

router = DefaultRouter()
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'events', EventViewSet, basename='event')

urlpatterns = [
    path('', include(router.urls)),
]