"""
Django app configuration for activities module.
"""

from django.apps import AppConfig


class ActivitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_package.activities'
    verbose_name = 'CRM Activities'
