# compliance/management/commands/validate_policy.py
# CLI command to validate compliance policies

from django.core.management.base import BaseCommand, CommandError
from compliance.models import CompliancePolicy
from compliance.policy_validator import PolicyValidator
import yaml
import json


class Command(BaseCommand):
    help = 'Validate compliance policy configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--policy-id',
            type=str,
            help='Policy ID to validate'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='YAML file path to validate'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
    
    def handle(self, *args, **options):
        validator = PolicyValidator()
        
        # Validate from file
        if options['file']:
            self.stdout.write(self.style.SUCCESS(f"Validating policy from file: {options['file']}"))
            
            try:
                with open(options['file'], 'r') as f:
                    yaml_content = f.read()
                
                policy_config, error = validator.parse_yaml(yaml_content)
                
                if error:
                    raise CommandError(f"YAML parsing error: {error}")
                
                is_valid, errors = validator.validate(policy_config)
                
                if options['json']:
                    result = {
                        'valid': is_valid,
                        'errors': errors,
                        'policy_name': policy_config.get('name', 'Unknown')
                    }
                    self.stdout.write(json.dumps(result, indent=2))
                else:
                    if is_valid:
                        self.stdout.write(self.style.SUCCESS("✓ Policy is valid"))
                    else:
                        self.stdout.write(self.style.ERROR("✗ Policy validation failed:"))
                        for error in errors:
                            self.stdout.write(self.style.ERROR(f"  - {error}"))
            
            except FileNotFoundError:
                raise CommandError(f"File not found: {options['file']}")
            except Exception as e:
                raise CommandError(f"Validation error: {str(e)}")
        
        # Validate existing policy
        elif options['policy_id']:
            self.stdout.write(self.style.SUCCESS(f"Validating policy: {options['policy_id']}"))
            
            try:
                policy = CompliancePolicy.objects.get(id=options['policy_id'])
                
                is_valid, errors = validator.validate(policy.policy_config)
                
                if options['json']:
                    result = {
                        'valid': is_valid,
                        'errors': errors,
                        'policy_id': str(policy.id),
                        'policy_name': policy.name
                    }
                    self.stdout.write(json.dumps(result, indent=2))
                else:
                    self.stdout.write(f"Policy: {policy.name} (v{policy.version})")
                    
                    if is_valid:
                        self.stdout.write(self.style.SUCCESS("✓ Policy is valid"))
                    else:
                        self.stdout.write(self.style.ERROR("✗ Policy validation failed:"))
                        for error in errors:
                            self.stdout.write(self.style.ERROR(f"  - {error}"))
            
            except CompliancePolicy.DoesNotExist:
                raise CommandError(f"Policy not found: {options['policy_id']}")
        
        else:
            raise CommandError("Please provide either --policy-id or --file")
