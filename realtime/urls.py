# realtime/urls.py
# URL routing for real-time API endpoints

from django.urls import path
from . import views

app_name = 'realtime'

urlpatterns = [
    path('poll/', views.long_polling, name='long-polling'),
    path('publish/', views.publish_event, name='publish-event'),
    path('health/', views.health_check, name='health-check'),
]
