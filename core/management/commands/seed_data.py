# core/management/commands/seed_data.py
# Django management command to seed initial data

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from core.models import Company, UserCompanyAccess
from crm.models import Account, Contact, Lead, Tag
from activities.models import Activity, Task, Event
from deals.models import Deal, PipelineStage
from products.models import Product, ProductCategory
from territories.models import Territory
import random
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with initial data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--companies',
            type=int,
            default=3,
            help='Number of companies to create',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of users to create per company',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))
        
        if options['clear']:
            self.clear_data()
        
        with transaction.atomic():
            # Create companies
            companies = self.create_companies(options['companies'])
            
            # Create users and company access
            users = self.create_users_and_access(companies, options['users'])
            
            # Create pipeline stages
            pipeline_stages = self.create_pipeline_stages(companies)
            
            # Create territories
            territories = self.create_territories(companies)
            
            # Create product categories and products
            product_categories = self.create_product_categories(companies)
            products = self.create_products(companies, product_categories)
            
            # Create accounts
            accounts = self.create_accounts(companies, territories)
            
            # Create contacts
            contacts = self.create_contacts(companies, accounts)
            
            # Create leads
            leads = self.create_leads(companies, territories)
            
            # Create deals
            deals = self.create_deals(companies, accounts, contacts, pipeline_stages)
            
            # Create activities
            self.create_activities(companies, users, accounts, contacts, leads, deals)
            
            # Create tasks
            self.create_tasks(companies, users)
            
            # Create events
            self.create_events(companies, users)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded data: {len(companies)} companies, '
                f'{len(users)} users, {len(accounts)} accounts, '
                f'{len(contacts)} contacts, {len(leads)} leads, '
                f'{len(deals)} deals'
            )
        )

    def clear_data(self):
        """Clear existing data"""
        self.stdout.write('Clearing existing data...')
        
        # Delete in reverse order of dependencies
        Activity.objects.all().delete()
        Task.objects.all().delete()
        Event.objects.all().delete()
        Deal.objects.all().delete()
        Lead.objects.all().delete()
        Contact.objects.all().delete()
        Account.objects.all().delete()
        Product.objects.all().delete()
        ProductCategory.objects.all().delete()
        Territory.objects.all().delete()
        PipelineStage.objects.all().delete()
        UserCompanyAccess.objects.all().delete()
        User.objects.all().delete()
        Company.objects.all().delete()

    def create_companies(self, count):
        """Create companies"""
        companies = []
        for i in range(count):
            company = Company.objects.create(
                name=f'Company {i+1}',
                domain=f'company{i+1}.com',
                address=f'{i+1} Business Street, City {i+1}',
                phone=f'+1-555-{i+1:03d}-0000',
                email=f'info@company{i+1}.com',
                is_active=True
            )
            companies.append(company)
        return companies

    def create_users_and_access(self, companies, users_per_company):
        """Create users and company access"""
        users = []
        roles = ['admin', 'manager', 'sales_rep', 'user']
        
        for company in companies:
            for i in range(users_per_company):
                user = User.objects.create_user(
                    email=f'user{i+1}@{company.domain}',
                    first_name=f'User{i+1}',
                    last_name='Test',
                    password='testpass123'
                )
                
                UserCompanyAccess.objects.create(
                    user=user,
                    company=company,
                    role=random.choice(roles),
                    is_active=True
                )
                users.append(user)
        return users

    def create_pipeline_stages(self, companies):
        """Create pipeline stages"""
        stages = []
        stage_names = [
            'Lead', 'Qualified', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost'
        ]
        
        for company in companies:
            for i, stage_name in enumerate(stage_names):
                stage = PipelineStage.objects.create(
                    name=stage_name,
                    description=f'{stage_name} stage in sales pipeline',
                    order=i,
                    is_active=True,
                    company=company
                )
                stages.append(stage)
        return stages

    def create_territories(self, companies):
        """Create territories"""
        territories = []
        territory_names = ['North', 'South', 'East', 'West', 'Central']
        
        for company in companies:
            for territory_name in territory_names:
                territory = Territory.objects.create(
                    name=f'{territory_name} Territory',
                    description=f'{territory_name} sales territory',
                    is_active=True,
                    company=company
                )
                territories.append(territory)
        return territories

    def create_product_categories(self, companies):
        """Create product categories"""
        categories = []
        category_names = ['Software', 'Hardware', 'Services', 'Consulting']
        
        for company in companies:
            for category_name in category_names:
                category = ProductCategory.objects.create(
                    name=category_name,
                    description=f'{category_name} products and services',
                    is_active=True,
                    company=company
                )
                categories.append(category)
        return categories

    def create_products(self, companies, categories):
        """Create products"""
        products = []
        product_names = [
            'CRM Software', 'Database System', 'Web Application', 'Mobile App',
            'Consulting Service', 'Support Package', 'Training Program'
        ]
        
        for company in companies:
            company_categories = [c for c in categories if c.company == company]
            for product_name in product_names:
                product = Product.objects.create(
                    name=product_name,
                    description=f'{product_name} for {company.name}',
                    sku=f'PROD-{random.randint(1000, 9999)}',
                    unit_price=random.uniform(100, 5000),
                    category=random.choice(company_categories),
                    is_active=True,
                    company=company
                )
                products.append(product)
        return products

    def create_accounts(self, companies, territories):
        """Create accounts"""
        accounts = []
        account_names = [
            'Acme Corporation', 'Tech Solutions Inc', 'Global Enterprises',
            'Innovation Labs', 'Future Systems', 'Digital Dynamics'
        ]
        
        for company in companies:
            company_territories = [t for t in territories if t.company == company]
            for account_name in account_names:
                account = Account.objects.create(
                    name=account_name,
                    account_type=random.choice(['Customer', 'Prospect', 'Partner']),
                    industry=random.choice(['Technology', 'Healthcare', 'Finance', 'Manufacturing']),
                    phone=f'+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    email=f'contact@{account_name.lower().replace(" ", "")}.com',
                    website=f'https://{account_name.lower().replace(" ", "")}.com',
                    territory=random.choice(company_territories),
                    company=company
                )
                accounts.append(account)
        return accounts

    def create_contacts(self, companies, accounts):
        """Create contacts"""
        contacts = []
        first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Lisa', 'Tom', 'Amy']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
        
        for company in companies:
            company_accounts = [a for a in accounts if a.company == company]
            for i in range(20):  # 20 contacts per company
                contact = Contact.objects.create(
                    first_name=random.choice(first_names),
                    last_name=random.choice(last_names),
                    email=f'contact{i+1}@{company.domain}',
                    phone=f'+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    title=random.choice(['Manager', 'Director', 'VP', 'CEO', 'CTO']),
                    account=random.choice(company_accounts) if company_accounts else None,
                    company=company
                )
                contacts.append(contact)
        return contacts

    def create_leads(self, companies, territories):
        """Create leads"""
        leads = []
        lead_sources = ['Website', 'Referral', 'Cold Call', 'Email', 'Social Media']
        lead_statuses = ['New', 'Contacted', 'Qualified', 'Unqualified']
        
        for company in companies:
            company_territories = [t for t in territories if t.company == company]
            for i in range(15):  # 15 leads per company
                lead = Lead.objects.create(
                    first_name=f'Lead{i+1}',
                    last_name='Prospect',
                    email=f'lead{i+1}@{company.domain}',
                    phone=f'+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    company_name=f'Prospect Company {i+1}',
                    lead_source=random.choice(lead_sources),
                    status=random.choice(lead_statuses),
                    territory=random.choice(company_territories) if company_territories else None,
                    company=company
                )
                leads.append(lead)
        return leads

    def create_deals(self, companies, accounts, contacts, pipeline_stages):
        """Create deals"""
        deals = []
        deal_names = [
            'Software License', 'Consulting Project', 'Support Contract',
            'Training Program', 'Custom Development', 'Integration Project'
        ]
        
        for company in companies:
            company_accounts = [a for a in accounts if a.company == company]
            company_contacts = [c for c in contacts if c.company == company]
            company_stages = [s for s in pipeline_stages if s.company == company]
            
            for i in range(10):  # 10 deals per company
                deal = Deal.objects.create(
                    name=random.choice(deal_names),
                    account=random.choice(company_accounts) if company_accounts else None,
                    contact=random.choice(company_contacts) if company_contacts else None,
                    amount=random.uniform(1000, 100000),
                    stage=random.choice(company_stages) if company_stages else None,
                    expected_close_date=datetime.now() + timedelta(days=random.randint(30, 180)),
                    probability=random.randint(10, 90),
                    status=random.choice(['Open', 'Won', 'Lost']),
                    company=company
                )
                deals.append(deal)
        return deals

    def create_activities(self, companies, users, accounts, contacts, leads, deals):
        """Create activities"""
        activity_types = ['Call', 'Email', 'Meeting', 'Demo', 'Follow-up']
        
        for company in companies:
            company_users = [u for u in users if any(uca.company == company for uca in u.usercompanyaccess_set.all())]
            company_accounts = [a for a in accounts if a.company == company]
            company_contacts = [c for c in contacts if c.company == company]
            company_leads = [l for l in leads if l.company == company]
            company_deals = [d for d in deals if d.company == company]
            
            for i in range(30):  # 30 activities per company
                activity = Activity.objects.create(
                    subject=f'Activity {i+1}',
                    activity_type=random.choice(activity_types),
                    description=f'Activity description for {random.choice(activity_types)}',
                    due_date=datetime.now() + timedelta(days=random.randint(1, 30)),
                    status=random.choice(['Not Started', 'In Progress', 'Completed']),
                    owner=random.choice(company_users) if company_users else None,
                    account=random.choice(company_accounts) if company_accounts else None,
                    contact=random.choice(company_contacts) if company_contacts else None,
                    lead=random.choice(company_leads) if company_leads else None,
                    deal=random.choice(company_deals) if company_deals else None,
                    company=company
                )

    def create_tasks(self, companies, users):
        """Create tasks"""
        task_names = [
            'Follow up with client', 'Prepare proposal', 'Schedule meeting',
            'Send contract', 'Update CRM', 'Research prospect'
        ]
        
        for company in companies:
            company_users = [u for u in users if any(uca.company == company for uca in u.usercompanyaccess_set.all())]
            
            for i in range(20):  # 20 tasks per company
                task = Task.objects.create(
                    title=random.choice(task_names),
                    description=f'Task description for {random.choice(task_names)}',
                    due_date=datetime.now() + timedelta(days=random.randint(1, 14)),
                    status=random.choice(['Not Started', 'In Progress', 'Completed']),
                    priority=random.choice(['Low', 'Medium', 'High']),
                    owner=random.choice(company_users) if company_users else None,
                    company=company
                )

    def create_events(self, companies, users):
        """Create events"""
        event_names = [
            'Client Meeting', 'Product Demo', 'Team Meeting', 'Training Session',
            'Conference Call', 'Workshop', 'Webinar'
        ]
        
        for company in companies:
            company_users = [u for u in users if any(uca.company == company for uca in u.usercompanyaccess_set.all())]
            
            for i in range(15):  # 15 events per company
                start_date = datetime.now() + timedelta(days=random.randint(1, 30))
                event = Event.objects.create(
                    title=random.choice(event_names),
                    description=f'Event description for {random.choice(event_names)}',
                    start_date=start_date,
                    end_date=start_date + timedelta(hours=random.randint(1, 4)),
                    location=f'Location {i+1}',
                    owner=random.choice(company_users) if company_users else None,
                    company=company
                )
