# crm/__init__.py
# CRM package with modular domain structure

# Make submodules importable at package level
from crm.accounts.models import Account
from crm.contacts.models import Contact
from crm.leads.models import Lead
from crm.activities.models import TimelineEvent, Activity
from crm.custom_fields.models import CustomFieldDefinition
from crm.custom_fields.services import CustomFieldService
from crm.leads.services import LeadConversionService, LeadConversionResult, AlreadyConvertedError
from crm.permissions.models import Role, RolePermission, PermissionMatrix

__all__ = [
    'Account',
    'Contact', 
    'Lead',
    'TimelineEvent',
    'Activity',
    'CustomFieldDefinition',
    'CustomFieldService',
    'LeadConversionService',
    'LeadConversionResult',
    'AlreadyConvertedError',
    'Role',
    'RolePermission',
    'PermissionMatrix',
]
