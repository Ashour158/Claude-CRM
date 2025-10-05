# core/management/commands/restore_data.py
# Django management command for data restoration

import os
import json
import zipfile
from django.core.management.base import BaseCommand
from django.core import serializers
from django.db import transaction
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    help = 'Restore CRM data from backup files'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_path',
            type=str,
            help='Path to backup file or directory',
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing data before restore',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be restored without actually restoring',
        )

    def handle(self, *args, **options):
        backup_path = options['backup_path']
        
        if not os.path.exists(backup_path):
            self.stdout.write(
                self.style.ERROR(f'Backup path does not exist: {backup_path}')
            )
            return
        
        self.stdout.write(self.style.SUCCESS('Starting data restoration...'))
        
        # Handle compressed backup
        if backup_path.endswith('.zip'):
            self.restore_from_archive(backup_path, options)
        else:
            self.restore_from_directory(backup_path, options)

    def restore_from_archive(self, archive_path, options):
        """Restore from compressed archive"""
        self.stdout.write(f'Extracting archive: {archive_path}')
        
        # Create temporary directory
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract archive
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Find manifest file
            manifest_files = [f for f in os.listdir(temp_dir) if f.startswith('backup_manifest_')]
            if manifest_files:
                manifest_path = os.path.join(temp_dir, manifest_files[0])
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                self.stdout.write(f'Backup created: {manifest["timestamp"]}')
                self.stdout.write(f'Format: {manifest["format"]}')
                
                # Restore files
                for filename in manifest['files']:
                    file_path = os.path.join(temp_dir, filename)
                    if os.path.exists(file_path):
                        self.restore_file(file_path, options)
            else:
                # No manifest, try to restore all JSON files
                json_files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
                for filename in json_files:
                    file_path = os.path.join(temp_dir, filename)
                    self.restore_file(file_path, options)

    def restore_from_directory(self, directory_path, options):
        """Restore from directory"""
        self.stdout.write(f'Restoring from directory: {directory_path}')
        
        # Find all JSON files
        json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
        
        for filename in json_files:
            file_path = os.path.join(directory_path, filename)
            self.restore_file(file_path, options)

    def restore_file(self, file_path, options):
        """Restore data from a single file"""
        filename = os.path.basename(file_path)
        self.stdout.write(f'Restoring: {filename}')
        
        if options['dry_run']:
            self.stdout.write(f'[DRY RUN] Would restore: {filename}')
            return
        
        try:
            with open(file_path, 'r') as f:
                data = f.read()
            
            # Parse JSON data
            objects = json.loads(data)
            
            if not objects:
                self.stdout.write(f'No data in {filename}')
                return
            
            # Restore objects
            with transaction.atomic():
                for obj_data in objects:
                    try:
                        # Deserialize object
                        obj = serializers.deserialize('json', [obj_data])
                        for deserialized_obj in obj:
                            deserialized_obj.save()
                    except ValidationError as e:
                        self.stdout.write(
                            self.style.WARNING(f'Validation error in {filename}: {e}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'Error restoring object in {filename}: {e}')
                        )
            
            self.stdout.write(f'Successfully restored: {filename}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error restoring {filename}: {e}')
            )
