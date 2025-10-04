# core/management/commands/create_sample_data.py
# Django management command to create sample data

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from core.models import Company, UserCompanyAccess
from crm.models import Account, Contact, Lead
from territories.models import Territory
from deals.models import PipelineStage, Deal
from products.models import ProductCategory, Product
from activities.models import Activity, Task
import random
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing and development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-name',
            type=str,
            default='Sample Company',
            help='Name of the company to create'
        )
        parser.add_argument(
            '--users-count',
            type=int,
            default=5,
            help='Number of users to create'
        )
        parser.add_argument(
            '--accounts-count',
            type=int,
            default=20,
            help='Number of accounts to create'
        )
        parser.add_argument(
            '--contacts-count',
            type=int,
            default=50,
            help='Number of contacts to create'
        )
        parser.add_argument(
            '--leads-count',
            type=int,
            default=30,
            help='Number of leads to create'
        )
        parser.add_argument(
            '--deals-count',
            type=int,
            default=15,
            help='Number of deals to create'
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            # Create company
            company = self.create_company(options['company_name'])
            self.stdout.write(f'Created company: {company.name}')

            # Create users
            users = self.create_users(company, options['users_count'])
            self.stdout.write(f'Created {len(users)} users')

            # Create territories
            territories = self.create_territories(company)
            self.stdout.write(f'Created {len(territories)} territories')

            # Create pipeline stages
            stages = self.create_pipeline_stages(company)
            self.stdout.write(f'Created {len(stages)} pipeline stages')

            # Create product categories and products
            categories = self.create_product_categories(company)
            products = self.create_products(company, categories)
            self.stdout.write(f'Created {len(categories)} categories and {len(products)} products')

            # Create accounts
            accounts = self.create_accounts(company, users, territories, options['accounts_count'])
            self.stdout.write(f'Created {len(accounts)} accounts')

            # Create contacts
            contacts = self.create_contacts(company, users, accounts, options['contacts_count'])
            self.stdout.write(f'Created {len(contacts)} contacts')

            # Create leads
            leads = self.create_leads(company, users, territories, options['leads_count'])
            self.stdout.write(f'Created {len(leads)} leads')

            # Create deals
            deals = self.create_deals(company, users, accounts, contacts, stages, options['deals_count'])
            self.stdout.write(f'Created {len(deals)} deals')

            # Create activities
            activities = self.create_activities(company, users, accounts, contacts, leads, deals)
            self.stdout.write(f'Created {len(activities)} activities')

            # Create tasks
            tasks = self.create_tasks(company, users, accounts, contacts, leads, deals)
            self.stdout.write(f'Created {len(tasks)} tasks')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )

    def create_company(self, name):
        """Create a sample company"""
        company = Company.objects.create(
            name=name,
            email=f'{name.lower().replace(" ", "")}@example.com',
            phone='+1-555-0123',
            address_line1='123 Business St',
            city='New York',
            state='NY',
            postal_code='10001',
            country='US',
            timezone='America/New_York',
            currency='USD'
        )
        return company

    def create_users(self, company, count):
        """Create sample users"""
        users = []
        roles = ['admin', 'manager', 'sales_rep', 'user']
        
        for i in range(count):
            user = User.objects.create_user(
                email=f'user{i+1}@{company.name.lower().replace(" ", "")}.com',
                first_name=f'User{i+1}',
                last_name='Smith',
                password='password123'
            )
            
            # Add user to company
            UserCompanyAccess.objects.create(
                user=user,
                company=company,
                role=random.choice(roles),
                is_primary=(i == 0)  # First user is primary
            )
            users.append(user)
        
        return users

    def create_territories(self, company):
        """Create sample territories"""
        territories = []
        territory_data = [
            {'name': 'North America', 'type': 'geographic', 'countries': ['USA', 'CAN']},
            {'name': 'Europe', 'type': 'geographic', 'countries': ['GBR', 'FRA', 'DEU']},
            {'name': 'Asia Pacific', 'type': 'geographic', 'countries': ['JPN', 'AUS', 'SGP']},
            {'name': 'Enterprise', 'type': 'customer_segment', 'customer_types': ['enterprise']},
            {'name': 'SMB', 'type': 'customer_segment', 'customer_types': ['small_business']},
        ]
        
        for data in territory_data:
            territory = Territory.objects.create(
                company=company,
                name=data['name'],
                code=data['name'].upper().replace(' ', '_'),
                type=data['type'],
                countries=data.get('countries'),
                customer_types=data.get('customer_types'),
                currency='USD'
            )
            territories.append(territory)
        
        return territories

    def create_pipeline_stages(self, company):
        """Create pipeline stages"""
        stages = []
        stage_data = [
            {'name': 'Prospecting', 'probability': 10, 'stage_order': 1},
            {'name': 'Qualification', 'probability': 25, 'stage_order': 2},
            {'name': 'Proposal', 'probability': 50, 'stage_order': 3},
            {'name': 'Negotiation', 'probability': 75, 'stage_order': 4},
            {'name': 'Closed Won', 'probability': 100, 'stage_order': 5, 'is_closed': True, 'is_won': True},
            {'name': 'Closed Lost', 'probability': 0, 'stage_order': 6, 'is_closed': True, 'is_won': False},
        ]
        
        for data in stage_data:
            stage = PipelineStage.objects.create(
                company=company,
                name=data['name'],
                probability=data['probability'],
                stage_order=data['stage_order'],
                is_closed=data.get('is_closed', False),
                is_won=data.get('is_won', False),
                color=f'#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}'
            )
            stages.append(stage)
        
        return stages

    def create_product_categories(self, company):
        """Create product categories"""
        categories = []
        category_data = [
            'Software',
            'Hardware',
            'Services',
            'Consulting',
            'Support'
        ]
        
        for name in category_data:
            category = ProductCategory.objects.create(
                company=company,
                name=name,
                code=name.upper()
            )
            categories.append(category)
        
        return categories

    def create_products(self, company, categories):
        """Create sample products"""
        products = []
        product_data = [
            {'name': 'CRM Software', 'code': 'CRM-001', 'price': 99.99},
            {'name': 'Analytics Dashboard', 'code': 'ANAL-001', 'price': 199.99},
            {'name': 'Mobile App', 'code': 'MOB-001', 'price': 49.99},
            {'name': 'API Access', 'code': 'API-001', 'price': 299.99},
            {'name': 'Training Session', 'code': 'TRAIN-001', 'price': 150.00},
        ]
        
        for data in product_data:
            product = Product.objects.create(
                company=company,
                name=data['name'],
                product_code=data['code'],
                unit_price=data['price'],
                category=random.choice(categories),
                product_type='service',
                currency='USD'
            )
            products.append(product)
        
        return products

    def create_accounts(self, company, users, territories, count):
        """Create sample accounts"""
        accounts = []
        industries = ['Technology', 'Healthcare', 'Finance', 'Education', 'Manufacturing']
        types = ['Customer', 'Prospect', 'Partner', 'Competitor']
        
        for i in range(count):
            account = Account.objects.create(
                company=company,
                name=f'Account {i+1}',
                type=random.choice(types),
                industry=random.choice(industries),
                email=f'contact{i+1}@account{i+1}.com',
                phone=f'+1-555-{random.randint(1000, 9999)}',
                annual_revenue=random.randint(100000, 10000000),
                employee_count=random.randint(10, 1000),
                owner=random.choice(users),
                territory=random.choice(territories),
                created_by=random.choice(users)
            )
            accounts.append(account)
        
        return accounts

    def create_contacts(self, company, users, accounts, count):
        """Create sample contacts"""
        contacts = []
        titles = ['CEO', 'CTO', 'CFO', 'VP Sales', 'Director', 'Manager', 'Analyst']
        
        for i in range(count):
            contact = Contact.objects.create(
                company=company,
                first_name=f'Contact{i+1}',
                last_name='Johnson',
                email=f'contact{i+1}@example.com',
                phone=f'+1-555-{random.randint(1000, 9999)}',
                title=random.choice(titles),
                account=random.choice(accounts),
                owner=random.choice(users),
                created_by=random.choice(users)
            )
            contacts.append(contact)
        
        return contacts

    def create_leads(self, company, users, territories, count):
        """Create sample leads"""
        leads = []
        sources = ['Website', 'Referral', 'Cold Call', 'Email', 'Social Media']
        statuses = ['new', 'contacted', 'qualified', 'unqualified']
        
        for i in range(count):
            lead = Lead.objects.create(
                company=company,
                first_name=f'Lead{i+1}',
                last_name='Wilson',
                email=f'lead{i+1}@example.com',
                phone=f'+1-555-{random.randint(1000, 9999)}',
                company=f'Lead Company {i+1}',
                source=random.choice(sources),
                status=random.choice(statuses),
                rating=random.choice(['hot', 'warm', 'cold']),
                lead_score=random.randint(0, 100),
                owner=random.choice(users),
                territory=random.choice(territories),
                created_by=random.choice(users)
            )
            leads.append(lead)
        
        return leads

    def create_deals(self, company, users, accounts, contacts, stages, count):
        """Create sample deals"""
        deals = []
        
        for i in range(count):
            deal = Deal.objects.create(
                company=company,
                name=f'Deal {i+1}',
                amount=random.randint(1000, 100000),
                currency='USD',
                close_date=datetime.now() + timedelta(days=random.randint(1, 90)),
                stage=random.choice(stages),
                account=random.choice(accounts),
                contact=random.choice(contacts),
                owner=random.choice(users),
                lead_source=random.choice(['Website', 'Referral', 'Cold Call']),
                created_by=random.choice(users)
            )
            deals.append(deal)
        
        return deals

    def create_activities(self, company, users, accounts, contacts, leads, deals):
        """Create sample activities"""
        activities = []
        activity_types = ['call', 'email', 'meeting', 'note']
        subjects = [
            'Initial contact', 'Follow-up call', 'Product demo',
            'Proposal discussion', 'Contract review', 'Status update'
        ]
        
        for i in range(20):
            activity = Activity.objects.create(
                company=company,
                activity_type=random.choice(activity_types),
                subject=random.choice(subjects),
                description=f'Activity description {i+1}',
                activity_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                owner=random.choice(users),
                contact=random.choice(contacts),
                created_by=random.choice(users)
            )
            activities.append(activity)
        
        return activities

    def create_tasks(self, company, users, accounts, contacts, leads, deals):
        """Create sample tasks"""
        tasks = []
        titles = [
            'Follow up with client', 'Prepare proposal', 'Schedule meeting',
            'Update CRM', 'Send contract', 'Review documents'
        ]
        
        for i in range(15):
            task = Task.objects.create(
                company=company,
                title=random.choice(titles),
                description=f'Task description {i+1}',
                due_date=datetime.now() + timedelta(days=random.randint(1, 30)),
                priority=random.choice(['low', 'medium', 'high', 'urgent']),
                assigned_to=random.choice(users),
                created_by=random.choice(users)
            )
            tasks.append(task)
        
        return tasks
