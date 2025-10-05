# core/backup_recovery.py
# Comprehensive backup and recovery system

import os
import json
import zipfile
import shutil
import subprocess
from datetime import datetime, timedelta
from django.core.management import call_command
from django.conf import settings
from django.db import connection
from django.core import serializers
from django.core.management.base import BaseCommand
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BackupManager:
    """Centralized backup management"""
    
    def __init__(self, backup_dir=None, retention_days=30):
        self.backup_dir = backup_dir or os.path.join(settings.BASE_DIR, 'backups')
        self.retention_days = retention_days
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """Ensure backup directory exists"""
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, backup_type='full', compress=True):
        """Create system backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"crm_backup_{backup_type}_{timestamp}"
        
        if backup_type == 'full':
            return self.create_full_backup(backup_name, compress)
        elif backup_type == 'database':
            return self.create_database_backup(backup_name, compress)
        elif backup_type == 'media':
            return self.create_media_backup(backup_name, compress)
        elif backup_type == 'code':
            return self.create_code_backup(backup_name, compress)
        else:
            raise ValueError(f"Unknown backup type: {backup_type}")
    
    def create_full_backup(self, backup_name, compress=True):
        """Create full system backup"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        os.makedirs(backup_path, exist_ok=True)
        
        try:
            # Backup database
            db_backup = self.backup_database(backup_path)
            
            # Backup media files
            media_backup = self.backup_media_files(backup_path)
            
            # Backup code
            code_backup = self.backup_code(backup_path)
            
            # Backup configuration
            config_backup = self.backup_configuration(backup_path)
            
            # Create manifest
            manifest = {
                'backup_name': backup_name,
                'backup_type': 'full',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'database': db_backup,
                    'media': media_backup,
                    'code': code_backup,
                    'configuration': config_backup
                },
                'compression': compress
            }
            
            manifest_path = os.path.join(backup_path, 'manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Compress if requested
            if compress:
                archive_path = f"{backup_path}.zip"
                self.compress_backup(backup_path, archive_path)
                shutil.rmtree(backup_path)
                return archive_path
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            raise
    
    def create_database_backup(self, backup_name, compress=True):
        """Create database backup"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        os.makedirs(backup_path, exist_ok=True)
        
        try:
            # Backup database
            db_backup = self.backup_database(backup_path)
            
            # Create manifest
            manifest = {
                'backup_name': backup_name,
                'backup_type': 'database',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'database': db_backup
                },
                'compression': compress
            }
            
            manifest_path = os.path.join(backup_path, 'manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Compress if requested
            if compress:
                archive_path = f"{backup_path}.zip"
                self.compress_backup(backup_path, archive_path)
                shutil.rmtree(backup_path)
                return archive_path
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    def create_media_backup(self, backup_name, compress=True):
        """Create media files backup"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        os.makedirs(backup_path, exist_ok=True)
        
        try:
            # Backup media files
            media_backup = self.backup_media_files(backup_path)
            
            # Create manifest
            manifest = {
                'backup_name': backup_name,
                'backup_type': 'media',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'media': media_backup
                },
                'compression': compress
            }
            
            manifest_path = os.path.join(backup_path, 'manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Compress if requested
            if compress:
                archive_path = f"{backup_path}.zip"
                self.compress_backup(backup_path, archive_path)
                shutil.rmtree(backup_path)
                return archive_path
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Media backup failed: {e}")
            raise
    
    def create_code_backup(self, backup_name, compress=True):
        """Create code backup"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        os.makedirs(backup_path, exist_ok=True)
        
        try:
            # Backup code
            code_backup = self.backup_code(backup_path)
            
            # Create manifest
            manifest = {
                'backup_name': backup_name,
                'backup_type': 'code',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'code': code_backup
                },
                'compression': compress
            }
            
            manifest_path = os.path.join(backup_path, 'manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Compress if requested
            if compress:
                archive_path = f"{backup_path}.zip"
                self.compress_backup(backup_path, archive_path)
                shutil.rmtree(backup_path)
                return archive_path
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Code backup failed: {e}")
            raise
    
    def backup_database(self, backup_path):
        """Backup database"""
        db_backup_path = os.path.join(backup_path, 'database')
        os.makedirs(db_backup_path, exist_ok=True)
        
        # Get database configuration
        db_config = settings.DATABASES['default']
        
        if db_config['ENGINE'] == 'django.db.backends.postgresql':
            return self.backup_postgresql(db_config, db_backup_path)
        elif db_config['ENGINE'] == 'django.db.backends.mysql':
            return self.backup_mysql(db_config, db_backup_path)
        else:
            # Use Django's dumpdata for other databases
            return self.backup_django_data(db_backup_path)
    
    def backup_postgresql(self, db_config, backup_path):
        """Backup PostgreSQL database"""
        try:
            # Create pg_dump command
            dump_file = os.path.join(backup_path, 'database.sql')
            cmd = [
                'pg_dump',
                '-h', db_config.get('HOST', 'localhost'),
                '-p', str(db_config.get('PORT', 5432)),
                '-U', db_config.get('USER', 'postgres'),
                '-d', db_config.get('NAME'),
                '-f', dump_file
            ]
            
            # Set password if provided
            env = os.environ.copy()
            if db_config.get('PASSWORD'):
                env['PGPASSWORD'] = db_config['PASSWORD']
            
            # Run pg_dump
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            return {
                'type': 'postgresql',
                'file': dump_file,
                'size': os.path.getsize(dump_file)
            }
            
        except Exception as e:
            logger.error(f"PostgreSQL backup failed: {e}")
            raise
    
    def backup_mysql(self, db_config, backup_path):
        """Backup MySQL database"""
        try:
            # Create mysqldump command
            dump_file = os.path.join(backup_path, 'database.sql')
            cmd = [
                'mysqldump',
                '-h', db_config.get('HOST', 'localhost'),
                '-P', str(db_config.get('PORT', 3306)),
                '-u', db_config.get('USER', 'root'),
                f'-p{db_config.get("PASSWORD", "")}',
                db_config.get('NAME')
            ]
            
            # Run mysqldump
            with open(dump_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"mysqldump failed: {result.stderr}")
            
            return {
                'type': 'mysql',
                'file': dump_file,
                'size': os.path.getsize(dump_file)
            }
            
        except Exception as e:
            logger.error(f"MySQL backup failed: {e}")
            raise
    
    def backup_django_data(self, backup_path):
        """Backup Django data using dumpdata"""
        try:
            # Get all models
            from django.apps import apps
            models = []
            for app_config in apps.get_app_configs():
                models.extend(app_config.get_models())
            
            # Create data backup
            data_file = os.path.join(backup_path, 'data.json')
            with open(data_file, 'w') as f:
                call_command('dumpdata', '--natural-foreign', '--natural-primary', stdout=f)
            
            return {
                'type': 'django',
                'file': data_file,
                'size': os.path.getsize(data_file)
            }
            
        except Exception as e:
            logger.error(f"Django data backup failed: {e}")
            raise
    
    def backup_media_files(self, backup_path):
        """Backup media files"""
        media_path = os.path.join(backup_path, 'media')
        os.makedirs(media_path, exist_ok=True)
        
        # Get media root
        media_root = settings.MEDIA_ROOT
        
        if os.path.exists(media_root):
            # Copy media files
            shutil.copytree(media_root, media_path, dirs_exist_ok=True)
            
            return {
                'type': 'media',
                'path': media_path,
                'size': self.get_directory_size(media_path)
            }
        else:
            return {
                'type': 'media',
                'path': media_path,
                'size': 0
            }
    
    def backup_code(self, backup_path):
        """Backup code files"""
        code_path = os.path.join(backup_path, 'code')
        os.makedirs(code_path, exist_ok=True)
        
        # Copy code files (exclude certain directories)
        exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env'}
        exclude_files = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe'}
        
        for root, dirs, files in os.walk(settings.BASE_DIR):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in exclude_files):
                    continue
                
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, settings.BASE_DIR)
                dst_path = os.path.join(code_path, rel_path)
                
                # Create directory if needed
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                
                # Copy file
                shutil.copy2(src_path, dst_path)
        
        return {
            'type': 'code',
            'path': code_path,
            'size': self.get_directory_size(code_path)
        }
    
    def backup_configuration(self, backup_path):
        """Backup configuration files"""
        config_path = os.path.join(backup_path, 'config')
        os.makedirs(config_path, exist_ok=True)
        
        # Backup environment files
        env_files = ['.env', '.env.production', 'env.production.example']
        for env_file in env_files:
            src_path = os.path.join(settings.BASE_DIR, env_file)
            if os.path.exists(src_path):
                shutil.copy2(src_path, config_path)
        
        # Backup Docker files
        docker_files = ['Dockerfile', 'docker-compose.yml', 'docker-compose.prod.yml']
        for docker_file in docker_files:
            src_path = os.path.join(settings.BASE_DIR, docker_file)
            if os.path.exists(src_path):
                shutil.copy2(src_path, config_path)
        
        # Backup requirements
        req_files = ['requirements.txt', 'requirements-dev.txt']
        for req_file in req_files:
            src_path = os.path.join(settings.BASE_DIR, req_file)
            if os.path.exists(src_path):
                shutil.copy2(src_path, config_path)
        
        return {
            'type': 'configuration',
            'path': config_path,
            'size': self.get_directory_size(config_path)
        }
    
    def compress_backup(self, source_path, archive_path):
        """Compress backup directory"""
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_path)
                    zipf.write(file_path, arcname)
    
    def get_directory_size(self, directory):
        """Get directory size in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    
    def list_backups(self):
        """List available backups"""
        backups = []
        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            if os.path.isfile(item_path) and item.endswith('.zip'):
                stat = os.stat(item_path)
                backups.append({
                    'name': item,
                    'path': item_path,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
            elif os.path.isdir(item_path):
                manifest_path = os.path.join(item_path, 'manifest.json')
                if os.path.exists(manifest_path):
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    backups.append({
                        'name': item,
                        'path': item_path,
                        'size': self.get_directory_size(item_path),
                        'created': manifest.get('timestamp'),
                        'type': manifest.get('backup_type')
                    })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for backup in self.list_backups():
            backup_date = datetime.fromisoformat(backup['created'].replace('Z', '+00:00'))
            if backup_date < cutoff_date:
                try:
                    if os.path.isfile(backup['path']):
                        os.remove(backup['path'])
                    elif os.path.isdir(backup['path']):
                        shutil.rmtree(backup['path'])
                    
                    logger.info(f"Deleted old backup: {backup['name']}")
                except Exception as e:
                    logger.error(f"Failed to delete backup {backup['name']}: {e}")

class RecoveryManager:
    """Centralized recovery management"""
    
    def __init__(self, backup_dir=None):
        self.backup_dir = backup_dir or os.path.join(settings.BASE_DIR, 'backups')
    
    def restore_backup(self, backup_path, restore_type='full'):
        """Restore from backup"""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        
        # Extract if compressed
        if backup_path.endswith('.zip'):
            extract_path = backup_path.replace('.zip', '_extracted')
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(extract_path)
            backup_path = extract_path
        
        # Read manifest
        manifest_path = os.path.join(backup_path, 'manifest.json')
        if not os.path.exists(manifest_path):
            raise FileNotFoundError("Backup manifest not found")
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        try:
            if restore_type == 'full' or restore_type == 'database':
                self.restore_database(backup_path, manifest)
            
            if restore_type == 'full' or restore_type == 'media':
                self.restore_media_files(backup_path, manifest)
            
            if restore_type == 'full' or restore_type == 'code':
                self.restore_code(backup_path, manifest)
            
            if restore_type == 'full' or restore_type == 'configuration':
                self.restore_configuration(backup_path, manifest)
            
            logger.info(f"Successfully restored backup: {manifest['backup_name']}")
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise
    
    def restore_database(self, backup_path, manifest):
        """Restore database from backup"""
        db_component = manifest['components'].get('database')
        if not db_component:
            return
        
        db_file = db_component['file']
        if not os.path.exists(db_file):
            raise FileNotFoundError(f"Database backup file not found: {db_file}")
        
        # Get database configuration
        db_config = settings.DATABASES['default']
        
        if db_component['type'] == 'postgresql':
            self.restore_postgresql(db_config, db_file)
        elif db_component['type'] == 'mysql':
            self.restore_mysql(db_config, db_file)
        else:
            self.restore_django_data(db_file)
    
    def restore_postgresql(self, db_config, db_file):
        """Restore PostgreSQL database"""
        try:
            cmd = [
                'psql',
                '-h', db_config.get('HOST', 'localhost'),
                '-p', str(db_config.get('PORT', 5432)),
                '-U', db_config.get('USER', 'postgres'),
                '-d', db_config.get('NAME'),
                '-f', db_file
            ]
            
            env = os.environ.copy()
            if db_config.get('PASSWORD'):
                env['PGPASSWORD'] = db_config['PASSWORD']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"psql restore failed: {result.stderr}")
            
        except Exception as e:
            logger.error(f"PostgreSQL restore failed: {e}")
            raise
    
    def restore_mysql(self, db_config, db_file):
        """Restore MySQL database"""
        try:
            cmd = [
                'mysql',
                '-h', db_config.get('HOST', 'localhost'),
                '-P', str(db_config.get('PORT', 3306)),
                '-u', db_config.get('USER', 'root'),
                f'-p{db_config.get("PASSWORD", "")}',
                db_config.get('NAME')
            ]
            
            with open(db_file, 'r') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"mysql restore failed: {result.stderr}")
            
        except Exception as e:
            logger.error(f"MySQL restore failed: {e}")
            raise
    
    def restore_django_data(self, data_file):
        """Restore Django data using loaddata"""
        try:
            call_command('loaddata', data_file)
        except Exception as e:
            logger.error(f"Django data restore failed: {e}")
            raise
    
    def restore_media_files(self, backup_path, manifest):
        """Restore media files from backup"""
        media_component = manifest['components'].get('media')
        if not media_component:
            return
        
        media_path = media_component['path']
        if not os.path.exists(media_path):
            return
        
        # Get media root
        media_root = settings.MEDIA_ROOT
        
        # Create media root if it doesn't exist
        os.makedirs(media_root, exist_ok=True)
        
        # Copy media files
        for root, dirs, files in os.walk(media_path):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, media_path)
                dst_path = os.path.join(media_root, rel_path)
                
                # Create directory if needed
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                
                # Copy file
                shutil.copy2(src_path, dst_path)
    
    def restore_code(self, backup_path, manifest):
        """Restore code from backup"""
        code_component = manifest['components'].get('code')
        if not code_component:
            return
        
        code_path = code_component['path']
        if not os.path.exists(code_path):
            return
        
        # Copy code files
        for root, dirs, files in os.walk(code_path):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, code_path)
                dst_path = os.path.join(settings.BASE_DIR, rel_path)
                
                # Create directory if needed
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                
                # Copy file
                shutil.copy2(src_path, dst_path)
    
    def restore_configuration(self, backup_path, manifest):
        """Restore configuration from backup"""
        config_component = manifest['components'].get('configuration')
        if not config_component:
            return
        
        config_path = config_component['path']
        if not os.path.exists(config_path):
            return
        
        # Copy configuration files
        for root, dirs, files in os.walk(config_path):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, config_path)
                dst_path = os.path.join(settings.BASE_DIR, rel_path)
                
                # Create directory if needed
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                
                # Copy file
                shutil.copy2(src_path, dst_path)

class CloudBackupManager:
    """Cloud backup management"""
    
    def __init__(self, provider='aws', bucket_name=None, region=None):
        self.provider = provider
        self.bucket_name = bucket_name
        self.region = region
        
        if provider == 'aws':
            self.s3_client = boto3.client('s3', region_name=region)
        elif provider == 'gcp':
            # Initialize GCP client
            pass
        elif provider == 'azure':
            # Initialize Azure client
            pass
    
    def upload_backup(self, backup_path, remote_path=None):
        """Upload backup to cloud storage"""
        if self.provider == 'aws':
            return self.upload_to_s3(backup_path, remote_path)
        elif self.provider == 'gcp':
            return self.upload_to_gcp(backup_path, remote_path)
        elif self.provider == 'azure':
            return self.upload_to_azure(backup_path, remote_path)
    
    def upload_to_s3(self, backup_path, remote_path=None):
        """Upload backup to S3"""
        try:
            if not remote_path:
                remote_path = os.path.basename(backup_path)
            
            self.s3_client.upload_file(backup_path, self.bucket_name, remote_path)
            
            logger.info(f"Uploaded backup to S3: {remote_path}")
            return f"s3://{self.bucket_name}/{remote_path}"
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
    def download_backup(self, remote_path, local_path):
        """Download backup from cloud storage"""
        if self.provider == 'aws':
            return self.download_from_s3(remote_path, local_path)
        elif self.provider == 'gcp':
            return self.download_from_gcp(remote_path, local_path)
        elif self.provider == 'azure':
            return self.download_from_azure(remote_path, local_path)
    
    def download_from_s3(self, remote_path, local_path):
        """Download backup from S3"""
        try:
            self.s3_client.download_file(self.bucket_name, remote_path, local_path)
            
            logger.info(f"Downloaded backup from S3: {remote_path}")
            return local_path
            
        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            raise
    
    def list_cloud_backups(self):
        """List backups in cloud storage"""
        if self.provider == 'aws':
            return self.list_s3_backups()
        elif self.provider == 'gcp':
            return self.list_gcp_backups()
        elif self.provider == 'azure':
            return self.list_azure_backups()
    
    def list_s3_backups(self):
        """List S3 backups"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            backups = []
            for obj in response.get('Contents', []):
                backups.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })
            
            return backups
            
        except ClientError as e:
            logger.error(f"S3 list failed: {e}")
            raise

# Global backup and recovery managers
backup_manager = BackupManager()
recovery_manager = RecoveryManager()
