# workflow/apps.py
# Workflow app configuration

from django.apps import AppConfig


class WorkflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workflow'
    verbose_name = 'Workflow & Automation'
    
    def ready(self):
        """Import signals when app is ready"""
        # Import signals here if needed
        pass
