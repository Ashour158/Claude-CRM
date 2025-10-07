# compliance/management/commands/apply_policy.py
# CLI command to apply compliance policies

from django.core.management.base import BaseCommand, CommandError
from compliance.models import CompliancePolicy, PolicyAuditLog
from compliance.policy_engine import PolicyEngine
from django.utils import timezone
import json


class Command(BaseCommand):
    help = 'Apply compliance policy'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'policy_id',
            type=str,
            help='Policy ID to apply'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform dry-run impact analysis without applying'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
    
    def handle(self, *args, **options):
        policy_id = options['policy_id']
        dry_run = options['dry_run']
        
        try:
            policy = CompliancePolicy.objects.get(id=policy_id)
        except CompliancePolicy.DoesNotExist:
            raise CommandError(f"Policy not found: {policy_id}")
        
        engine = PolicyEngine()
        
        if dry_run:
            # Perform impact analysis
            self.stdout.write(self.style.WARNING(f"Performing dry-run for policy: {policy.name}"))
            
            impact = engine.analyze_impact(policy)
            
            if options['json']:
                self.stdout.write(json.dumps(impact, indent=2))
            else:
                self.stdout.write(self.style.SUCCESS("Impact Analysis:"))
                self.stdout.write(f"  Entities affected: {', '.join(impact['entities'])}")
                self.stdout.write(f"  Total records: {impact['total_records']}")
                
                if impact['affected_by_entity']:
                    self.stdout.write("  Records by entity:")
                    for entity, count in impact['affected_by_entity'].items():
                        self.stdout.write(f"    - {entity}: {count}")
                
                if impact['warnings']:
                    self.stdout.write(self.style.WARNING("  Warnings:"))
                    for warning in impact['warnings']:
                        self.stdout.write(self.style.WARNING(f"    - {warning}"))
        
        else:
            # Apply policy
            if policy.status == 'active' and policy.is_enforced:
                raise CommandError("Policy is already active and enforced")
            
            self.stdout.write(self.style.WARNING(f"Applying policy: {policy.name}"))
            
            result = engine.apply_policy(policy)
            
            if result['success']:
                # Update policy
                policy.status = 'active'
                policy.is_enforced = True
                policy.applied_at = timezone.now()
                policy.save()
                
                # Log application
                PolicyAuditLog.objects.create(
                    policy=policy,
                    company=policy.company,
                    action='applied',
                    action_details=result,
                    entities_affected=result.get('entities', []),
                    records_affected=result.get('total_records', 0)
                )
                
                if options['json']:
                    self.stdout.write(json.dumps(result, indent=2))
                else:
                    self.stdout.write(self.style.SUCCESS("✓ Policy applied successfully"))
                    self.stdout.write(f"  Entities processed: {', '.join(result['entities'])}")
                    self.stdout.write(f"  Total records affected: {result['total_records']}")
            
            else:
                if options['json']:
                    self.stdout.write(json.dumps(result, indent=2))
                else:
                    self.stdout.write(self.style.ERROR("✗ Policy application failed"))
                    for error in result.get('errors', []):
                        self.stdout.write(self.style.ERROR(f"  - {error}"))
