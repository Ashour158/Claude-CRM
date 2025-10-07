# compliance/management/commands/run_access_review.py
# CLI command to run access reviews

from django.core.management.base import BaseCommand, CommandError
from compliance.access_review import AccessReviewEngine
from core.models import Company
import json


class Command(BaseCommand):
    help = 'Run automated access review'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=str,
            help='Company ID to review (optional, runs for all if not specified)'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
    
    def handle(self, *args, **options):
        engine = AccessReviewEngine()
        
        # Get companies to review
        if options['company_id']:
            try:
                companies = [Company.objects.get(id=options['company_id'])]
            except Company.DoesNotExist:
                raise CommandError(f"Company not found: {options['company_id']}")
        else:
            companies = Company.objects.filter(is_active=True)
        
        results = []
        
        for company in companies:
            self.stdout.write(self.style.SUCCESS(f"Running access review for: {company.name}"))
            
            try:
                # Create and run review
                review = engine.create_review(company)
                result = engine.run_review(review)
                
                results.append({
                    'company_id': str(company.id),
                    'company_name': company.name,
                    'review_id': review.review_id,
                    'result': result
                })
                
                if not options['json']:
                    self.stdout.write(f"  Review ID: {review.review_id}")
                    self.stdout.write(f"  Total users reviewed: {result['total_users']}")
                    self.stdout.write(f"  Stale access found: {result['stale_access_found']}")
                    
                    if result['stale_access_found'] > 0:
                        self.stdout.write(self.style.WARNING("  Stale access details:"))
                        for detail in result.get('details', []):
                            self.stdout.write(self.style.WARNING(
                                f"    - {detail['user']}: {detail['days_inactive']} days inactive"
                            ))
            
            except Exception as e:
                if not options['json']:
                    self.stdout.write(self.style.ERROR(f"  Error: {str(e)}"))
                
                results.append({
                    'company_id': str(company.id),
                    'company_name': company.name,
                    'error': str(e)
                })
        
        if options['json']:
            self.stdout.write(json.dumps(results, indent=2))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nCompleted access reviews for {len(companies)} company(ies)"))
