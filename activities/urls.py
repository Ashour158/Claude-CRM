# activities/urls.py
# Activities URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'activities', views.ActivityViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'events', views.EventViewSet)

urlpatterns = [
    path('', include(router.urls)),
]