# ai_scoring/apps.py
# AI Lead Scoring and Model Training App Configuration

from django.apps import AppConfig

class AiScoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_scoring'
    verbose_name = 'AI Lead Scoring and Model Training'
    
    def ready(self):
        import ai_scoring.signals
