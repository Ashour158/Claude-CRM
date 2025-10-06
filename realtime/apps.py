# realtime/apps.py
# Django app configuration for realtime

from django.apps import AppConfig


class RealtimeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'realtime'
    verbose_name = 'Real-time Infrastructure'
    
    def ready(self):
        """
        App initialization
        
        Uncomment the following lines to auto-connect signals
        for automatic event publishing on model changes:
        """
        # from .signals import (
        #     connect_deal_signals,
        #     connect_activity_signals,
        #     connect_timeline_signals
        # )
        # connect_deal_signals()
        # connect_activity_signals()
        # connect_timeline_signals()
        pass
