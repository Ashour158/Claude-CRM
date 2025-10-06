# core/management/commands/seed_roles_permissions.py
"""
Management command to seed baseline roles and permissions.
Creates: Admin, SalesRep, ReadOnly roles with default permissions.
Idempotent: Can be run multiple times without creating duplicates.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction


class Command(BaseCommand):
    help = 'Seed baseline roles and permissions (idempotent)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-admin',
            action='store_true',
            help='Skip creating Admin role',
        )
        parser.add_argument(
            '--skip-sales',
            action='store_true',
            help='Skip creating SalesRep role',
        )
        parser.add_argument(
            '--skip-readonly',
            action='store_true',
            help='Skip creating ReadOnly role',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting role and permission seeding...'))
        
        roles_created = 0
        roles_updated = 0
        
        # Define roles and their permissions
        roles_config = {
            'Admin': {
                'skip_flag': options.get('skip_admin', False),
                'permissions': 'all',
                'description': 'Full access to all modules and settings'
            },
            'SalesRep': {
                'skip_flag': options.get('skip_sales', False),
                'permissions': [
                    'crm.view_account', 'crm.add_account', 'crm.change_account',
                    'crm.view_contact', 'crm.add_contact', 'crm.change_contact',
                    'crm.view_lead', 'crm.add_lead', 'crm.change_lead',
                    'deals.view_deal', 'deals.add_deal', 'deals.change_deal',
                    'activities.view_activity', 'activities.add_activity', 'activities.change_activity',
                    'activities.view_task', 'activities.add_task', 'activities.change_task',
                ],
                'description': 'Sales representatives with CRM access'
            },
            'ReadOnly': {
                'skip_flag': options.get('skip_readonly', False),
                'permissions': [
                    'crm.view_account', 'crm.view_contact', 'crm.view_lead',
                    'deals.view_deal',
                    'activities.view_activity', 'activities.view_task',
                ],
                'description': 'Read-only access to CRM data'
            }
        }
        
        for role_name, config in roles_config.items():
            if config['skip_flag']:
                self.stdout.write(
                    self.style.WARNING(f'Skipping {role_name} role (--skip flag)')
                )
                continue
            
            # Create or get role group
            group, created = Group.objects.get_or_create(name=role_name)
            
            if created:
                roles_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created role: {role_name}')
                )
            else:
                roles_updated += 1
                self.stdout.write(
                    self.style.WARNING(f'→ Role already exists: {role_name} (updating permissions)')
                )
            
            # Clear existing permissions
            group.permissions.clear()
            
            # Add permissions
            if config['permissions'] == 'all':
                # Admin gets all permissions
                all_permissions = Permission.objects.all()
                group.permissions.set(all_permissions)
                self.stdout.write(
                    f'  Assigned {all_permissions.count()} permissions (ALL)'
                )
            else:
                # Add specific permissions
                permissions_added = 0
                permissions_missing = []
                
                for perm_string in config['permissions']:
                    try:
                        app_label, codename = perm_string.split('.')
                        permission = Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=codename
                        )
                        group.permissions.add(permission)
                        permissions_added += 1
                    except Permission.DoesNotExist:
                        permissions_missing.append(perm_string)
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠ Permission not found: {perm_string}')
                        )
                    except ValueError:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Invalid permission format: {perm_string}')
                        )
                
                self.stdout.write(
                    f'  Assigned {permissions_added} permissions'
                )
                
                if permissions_missing:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Note: {len(permissions_missing)} permissions could not be found. '
                            f'They may not exist yet if migrations haven\'t been run.'
                        )
                    )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('Role seeding complete!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Roles created: {roles_created}')
        self.stdout.write(f'Roles updated: {roles_updated}')
        self.stdout.write(f'Total roles: {Group.objects.count()}')
        self.stdout.write('')
        
        # List all roles
        self.stdout.write(self.style.SUCCESS('Current roles:'))
        for group in Group.objects.all().order_by('name'):
            perm_count = group.permissions.count()
            self.stdout.write(f'  • {group.name}: {perm_count} permissions')
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                'Roles can be assigned to users via Django admin or User model.'
            )
        )
