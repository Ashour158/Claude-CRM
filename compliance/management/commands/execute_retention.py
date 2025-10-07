# compliance/management/commands/execute_retention.py
# CLI command to execute retention policies

from django.core.management.base import BaseCommand, CommandError
from compliance.models import RetentionPolicy
from compliance.retention_engine import RetentionEngine, RetentionScheduler
import json


class Command(BaseCommand):
    help = 'Execute data retention policies'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--policy-id',
            type=str,
            help='Specific policy ID to execute'
        )
        parser.add_argument(
            '--all-scheduled',
            action='store_true',
            help='Execute all scheduled policies'
        )
        parser.add_argument(
            '--preview',
            action='store_true',
            help='Preview records that will be affected'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
    
    def handle(self, *args, **options):
        engine = RetentionEngine()
        
        if options['policy_id']:
            # Execute specific policy
            try:
                policy = RetentionPolicy.objects.get(id=options['policy_id'])
            except RetentionPolicy.DoesNotExist:
                raise CommandError(f"Policy not found: {options['policy_id']}")
            
            if options['preview']:
                # Preview mode
                self.stdout.write(self.style.WARNING(f"Previewing retention policy: {policy.name}"))
                
                records = engine.get_records_for_deletion(policy)
                
                if records is None:
                    raise CommandError(f"Model not found: {policy.entity_type}")
                
                count = records.count()
                
                if options['json']:
                    result = {
                        'policy_id': str(policy.id),
                        'policy_name': policy.name,
                        'entity_type': policy.entity_type,
                        'records_to_delete': count,
                        'deletion_method': policy.deletion_method
                    }
                    self.stdout.write(json.dumps(result, indent=2))
                else:
                    self.stdout.write(f"  Entity: {policy.entity_type}")
                    self.stdout.write(f"  Records to delete: {count}")
                    self.stdout.write(f"  Deletion method: {policy.deletion_method}")
                    self.stdout.write(f"  Retention period: {policy.retention_days} days")
            
            else:
                # Execute policy
                self.stdout.write(self.style.WARNING(f"Executing retention policy: {policy.name}"))
                
                result = engine.execute_policy(policy)
                
                if options['json']:
                    self.stdout.write(json.dumps(result, indent=2))
                else:
                    if result['success']:
                        self.stdout.write(self.style.SUCCESS("✓ Policy executed successfully"))
                        self.stdout.write(f"  Records processed: {result['records_processed']}")
                        self.stdout.write(f"  Records deleted: {result['records_deleted']}")
                        self.stdout.write(f"  Records archived: {result['records_archived']}")
                    else:
                        self.stdout.write(self.style.ERROR("✗ Policy execution failed"))
                        for error in result['errors']:
                            self.stdout.write(self.style.ERROR(f"  - {error}"))
        
        elif options['all_scheduled']:
            # Execute all scheduled policies
            self.stdout.write(self.style.SUCCESS("Executing all scheduled retention policies"))
            
            results = RetentionScheduler.execute_scheduled_policies()
            
            if options['json']:
                self.stdout.write(json.dumps(results, indent=2))
            else:
                self.stdout.write(f"Executed {len(results)} policy(ies):")
                
                for result in results:
                    if 'error' in result:
                        self.stdout.write(self.style.ERROR(
                            f"  ✗ {result['policy_name']}: {result['error']}"
                        ))
                    else:
                        policy_result = result['result']
                        self.stdout.write(self.style.SUCCESS(
                            f"  ✓ {result['policy_name']}: "
                            f"{policy_result['records_deleted']} deleted, "
                            f"{policy_result['records_archived']} archived"
                        ))
        
        else:
            raise CommandError("Please provide either --policy-id or --all-scheduled")
