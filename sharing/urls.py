# sharing/urls.py
# URL configuration for sharing app

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SharingRuleViewSet, RecordShareViewSet

router = DefaultRouter()
router.register(r'rules', SharingRuleViewSet, basename='sharing-rule')
router.register(r'shares', RecordShareViewSet, basename='record-share')

urlpatterns = [
    path('', include(router.urls)),
]
