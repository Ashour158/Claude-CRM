# sharing/management/commands/seed_sharing_rules.py
# Management command to seed example sharing rules

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Company
from sharing.models import SharingRule, RecordShare
from crm.models import Lead

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed example sharing rules and record shares'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company-code',
            type=str,
            help='Company code to seed rules for (optional, will use first company if not provided)',
        )
    
    def handle(self, *args, **options):
        company_code = options.get('company_code')
        
        # Get or create company
        if company_code:
            try:
                company = Company.objects.get(code=company_code)
            except Company.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Company with code "{company_code}" not found')
                )
                return
        else:
            company = Company.objects.first()
            if not company:
                self.stdout.write(
                    self.style.ERROR('No companies found. Please create a company first.')
                )
                return
        
        self.stdout.write(f'Seeding sharing rules for company: {company.name}')
        
        # Create example sharing rule: All users can see qualified/converted leads
        rule1, created = SharingRule.objects.get_or_create(
            company=company,
            name='Qualified Leads Visibility',
            object_type='lead',
            defaults={
                'description': 'All users can view qualified or converted leads',
                'predicate': {
                    'field': 'status',
                    'operator': 'in',
                    'value': ['qualified', 'converted']
                },
                'access_level': 'read_only',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created sharing rule: {rule1.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'- Sharing rule already exists: {rule1.name}')
            )
        
        # Create another example rule: High-value deals (if deals exist)
        rule2, created = SharingRule.objects.get_or_create(
            company=company,
            name='High-Value Deals Visibility',
            object_type='deal',
            defaults={
                'description': 'All users can view high-value deals (amount >= 10000)',
                'predicate': {
                    'field': 'amount',
                    'operator': 'gte',
                    'value': 10000
                },
                'access_level': 'read_only',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created sharing rule: {rule2.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'- Sharing rule already exists: {rule2.name}')
            )
        
        # Create example explicit share (if there are users and leads)
        users = User.objects.all()[:2]
        leads = Lead.objects.filter(company=company)[:1]
        
        if len(users) >= 2 and leads.exists():
            user1, user2 = users[0], users[1]
            lead = leads[0]
            
            # Share lead owned by user1 with user2
            if hasattr(lead, 'owner') and lead.owner and lead.owner.id != user2.id:
                share, created = RecordShare.objects.get_or_create(
                    company=company,
                    object_type='lead',
                    object_id=lead.id,
                    user=user2,
                    defaults={
                        'access_level': 'read_only',
                        'reason': 'Example explicit share for demonstration',
                        'created_by': user1,
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Created explicit share: Lead {lead.id} shared with {user2.email}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'- Explicit share already exists: Lead {lead.id} -> {user2.email}'
                        )
                    )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '- Skipping explicit share creation (need at least 2 users and 1 lead)'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Sharing rules seeding completed!')
        )
        self.stdout.write(
            f'Summary:\n'
            f'  - Company: {company.name}\n'
            f'  - Total Sharing Rules: {SharingRule.objects.filter(company=company).count()}\n'
            f'  - Total Record Shares: {RecordShare.objects.filter(company=company).count()}'
        )
