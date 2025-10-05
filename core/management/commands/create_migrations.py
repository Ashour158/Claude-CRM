# core/management/commands/create_migrations.py
# Django management command to create all migrations

from django.core.management.base import BaseCommand
from django.core.management import call_command
import os

class Command(BaseCommand):
    help = 'Create migrations for all apps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apps',
            nargs='+',
            default=[
                'core', 'crm', 'activities', 'deals', 'products', 
                'territories', 'sales', 'vendors', 'analytics', 
                'marketing', 'system_config', 'integrations', 
                'master_data', 'workflow'
            ],
            help='Apps to create migrations for',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating migrations for all apps...'))
        
        apps = options['apps']
        dry_run = options['dry_run']
        
        for app in apps:
            try:
                self.stdout.write(f'Creating migrations for {app}...')
                
                if dry_run:
                    self.stdout.write(f'[DRY RUN] Would create migrations for {app}')
                else:
                    call_command('makemigrations', app, verbosity=0)
                    self.stdout.write(f'✅ Created migrations for {app}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error creating migrations for {app}: {e}')
                )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('✅ All migrations created successfully!')
            )
            self.stdout.write('Run "python manage.py migrate" to apply migrations.')
        else:
            self.stdout.write('Dry run completed. No migrations were created.')
