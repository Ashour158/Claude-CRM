# mobile/apps.py
# Mobile Application App Configuration

from django.apps import AppConfig

class MobileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mobile'
    verbose_name = 'Mobile Application'
    
    def ready(self):
        import mobile.signals
