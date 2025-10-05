# core/management/commands/run_migrations.py
# Django management command to run all migrations

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Run all migrations and setup database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fake-initial',
            action='store_true',
            help='Mark initial migrations as applied without running them',
        )
        parser.add_argument(
            '--fake',
            action='store_true',
            help='Mark migrations as applied without running them',
        )
        parser.add_argument(
            '--plan',
            action='store_true',
            help='Show migration plan without running migrations',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database migration process...'))
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write('✅ Database connection successful')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database connection failed: {e}')
            )
            return
        
        # Run migrations
        try:
            if options['plan']:
                self.stdout.write('📋 Migration plan:')
                call_command('migrate', '--plan', verbosity=2)
            else:
                self.stdout.write('🔄 Running migrations...')
                
                # Run migrations with appropriate flags
                migrate_args = []
                if options['fake_initial']:
                    migrate_args.append('--fake-initial')
                if options['fake']:
                    migrate_args.append('--fake')
                
                call_command('migrate', *migrate_args, verbosity=2)
                
                self.stdout.write('✅ Migrations completed successfully!')
                
                # Show migration status
                self.stdout.write('\n📊 Migration status:')
                call_command('showmigrations', verbosity=1)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Migration failed: {e}')
            )
            return
        
        # Create superuser if needed
        self.create_superuser()
        
        # Setup initial data
        self.setup_initial_data()

    def create_superuser(self):
        """Create superuser if none exists"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('👤 Creating superuser...')
            try:
                call_command('createsuperuser', interactive=False, verbosity=0)
                self.stdout.write('✅ Superuser created successfully!')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Could not create superuser: {e}')
                )
        else:
            self.stdout.write('✅ Superuser already exists')

    def setup_initial_data(self):
        """Setup initial data"""
        self.stdout.write('🌱 Setting up initial data...')
        
        try:
            # Create initial company
            from core.models import Company
            if not Company.objects.exists():
                company = Company.objects.create(
                    name='Default Company',
                    domain='localhost',
                    is_active=True
                )
                self.stdout.write(f'✅ Created default company: {company.name}')
            
            # Create initial pipeline stages
            from deals.models import PipelineStage
            if not PipelineStage.objects.exists():
                stages = [
                    ('Lead', 'Initial lead stage'),
                    ('Qualified', 'Qualified lead stage'),
                    ('Proposal', 'Proposal stage'),
                    ('Negotiation', 'Negotiation stage'),
                    ('Closed Won', 'Closed won stage'),
                    ('Closed Lost', 'Closed lost stage')
                ]
                
                for i, (name, description) in enumerate(stages):
                    PipelineStage.objects.create(
                        name=name,
                        description=description,
                        order=i,
                        is_active=True,
                        company=Company.objects.first()
                    )
                
                self.stdout.write('✅ Created default pipeline stages')
            
            # Create initial product categories
            from products.models import ProductCategory
            if not ProductCategory.objects.exists():
                categories = [
                    'Software',
                    'Hardware',
                    'Services',
                    'Consulting'
                ]
                
                for category_name in categories:
                    ProductCategory.objects.create(
                        name=category_name,
                        description=f'{category_name} products and services',
                        is_active=True,
                        company=Company.objects.first()
                    )
                
                self.stdout.write('✅ Created default product categories')
            
            # Create initial territories
            from territories.models import Territory
            if not Territory.objects.exists():
                territories = [
                    'North Territory',
                    'South Territory',
                    'East Territory',
                    'West Territory',
                    'Central Territory'
                ]
                
                for territory_name in territories:
                    Territory.objects.create(
                        name=territory_name,
                        description=f'{territory_name} sales territory',
                        is_active=True,
                        company=Company.objects.first()
                    )
                
                self.stdout.write('✅ Created default territories')
            
            self.stdout.write('✅ Initial data setup completed!')
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Error setting up initial data: {e}')
            )
