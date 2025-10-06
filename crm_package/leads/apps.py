"""
Django app configuration for leads module.
"""

from django.apps import AppConfig


class LeadsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_package.leads'
    verbose_name = 'CRM Leads'
