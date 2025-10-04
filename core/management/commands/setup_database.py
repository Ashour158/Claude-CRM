# core/management/commands/setup_database.py
# Django management command to set up the database

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up the database with migrations and initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migrations',
            action='store_true',
            help='Skip running migrations'
        )
        parser.add_argument(
            '--skip-sample-data',
            action='store_true',
            help='Skip creating sample data'
        )
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create a superuser'
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up database...')
        
        # Run migrations
        if not options['skip_migrations']:
            self.stdout.write('Running migrations...')
            call_command('migrate', verbosity=2)
            self.stdout.write(self.style.SUCCESS('Migrations completed'))
        
        # Create superuser
        if options['create_superuser']:
            self.stdout.write('Creating superuser...')
            call_command('createsuperuser', interactive=True)
        
        # Create sample data
        if not options['skip_sample_data']:
            self.stdout.write('Creating sample data...')
            call_command('create_sample_data')
            self.stdout.write(self.style.SUCCESS('Sample data created'))
        
        # Set up Row Level Security
        self.setup_rls()
        
        self.stdout.write(
            self.style.SUCCESS('Database setup completed successfully!')
        )

    def setup_rls(self):
        """Set up Row Level Security policies"""
        self.stdout.write('Setting up Row Level Security...')
        
        with connection.cursor() as cursor:
            # Enable RLS on all company-isolated tables
            tables = [
                'accounts', 'contacts', 'leads', 'deals', 'activities', 
                'tasks', 'events', 'territories', 'territory_rules',
                'products', 'product_categories', 'price_lists', 'price_list_items'
            ]
            
            for table in tables:
                try:
                    cursor.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;')
                    self.stdout.write(f'  ✓ Enabled RLS on {table}')
                except Exception as e:
                    self.stdout.write(f'  ⚠ Could not enable RLS on {table}: {e}')
            
            # Create RLS policies
            self.create_rls_policies(cursor)
        
        self.stdout.write(self.style.SUCCESS('Row Level Security configured'))

    def create_rls_policies(self, cursor):
        """Create RLS policies for multi-tenancy"""
        policies = [
            {
                'table': 'accounts',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'contacts',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'leads',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'deals',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'activities',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'tasks',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'events',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'territories',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'territory_rules',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'products',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'product_categories',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'price_lists',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            },
            {
                'table': 'price_list_items',
                'policy': 'company_isolation',
                'definition': 'company_id = current_setting(\'app.current_company_id\')::uuid'
            }
        ]
        
        for policy in policies:
            try:
                cursor.execute(f'''
                    CREATE POLICY {policy['policy']} ON {policy['table']}
                    FOR ALL TO PUBLIC
                    USING ({policy['definition']});
                ''')
                self.stdout.write(f'  ✓ Created RLS policy for {policy["table"]}')
            except Exception as e:
                self.stdout.write(f'  ⚠ Could not create policy for {policy["table"]}: {e}')
