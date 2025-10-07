# compliance/retention_engine.py
# Data retention enforcement engine

from datetime import timedelta
from django.utils import timezone
from django.apps import apps
from django.db.models import Q
from .models import RetentionLog


class RetentionEngine:
    """Engine for enforcing data retention policies"""
    
    def execute_policy(self, policy) -> dict:
        """
        Execute retention policy
        
        Args:
            policy: RetentionPolicy instance
            
        Returns:
            Dictionary with execution results
        """
        result = {
            'success': True,
            'records_processed': 0,
            'records_deleted': 0,
            'records_archived': 0,
            'errors': []
        }
        
        # Create log entry
        log = RetentionLog.objects.create(
            policy=policy,
            company=policy.company
        )
        
        try:
            # Get model
            model = apps.get_model('crm', policy.entity_type)
        except LookupError:
            result['success'] = False
            result['errors'].append(f"Model {policy.entity_type} not found")
            log.errors_encountered = 1
            log.execution_details = result
            log.execution_completed = timezone.now()
            log.save()
            return result
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=policy.retention_days)
        
        # Build query
        query = Q(company=policy.company, created_at__lt=cutoff_date)
        
        # Apply filter conditions
        if policy.filter_conditions:
            for field, value in policy.filter_conditions.items():
                query &= Q(**{field: value})
        
        # Get records
        records = model.objects.filter(query)
        result['records_processed'] = records.count()
        
        # Process records based on deletion method
        if policy.deletion_method == 'hard':
            # Hard delete (physical removal)
            count = records.count()
            records.delete()
            result['records_deleted'] = count
        
        elif policy.deletion_method == 'soft':
            # Soft delete (mark as deleted)
            if hasattr(model, 'is_deleted'):
                count = records.update(is_deleted=True)
                result['records_deleted'] = count
            else:
                result['errors'].append(f"Model {policy.entity_type} does not support soft delete")
        
        elif policy.deletion_method == 'archive':
            # Archive (move to cold storage)
            result['records_archived'] = self._archive_records(records, policy)
        
        # Update log
        log.records_processed = result['records_processed']
        log.records_deleted = result['records_deleted']
        log.records_archived = result['records_archived']
        log.errors_encountered = len(result['errors'])
        log.execution_details = result
        log.execution_completed = timezone.now()
        
        # Add compliance log
        log.compliance_log = {
            'policy_name': policy.name,
            'entity_type': policy.entity_type,
            'retention_days': policy.retention_days,
            'deletion_method': policy.deletion_method,
            'cutoff_date': cutoff_date.isoformat(),
            'executed_at': timezone.now().isoformat(),
            'compliance_frameworks': policy.company.dataresidency_set.first().compliance_frameworks if policy.company.dataresidency_set.exists() else []
        }
        
        log.save()
        
        # Update policy
        policy.last_executed = timezone.now()
        
        # Schedule next execution (e.g., daily)
        policy.next_execution = timezone.now() + timedelta(days=1)
        policy.save()
        
        return result
    
    def _archive_records(self, records, policy) -> int:
        """
        Archive records to cold storage
        
        Args:
            records: QuerySet of records to archive
            policy: RetentionPolicy instance
            
        Returns:
            Number of records archived
        """
        # In a real implementation, this would:
        # 1. Export records to cold storage (S3 Glacier, etc.)
        # 2. Mark records as archived or delete them
        # 3. Keep metadata for retrieval
        
        count = records.count()
        
        # For now, just mark as archived if the field exists
        if hasattr(records.model, 'is_archived'):
            records.update(is_archived=True)
        
        return count
    
    def get_records_for_deletion(self, policy):
        """
        Get records that will be deleted (for preview)
        
        Args:
            policy: RetentionPolicy instance
            
        Returns:
            QuerySet of records
        """
        try:
            model = apps.get_model('crm', policy.entity_type)
        except LookupError:
            return None
        
        cutoff_date = timezone.now() - timedelta(days=policy.retention_days)
        
        query = Q(company=policy.company, created_at__lt=cutoff_date)
        
        if policy.filter_conditions:
            for field, value in policy.filter_conditions.items():
                query &= Q(**{field: value})
        
        return model.objects.filter(query)


class RetentionScheduler:
    """Scheduler for retention policy execution"""
    
    @staticmethod
    def get_policies_to_execute():
        """Get retention policies that need to be executed"""
        from .models import RetentionPolicy
        
        now = timezone.now()
        
        # Get active policies that are due for execution
        policies = RetentionPolicy.objects.filter(
            is_active=True,
            next_execution__lte=now
        )
        
        return policies
    
    @staticmethod
    def execute_scheduled_policies():
        """Execute all scheduled retention policies"""
        from .models import RetentionPolicy
        
        policies = RetentionScheduler.get_policies_to_execute()
        
        results = []
        engine = RetentionEngine()
        
        for policy in policies:
            try:
                result = engine.execute_policy(policy)
                results.append({
                    'policy_id': policy.id,
                    'policy_name': policy.name,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'policy_id': policy.id,
                    'policy_name': policy.name,
                    'error': str(e)
                })
        
        return results
