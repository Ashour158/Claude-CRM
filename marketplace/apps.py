# marketplace/apps.py
# Marketplace and Extensibility App Configuration

from django.apps import AppConfig

class MarketplaceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'marketplace'
    verbose_name = 'Marketplace and Extensibility'
    
    def ready(self):
        import marketplace.signals
