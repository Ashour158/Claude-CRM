# territories/urls.py
# Territories URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'territories', views.TerritoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]