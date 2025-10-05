# core/management/commands/health_check.py
# Django management command for system health check

import time
import psutil
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from core.models import Company, AuditLog
from crm.models import Account, Contact, Lead
from activities.models import Activity, Task, Event
from deals.models import Deal
from products.models import Product
from territories.models import Territory

User = get_user_model()

class Command(BaseCommand):
    help = 'Perform comprehensive system health check'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed health information',
        )
        parser.add_argument(
            '--fix-issues',
            action='store_true',
            help='Attempt to fix common issues',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting system health check...'))
        
        health_status = {
            'overall': 'HEALTHY',
            'checks': {}
        }
        
        # Database health
        db_health = self.check_database()
        health_status['checks']['database'] = db_health
        
        # Cache health
        cache_health = self.check_cache()
        health_status['checks']['cache'] = cache_health
        
        # System resources
        system_health = self.check_system_resources()
        health_status['checks']['system'] = system_health
        
        # Data integrity
        data_health = self.check_data_integrity()
        health_status['checks']['data'] = data_health
        
        # Security
        security_health = self.check_security()
        health_status['checks']['security'] = security_health
        
        # Performance
        performance_health = self.check_performance()
        health_status['checks']['performance'] = performance_health
        
        # Determine overall health
        failed_checks = [check for check in health_status['checks'].values() if check['status'] != 'HEALTHY']
        if failed_checks:
            health_status['overall'] = 'UNHEALTHY'
        
        # Display results
        self.display_health_results(health_status, options['detailed'])
        
        # Fix issues if requested
        if options['fix_issues'] and failed_checks:
            self.fix_issues(failed_checks)

    def check_database(self):
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            response_time = time.time() - start_time
            
            # Check connection pool
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_stat_activity")
                active_connections = cursor.fetchone()[0]
            
            status = 'HEALTHY'
            issues = []
            
            if response_time > 1.0:
                status = 'WARNING'
                issues.append(f'Slow database response: {response_time:.2f}s')
            
            if active_connections > 50:
                status = 'WARNING'
                issues.append(f'High connection count: {active_connections}')
            
            return {
                'status': status,
                'response_time': response_time,
                'active_connections': active_connections,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'status': 'UNHEALTHY',
                'error': str(e),
                'issues': ['Database connection failed']
            }

    def check_cache(self):
        """Check cache connectivity and performance"""
        try:
            start_time = time.time()
            test_key = 'health_check_test'
            test_value = 'test_value'
            
            # Test cache write
            cache.set(test_key, test_value, 60)
            
            # Test cache read
            retrieved_value = cache.get(test_key)
            
            response_time = time.time() - start_time
            
            status = 'HEALTHY'
            issues = []
            
            if retrieved_value != test_value:
                status = 'UNHEALTHY'
                issues.append('Cache read/write mismatch')
            
            if response_time > 0.1:
                status = 'WARNING'
                issues.append(f'Slow cache response: {response_time:.3f}s')
            
            # Clean up test key
            cache.delete(test_key)
            
            return {
                'status': status,
                'response_time': response_time,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'status': 'UNHEALTHY',
                'error': str(e),
                'issues': ['Cache connection failed']
            }

    def check_system_resources(self):
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            status = 'HEALTHY'
            issues = []
            
            if cpu_percent > 80:
                status = 'WARNING'
                issues.append(f'High CPU usage: {cpu_percent}%')
            
            if memory_percent > 85:
                status = 'WARNING'
                issues.append(f'High memory usage: {memory_percent}%')
            
            if disk_percent > 90:
                status = 'WARNING'
                issues.append(f'High disk usage: {disk_percent}%')
            
            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'status': 'UNHEALTHY',
                'error': str(e),
                'issues': ['System resource check failed']
            }

    def check_data_integrity(self):
        """Check data integrity and consistency"""
        try:
            issues = []
            
            # Check for orphaned records
            orphaned_contacts = Contact.objects.filter(account__isnull=True).count()
            if orphaned_contacts > 0:
                issues.append(f'{orphaned_contacts} contacts without accounts')
            
            # Check for missing required fields
            incomplete_accounts = Account.objects.filter(name__isnull=True).count()
            if incomplete_accounts > 0:
                issues.append(f'{incomplete_accounts} accounts with missing names')
            
            # Check for duplicate emails
            from django.db.models import Count
            duplicate_emails = Contact.objects.values('email').annotate(
                count=Count('email')
            ).filter(count__gt=1).count()
            if duplicate_emails > 0:
                issues.append(f'{duplicate_emails} duplicate email addresses')
            
            status = 'HEALTHY' if not issues else 'WARNING'
            
            return {
                'status': status,
                'issues': issues,
                'orphaned_contacts': orphaned_contacts,
                'incomplete_accounts': incomplete_accounts,
                'duplicate_emails': duplicate_emails
            }
            
        except Exception as e:
            return {
                'status': 'UNHEALTHY',
                'error': str(e),
                'issues': ['Data integrity check failed']
            }

    def check_security(self):
        """Check security configurations"""
        try:
            issues = []
            
            # Check for default secret key
            if settings.SECRET_KEY == 'django-insecure-change-this-in-production':
                issues.append('Using default secret key')
            
            # Check for debug mode in production
            if settings.DEBUG:
                issues.append('Debug mode is enabled')
            
            # Check for insecure settings
            if not settings.SECURE_SSL_REDIRECT:
                issues.append('SSL redirect not enabled')
            
            # Check for weak password requirements
            if not hasattr(settings, 'AUTH_PASSWORD_VALIDATORS') or not settings.AUTH_PASSWORD_VALIDATORS:
                issues.append('No password validators configured')
            
            status = 'HEALTHY' if not issues else 'WARNING'
            
            return {
                'status': status,
                'issues': issues,
                'debug_mode': settings.DEBUG,
                'ssl_redirect': settings.SECURE_SSL_REDIRECT
            }
            
        except Exception as e:
            return {
                'status': 'UNHEALTHY',
                'error': str(e),
                'issues': ['Security check failed']
            }

    def check_performance(self):
        """Check system performance metrics"""
        try:
            issues = []
            
            # Check database query performance
            start_time = time.time()
            Account.objects.count()
            db_query_time = time.time() - start_time
            
            if db_query_time > 0.5:
                issues.append(f'Slow database queries: {db_query_time:.3f}s')
            
            # Check cache performance
            start_time = time.time()
            cache.get('non_existent_key')
            cache_query_time = time.time() - start_time
            
            if cache_query_time > 0.1:
                issues.append(f'Slow cache queries: {cache_query_time:.3f}s')
            
            # Check record counts
            total_records = (
                Account.objects.count() +
                Contact.objects.count() +
                Lead.objects.count() +
                Deal.objects.count() +
                Activity.objects.count()
            )
            
            if total_records > 100000:
                issues.append(f'Large dataset: {total_records} records')
            
            status = 'HEALTHY' if not issues else 'WARNING'
            
            return {
                'status': status,
                'issues': issues,
                'db_query_time': db_query_time,
                'cache_query_time': cache_query_time,
                'total_records': total_records
            }
            
        except Exception as e:
            return {
                'status': 'UNHEALTHY',
                'error': str(e),
                'issues': ['Performance check failed']
            }

    def display_health_results(self, health_status, detailed):
        """Display health check results"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f"Overall Health: {health_status['overall']}")
        self.stdout.write('='*50)
        
        for check_name, check_result in health_status['checks'].items():
            status_color = self.style.SUCCESS if check_result['status'] == 'HEALTHY' else self.style.WARNING
            self.stdout.write(f"\n{check_name.upper()}: {status_color(check_result['status'])}")
            
            if detailed:
                for key, value in check_result.items():
                    if key not in ['status', 'issues', 'error']:
                        self.stdout.write(f"  {key}: {value}")
            
            if 'issues' in check_result and check_result['issues']:
                for issue in check_result['issues']:
                    self.stdout.write(f"  ⚠️  {issue}")
            
            if 'error' in check_result:
                self.stdout.write(f"  ❌ Error: {check_result['error']}")

    def fix_issues(self, failed_checks):
        """Attempt to fix common issues"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write("Attempting to fix issues...")
        self.stdout.write('='*50)
        
        for check in failed_checks:
            if check['status'] == 'UNHEALTHY':
                self.stdout.write(f"❌ Cannot auto-fix: {check.get('error', 'Unknown error')}")
            else:
                self.stdout.write(f"⚠️  Manual intervention required for: {check.get('issues', [])}")
        
        self.stdout.write("\nSome issues may require manual intervention.")
