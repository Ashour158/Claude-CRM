# deals/urls.py
# Deals URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'deals', views.DealViewSet)

urlpatterns = [
    path('', include(router.urls)),
]