# security/apps.py
# Enterprise Security App Configuration

from django.apps import AppConfig

class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security'
    verbose_name = 'Enterprise Security'
    
    def ready(self):
        import security.signals
