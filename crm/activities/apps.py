# crm/activities/apps.py
from django.apps import AppConfig


class CrmActivitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm.activities'
    label = 'crm_activities'  # Unique label to avoid conflict with old activities app
    verbose_name = 'CRM Activities'
