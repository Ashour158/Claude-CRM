# core/management/commands/seed_roles_permissions.py
"""
Management command to seed default roles and permissions.
This command is idempotent and can be run multiple times safely.
"""

import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seed default roles and permissions (idempotent)'

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write('Seeding roles and permissions...')
        
        # Define roles and their permissions
        roles_permissions = {
            'Admin': {
                'description': 'Full system access',
                'permissions': ['add', 'change', 'delete', 'view'],
                'models': ['account', 'contact', 'lead', 'deal', 'activity', 'task', 'event']
            },
            'Sales Manager': {
                'description': 'Manage sales team and operations',
                'permissions': ['add', 'change', 'view'],
                'models': ['account', 'contact', 'lead', 'deal', 'activity', 'task']
            },
            'Sales Representative': {
                'description': 'Basic sales operations',
                'permissions': ['add', 'view'],
                'models': ['contact', 'lead', 'activity', 'task']
            },
            'Viewer': {
                'description': 'Read-only access',
                'permissions': ['view'],
                'models': ['account', 'contact', 'lead', 'deal', 'activity', 'task']
            }
        }
        
        created_count = 0
        updated_count = 0
        
        for role_name, role_config in roles_permissions.items():
            # Create or get the group
            group, created = Group.objects.get_or_create(name=role_name)
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created role: {role_name}'))
                logger.info(f'Created role: {role_name}')
            else:
                updated_count += 1
                self.stdout.write(f'Updating role: {role_name}')
            
            # Clear existing permissions to ensure idempotency
            group.permissions.clear()
            
            # Add permissions for each model
            for model_name in role_config['models']:
                for perm_type in role_config['permissions']:
                    # Try to find the permission
                    perm_codename = f'{perm_type}_{model_name}'
                    try:
                        permission = Permission.objects.get(codename=perm_codename)
                        group.permissions.add(permission)
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Permission not found: {perm_codename} (will be available after migrations)'
                            )
                        )
            
            group.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded roles and permissions. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
        logger.info(f'Roles and permissions seeded. Created: {created_count}, Updated: {updated_count}')
