# simulation/apps.py
# What-If Analysis and Simulation App Configuration

from django.apps import AppConfig

class SimulationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'simulation'
    verbose_name = 'What-If Analysis and Simulation'
    
    def ready(self):
        import simulation.signals
