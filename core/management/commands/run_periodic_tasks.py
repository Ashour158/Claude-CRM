# core/management/commands/run_periodic_tasks.py
# Management command to manually run Celery periodic tasks

from django.core.management.base import BaseCommand
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manually run Celery periodic tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            choices=[
                'all',
                'precompute_facets',
                'precompute_aggregates',
                'audit_maintenance',
                'warm_caches',
            ],
            default='all',
            help='Which task(s) to run',
        )

    def handle(self, *args, **options):
        task = options['task']
        
        self.stdout.write(self.style.SUCCESS(f'Running periodic task(s): {task}'))
        
        try:
            if task == 'all' or task == 'precompute_facets':
                self.run_precompute_facets()
            
            if task == 'all' or task == 'precompute_aggregates':
                self.run_precompute_aggregates()
            
            if task == 'all' or task == 'audit_maintenance':
                self.run_audit_maintenance()
            
            if task == 'all' or task == 'warm_caches':
                self.run_warm_caches()
            
            self.stdout.write(
                self.style.SUCCESS('Successfully executed periodic task(s)')
            )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error executing task(s): {str(e)}')
            )
            raise

    def run_precompute_facets(self):
        """Run the precompute_facets task"""
        self.stdout.write('Running precompute_facets task...')
        
        try:
            from analytics.tasks import precompute_facets_task
            result = precompute_facets_task()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Precompute facets completed: {len(result)} facets processed'
                )
            )
        except ImportError as e:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ Could not import precompute_facets_task: {e}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Precompute facets failed: {e}')
            )

    def run_precompute_aggregates(self):
        """Run the precompute_aggregates task"""
        self.stdout.write('Running precompute_aggregates task...')
        
        try:
            from analytics.tasks import precompute_aggregates_task
            result = precompute_aggregates_task()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Precompute aggregates completed: {len(result)} entities processed'
                )
            )
        except ImportError as e:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ Could not import precompute_aggregates_task: {e}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Precompute aggregates failed: {e}')
            )

    def run_audit_maintenance(self):
        """Run the audit_maintenance task"""
        self.stdout.write('Running audit_maintenance task...')
        
        try:
            from analytics.tasks import audit_maintenance_task
            result = audit_maintenance_task()
            
            if result.get('success', True):
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Audit maintenance completed: '
                        f'{len(result.get("partitions_created", []))} partitions created, '
                        f'{len(result.get("partitions_archived", []))} partitions archived'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Audit maintenance failed: {result.get("error", "Unknown error")}'
                    )
                )
        except ImportError as e:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ Could not import audit_maintenance_task: {e}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Audit maintenance failed: {e}')
            )

    def run_warm_caches(self):
        """Run the warm_caches task"""
        self.stdout.write('Running warm_caches task...')
        
        try:
            from analytics.tasks import warm_caches_task
            result = warm_caches_task()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Cache warming completed: {len(result)} caches warmed'
                )
            )
        except ImportError as e:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ Could not import warm_caches_task: {e}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Cache warming failed: {e}')
            )
