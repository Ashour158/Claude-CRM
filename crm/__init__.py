# crm/__init__.py
# CRM package with modular domain structure

# Models and services are imported from submodules
# Import them directly from their locations instead of re-exporting here
# to avoid circular import and app registry issues

default_app_config = 'crm.apps.CrmConfig'

