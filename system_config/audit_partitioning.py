# system_config/audit_partitioning.py
# Audit table partitioning by month and archiver job

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.db import connection, transaction
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class AuditPartitionManager:
    """
    Manages monthly partitioning of audit log tables.
    Creates and manages PostgreSQL table partitions for audit logs.
    """
    
    TABLE_NAME = 'audit_log'
    PARTITION_PREFIX = 'audit_log_y'
    RETENTION_MONTHS = getattr(settings, 'AUDIT_RETENTION_MONTHS', 12)
    
    @classmethod
    def create_partition_table(cls) -> bool:
        """
        Create main partitioned audit log table.
        
        Returns:
            True if successful, False otherwise
        """
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
            id BIGSERIAL NOT NULL,
            company_id UUID NOT NULL,
            action VARCHAR(20) NOT NULL,
            user_id INTEGER,
            object_type VARCHAR(100),
            object_id VARCHAR(100),
            object_name VARCHAR(255),
            description TEXT,
            details JSONB DEFAULT '{{}}',
            ip_address INET,
            user_agent TEXT,
            request_path VARCHAR(500),
            request_method VARCHAR(10),
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at);
        
        CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_company_action 
            ON {cls.TABLE_NAME} (company_id, action);
        
        CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_company_user 
            ON {cls.TABLE_NAME} (company_id, user_id);
        
        CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_company_object 
            ON {cls.TABLE_NAME} (company_id, object_type);
        
        CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_created 
            ON {cls.TABLE_NAME} (created_at);
        """
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(create_table_sql)
            logger.info(f"Created partitioned audit log table")
            return True
        except Exception as e:
            logger.error(f"Error creating partition table: {e}")
            return False
    
    @classmethod
    def create_monthly_partition(cls, year: int, month: int) -> bool:
        """
        Create a monthly partition for audit logs.
        
        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
            
        Returns:
            True if successful
        """
        partition_name = f"{cls.PARTITION_PREFIX}{year}m{month:02d}"
        
        # Calculate partition boundaries
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        create_partition_sql = f"""
        CREATE TABLE IF NOT EXISTS {partition_name}
        PARTITION OF {cls.TABLE_NAME}
        FOR VALUES FROM ('{start_date.isoformat()}') TO ('{end_date.isoformat()}');
        """
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(create_partition_sql)
            logger.info(f"Created partition: {partition_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating partition {partition_name}: {e}")
            return False
    
    @classmethod
    def ensure_partitions(cls, months_ahead: int = 3) -> List[str]:
        """
        Ensure partitions exist for current and future months.
        
        Args:
            months_ahead: Number of months ahead to create partitions
            
        Returns:
            List of created partition names
        """
        created_partitions = []
        current_date = timezone.now()
        
        for i in range(-1, months_ahead + 1):  # Include last month and future months
            target_date = current_date + timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month
            
            if cls.create_monthly_partition(year, month):
                partition_name = f"{cls.PARTITION_PREFIX}{year}m{month:02d}"
                created_partitions.append(partition_name)
        
        logger.info(f"Ensured {len(created_partitions)} partitions exist")
        return created_partitions
    
    @classmethod
    def list_partitions(cls) -> List[Dict[str, Any]]:
        """
        List all existing audit log partitions.
        
        Returns:
            List of partition information dictionaries
        """
        query = f"""
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables
        WHERE tablename LIKE '{cls.PARTITION_PREFIX}%'
        ORDER BY tablename DESC;
        """
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                partitions = [
                    {
                        'schema': row[0],
                        'name': row[1],
                        'size': row[2]
                    }
                    for row in rows
                ]
            
            logger.info(f"Found {len(partitions)} audit log partitions")
            return partitions
        except Exception as e:
            logger.error(f"Error listing partitions: {e}")
            return []
    
    @classmethod
    def get_partition_stats(cls) -> Dict[str, Any]:
        """
        Get statistics about audit log partitions.
        
        Returns:
            Dictionary with partition statistics
        """
        partitions = cls.list_partitions()
        
        # Get row counts
        total_rows = 0
        partition_rows = {}
        
        for partition in partitions:
            count_query = f"SELECT COUNT(*) FROM {partition['name']}"
            try:
                with connection.cursor() as cursor:
                    cursor.execute(count_query)
                    count = cursor.fetchone()[0]
                    partition_rows[partition['name']] = count
                    total_rows += count
            except Exception as e:
                logger.error(f"Error counting rows in {partition['name']}: {e}")
        
        return {
            'total_partitions': len(partitions),
            'total_rows': total_rows,
            'partition_details': [
                {
                    **p,
                    'row_count': partition_rows.get(p['name'], 0)
                }
                for p in partitions
            ]
        }


class AuditArchiver:
    """
    Archives old audit logs to compressed storage.
    Moves audit data older than retention period to archive tables.
    """
    
    ARCHIVE_TABLE_PREFIX = 'audit_log_archive_y'
    COMPRESSION_ENABLED = True
    
    @classmethod
    def create_archive_table(cls, year: int, month: int) -> bool:
        """
        Create archive table for a specific month.
        
        Args:
            year: Year
            month: Month
            
        Returns:
            True if successful
        """
        archive_table_name = f"{cls.ARCHIVE_TABLE_PREFIX}{year}m{month:02d}"
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {archive_table_name} (
            LIKE {AuditPartitionManager.TABLE_NAME} INCLUDING ALL
        ) WITH (
            fillfactor = 100
            {', compression = pglz' if cls.COMPRESSION_ENABLED else ''}
        );
        
        CREATE INDEX IF NOT EXISTS idx_{archive_table_name}_company 
            ON {archive_table_name} (company_id);
        
        CREATE INDEX IF NOT EXISTS idx_{archive_table_name}_created 
            ON {archive_table_name} (created_at);
        """
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(create_table_sql)
            logger.info(f"Created archive table: {archive_table_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating archive table: {e}")
            return False
    
    @classmethod
    def archive_partition(cls, partition_name: str, delete_source: bool = True) -> Dict[str, Any]:
        """
        Archive a partition to archive storage.
        
        Args:
            partition_name: Name of partition to archive
            delete_source: Whether to delete source partition after archiving
            
        Returns:
            Dictionary with archiving results
        """
        # Extract year and month from partition name
        # Format: audit_log_y2024m01
        try:
            parts = partition_name.replace(AuditPartitionManager.PARTITION_PREFIX, '').split('m')
            year = int(parts[0])
            month = int(parts[1])
        except Exception as e:
            logger.error(f"Invalid partition name format: {partition_name}")
            return {'success': False, 'error': 'Invalid partition name'}
        
        archive_table_name = f"{cls.ARCHIVE_TABLE_PREFIX}{year}m{month:02d}"
        
        # Create archive table
        if not cls.create_archive_table(year, month):
            return {'success': False, 'error': 'Failed to create archive table'}
        
        # Copy data to archive
        copy_sql = f"""
        INSERT INTO {archive_table_name}
        SELECT * FROM {partition_name};
        """
        
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Get row count before
                    cursor.execute(f"SELECT COUNT(*) FROM {partition_name}")
                    row_count = cursor.fetchone()[0]
                    
                    # Copy to archive
                    cursor.execute(copy_sql)
                    
                    # Drop source partition if requested
                    if delete_source:
                        cursor.execute(f"DROP TABLE {partition_name}")
                        logger.info(f"Dropped source partition: {partition_name}")
            
            logger.info(f"Archived {row_count} rows from {partition_name} to {archive_table_name}")
            
            return {
                'success': True,
                'partition': partition_name,
                'archive_table': archive_table_name,
                'rows_archived': row_count
            }
        except Exception as e:
            logger.error(f"Error archiving partition {partition_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def archive_old_partitions(cls, retention_months: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Archive all partitions older than retention period.
        
        Args:
            retention_months: Number of months to retain (default from settings)
            
        Returns:
            List of archiving results
        """
        if retention_months is None:
            retention_months = AuditPartitionManager.RETENTION_MONTHS
        
        cutoff_date = timezone.now() - timedelta(days=30 * retention_months)
        cutoff_year = cutoff_date.year
        cutoff_month = cutoff_date.month
        
        logger.info(f"Archiving partitions older than {cutoff_year}-{cutoff_month:02d}")
        
        partitions = AuditPartitionManager.list_partitions()
        results = []
        
        for partition in partitions:
            partition_name = partition['name']
            
            # Extract year and month
            try:
                parts = partition_name.replace(AuditPartitionManager.PARTITION_PREFIX, '').split('m')
                year = int(parts[0])
                month = int(parts[1])
                
                # Check if partition is old enough to archive
                if year < cutoff_year or (year == cutoff_year and month < cutoff_month):
                    result = cls.archive_partition(partition_name, delete_source=True)
                    results.append(result)
            except Exception as e:
                logger.error(f"Error processing partition {partition_name}: {e}")
        
        logger.info(f"Archived {len(results)} partitions")
        return results
    
    @classmethod
    def restore_from_archive(cls, archive_table_name: str) -> Dict[str, Any]:
        """
        Restore data from archive back to main table.
        
        Args:
            archive_table_name: Name of archive table
            
        Returns:
            Dictionary with restore results
        """
        restore_sql = f"""
        INSERT INTO {AuditPartitionManager.TABLE_NAME}
        SELECT * FROM {archive_table_name};
        """
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {archive_table_name}")
                row_count = cursor.fetchone()[0]
                
                cursor.execute(restore_sql)
            
            logger.info(f"Restored {row_count} rows from {archive_table_name}")
            
            return {
                'success': True,
                'archive_table': archive_table_name,
                'rows_restored': row_count
            }
        except Exception as e:
            logger.error(f"Error restoring from archive: {e}")
            return {'success': False, 'error': str(e)}


class AuditMaintenanceScheduler:
    """
    Scheduler for audit log maintenance tasks.
    """
    
    @classmethod
    def run_maintenance(cls) -> Dict[str, Any]:
        """
        Run complete maintenance cycle.
        
        Returns:
            Dictionary with maintenance results
        """
        logger.info("Starting audit log maintenance")
        
        results = {
            'started_at': timezone.now().isoformat(),
            'partitions_created': [],
            'partitions_archived': [],
            'errors': []
        }
        
        try:
            # Ensure future partitions exist
            partitions_created = AuditPartitionManager.ensure_partitions(months_ahead=3)
            results['partitions_created'] = partitions_created
        except Exception as e:
            logger.error(f"Error creating partitions: {e}")
            results['errors'].append(f"Partition creation: {str(e)}")
        
        try:
            # Archive old partitions
            archived = AuditArchiver.archive_old_partitions()
            results['partitions_archived'] = archived
        except Exception as e:
            logger.error(f"Error archiving partitions: {e}")
            results['errors'].append(f"Archiving: {str(e)}")
        
        try:
            # Get statistics
            stats = AuditPartitionManager.get_partition_stats()
            results['partition_stats'] = stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            results['errors'].append(f"Statistics: {str(e)}")
        
        results['completed_at'] = timezone.now().isoformat()
        results['success'] = len(results['errors']) == 0
        
        logger.info(f"Maintenance completed: {results['success']}")
        
        return results
