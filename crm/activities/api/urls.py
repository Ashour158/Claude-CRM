# crm/activities/api/urls.py
# URL configuration for activities API

from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    path('timeline/', views.timeline_list, name='timeline-list'),
]
