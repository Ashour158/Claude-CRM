# crm/activities/urls.py
# URL routing for activities/timeline

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from crm.activities.views import TimelineViewSet

router = DefaultRouter()
router.register(r'', TimelineViewSet, basename='timeline')

urlpatterns = [
    path('', include(router.urls)),
]
