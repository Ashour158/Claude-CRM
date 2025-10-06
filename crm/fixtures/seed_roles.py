# crm/fixtures/seed_roles.py
# Seed data for default roles and permissions

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Company
from crm.permissions.models import Role, RolePermission
from crm.permissions.enums import PermissionAction


DEFAULT_ROLES = [
    {
        'code': 'admin',
        'name': 'Administrator',
        'description': 'Full access to all features and data',
        'is_system': True,
        'permissions': {
            'account': ['view', 'create', 'edit', 'delete', 'merge', 'export', 'bulk_update'],
            'contact': ['view', 'create', 'edit', 'delete', 'merge', 'export', 'bulk_update'],
            'lead': ['view', 'create', 'edit', 'delete', 'convert', 'export', 'bulk_update'],
            'deal': ['view', 'create', 'edit', 'delete', 'export', 'bulk_update'],
            'product': ['view', 'create', 'edit', 'delete', 'export'],
            'activity': ['view', 'create', 'edit', 'delete'],
            'custom_field': ['manage_custom_fields'],
            'system': ['manage_permissions', 'manage_users'],
        }
    },
    {
        'code': 'sales_rep',
        'name': 'Sales Representative',
        'description': 'Can manage own leads, contacts, accounts, and deals',
        'is_system': True,
        'permissions': {
            'account': ['view', 'create', 'edit', 'export'],
            'contact': ['view', 'create', 'edit', 'export'],
            'lead': ['view', 'create', 'edit', 'convert'],
            'deal': ['view', 'create', 'edit'],
            'product': ['view'],
            'activity': ['view', 'create', 'edit'],
        }
    },
    {
        'code': 'read_only',
        'name': 'Read Only',
        'description': 'View-only access to CRM data',
        'is_system': True,
        'permissions': {
            'account': ['view'],
            'contact': ['view'],
            'lead': ['view'],
            'deal': ['view'],
            'product': ['view'],
            'activity': ['view'],
        }
    }
]


@transaction.atomic
def seed_roles_for_organization(organization: Company):
    """
    Seed default roles and permissions for an organization.
    
    Args:
        organization: The organization to seed roles for
    """
    for role_data in DEFAULT_ROLES:
        # Create or update role
        role, created = Role.objects.update_or_create(
            organization=organization,
            code=role_data['code'],
            defaults={
                'name': role_data['name'],
                'description': role_data['description'],
                'is_system': role_data['is_system'],
                'is_active': True,
            }
        )
        
        if created or True:  # Always update permissions
            # Delete existing permissions
            RolePermission.objects.filter(
                organization=organization,
                role=role
            ).delete()
            
            # Create new permissions
            for object_type, actions in role_data['permissions'].items():
                for action in actions:
                    RolePermission.objects.create(
                        organization=organization,
                        role=role,
                        object_type=object_type,
                        action=action
                    )
    
    return len(DEFAULT_ROLES)


class Command(BaseCommand):
    help = 'Seed default roles and permissions for all organizations'
    
    def handle(self, *args, **options):
        orgs = Company.objects.filter(is_active=True)
        
        total_created = 0
        for org in orgs:
            count = seed_roles_for_organization(org)
            total_created += count
            self.stdout.write(
                self.style.SUCCESS(f'Seeded {count} roles for {org.name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded roles for {orgs.count()} organizations')
        )
