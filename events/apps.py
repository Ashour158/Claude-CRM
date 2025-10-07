# events/apps.py
# Event-Driven Architecture App Configuration

from django.apps import AppConfig

class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'
    verbose_name = 'Event-Driven Architecture'
    
    def ready(self):
        import events.signals
