# core/management/commands/search_index.py
# Management command for search index operations

from django.core.management.base import BaseCommand
from core.search import SearchService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage search indexes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['rebuild', 'health', 'info'],
            help='Action to perform: rebuild, health, or info'
        )
        parser.add_argument(
            '--backend',
            type=str,
            default=None,
            help='Search backend to use (postgres or external)'
        )
        parser.add_argument(
            '--models',
            type=str,
            nargs='+',
            help='Models to rebuild (Account, Contact, Lead, Deal)'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        backend_name = options.get('backend')
        models = options.get('models')
        
        # Initialize search service
        if backend_name:
            search_service = SearchService(backend_name=backend_name)
        else:
            search_service = SearchService()
        
        self.stdout.write(f"Using backend: {search_service.backend_name}")
        
        if action == 'rebuild':
            self.rebuild_index(search_service, models)
        elif action == 'health':
            self.check_health(search_service)
        elif action == 'info':
            self.show_info(search_service)
    
    def rebuild_index(self, search_service, models=None):
        """Rebuild search indexes"""
        self.stdout.write(self.style.WARNING(
            f'Rebuilding search indexes for: {models or "all models"}...'
        ))
        
        success = search_service.rebuild_index(models)
        
        if success:
            self.stdout.write(self.style.SUCCESS('✓ Index rebuild completed'))
        else:
            self.stdout.write(self.style.ERROR('✗ Index rebuild failed'))
    
    def check_health(self, search_service):
        """Check search backend health"""
        self.stdout.write('Checking search backend health...')
        
        health = search_service.health_check()
        
        self.stdout.write(f"\nService: {health.get('service')}")
        self.stdout.write(f"Backend: {health.get('backend')}")
        self.stdout.write(f"Status: {health.get('status')}")
        
        if 'details' in health:
            self.stdout.write("\nDetails:")
            for key, value in health['details'].items():
                self.stdout.write(f"  {key}: {value}")
        
        if health.get('status') == 'healthy':
            self.stdout.write(self.style.SUCCESS('\n✓ Backend is healthy'))
        else:
            self.stdout.write(self.style.ERROR('\n✗ Backend is unhealthy'))
            if 'error' in health:
                self.stdout.write(f"Error: {health['error']}")
    
    def show_info(self, search_service):
        """Show search service information"""
        self.stdout.write('Search Service Information:')
        
        info = search_service.get_backend_info()
        
        self.stdout.write(f"\nCurrent Backend: {info['name']}")
        self.stdout.write(f"Backend Class: {info['class']}")
        self.stdout.write(f"\nAvailable Backends:")
        for backend in info['available_backends']:
            prefix = '→' if backend == info['name'] else ' '
            self.stdout.write(f"  {prefix} {backend}")
        
        # Show configuration
        config = search_service.config
        self.stdout.write(f"\nConfiguration:")
        self.stdout.write(f"  GDPR Masking: {config.get('gdpr', {}).get('mask_pii', False)}")
        self.stdout.write(f"  Fuzzy Search: Enabled")
        
        # Show scoring weights
        scoring = config.get('scoring', {})
        field_weights = scoring.get('field_weights', {})
        if field_weights:
            self.stdout.write(f"\nField Weights:")
            for field, weight in sorted(field_weights.items(), key=lambda x: x[1], reverse=True):
                self.stdout.write(f"  {field}: {weight}")
