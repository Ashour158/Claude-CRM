"""
Django app configuration for workflow module.
"""

from django.apps import AppConfig


class WorkflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_package.workflow'
    verbose_name = 'CRM Workflow'
