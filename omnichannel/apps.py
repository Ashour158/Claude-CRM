# omnichannel/apps.py
# Omnichannel Communication App Configuration

from django.apps import AppConfig

class OmnichannelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'omnichannel'
    verbose_name = 'Omnichannel Communication'
    
    def ready(self):
        import omnichannel.signals
