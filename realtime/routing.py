# realtime/routing.py
# WebSocket URL routing

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws', consumers.RealtimeConsumer.as_asgi()),
]
