# ai_assistant/apps.py
# AI Assistant App Configuration

from django.apps import AppConfig

class AiAssistantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_assistant'
    verbose_name = 'AI Assistant'
    
    def ready(self):
        import ai_assistant.signals
