# core/management/commands/backup_data.py
# Django management command for data backup

import os
import json
import zipfile
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import serializers
from django.db import connection
from core.models import Company, User, UserCompanyAccess, AuditLog
from crm.models import Account, Contact, Lead
from activities.models import Activity, Task, Event
from deals.models import Deal, PipelineStage
from products.models import Product, ProductCategory
from territories.models import Territory

class Command(BaseCommand):
    help = 'Backup CRM data to JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Output directory for backup files',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'xml'],
            default='json',
            help='Backup format',
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress backup files',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data backup...'))
        
        # Create output directory
        output_dir = options['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Define models to backup
        models_to_backup = [
            (Company, 'companies'),
            (User, 'users'),
            (UserCompanyAccess, 'user_company_access'),
            (Account, 'accounts'),
            (Contact, 'contacts'),
            (Lead, 'leads'),
            (Activity, 'activities'),
            (Task, 'tasks'),
            (Event, 'events'),
            (Deal, 'deals'),
            (PipelineStage, 'pipeline_stages'),
            (Product, 'products'),
            (ProductCategory, 'product_categories'),
            (Territory, 'territories'),
            (AuditLog, 'audit_logs'),
        ]
        
        backup_files = []
        
        # Backup each model
        for model, filename in models_to_backup:
            try:
                # Get all objects
                objects = model.objects.all()
                
                # Serialize data
                if options['format'] == 'json':
                    data = serializers.serialize('json', objects)
                    file_extension = 'json'
                else:
                    data = serializers.serialize('xml', objects)
                    file_extension = 'xml'
                
                # Write to file
                backup_filename = f"{filename}_{timestamp}.{file_extension}"
                backup_path = os.path.join(output_dir, backup_filename)
                
                with open(backup_path, 'w') as f:
                    f.write(data)
                
                backup_files.append(backup_path)
                
                self.stdout.write(f'Backed up {model.__name__}: {len(objects)} records')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error backing up {model.__name__}: {e}')
                )
        
        # Create compressed archive if requested
        if options['compress']:
            archive_name = f"crm_backup_{timestamp}.zip"
            archive_path = os.path.join(output_dir, archive_name)
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for backup_file in backup_files:
                    zipf.write(backup_file, os.path.basename(backup_file))
                    os.remove(backup_file)  # Remove individual files after archiving
            
            self.stdout.write(
                self.style.SUCCESS(f'Created compressed backup: {archive_path}')
            )
        
        # Create backup manifest
        manifest = {
            'timestamp': timestamp,
            'format': options['format'],
            'compressed': options['compress'],
            'files': [os.path.basename(f) for f in backup_files],
            'database': settings.DATABASES['default']['NAME'],
            'django_version': settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'Unknown'
        }
        
        manifest_path = os.path.join(output_dir, f"backup_manifest_{timestamp}.json")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Backup completed successfully. Files saved to: {output_dir}'
            )
        )
