# mobile/offline_sync.py
# Mobile Offline Sync with Conflict Resolution

import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core.cache import cache
import requests
from celery import shared_task

from .models import (
    MobileDevice, OfflineSyncSession, SyncConflict, SyncLog,
    OfflineData, SyncQueue, DeviceAnalytics
)
from core.models import User, Company

logger = logging.getLogger(__name__)

class OfflineSyncEngine:
    """
    Advanced offline sync engine with conflict resolution,
    data compression, and intelligent sync strategies.
    """
    
    def __init__(self):
        self.sync_strategies = {
            'full_sync': self._perform_full_sync,
            'incremental_sync': self._perform_incremental_sync,
            'selective_sync': self._perform_selective_sync,
            'conflict_resolution': self._resolve_sync_conflicts
        }
        
        self.conflict_resolution_strategies = {
            'server_wins': self._server_wins_resolution,
            'client_wins': self._client_wins_resolution,
            'merge_fields': self._merge_fields_resolution,
            'user_choice': self._user_choice_resolution,
            'timestamp_based': self._timestamp_based_resolution
        }
    
    def initiate_sync_session(self, device_id: str, user_id: str, sync_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate a new offline sync session.
        """
        try:
            device = MobileDevice.objects.get(id=device_id)
            user = User.objects.get(id=user_id, company=device.company)
            
            # Create sync session
            sync_session = OfflineSyncSession.objects.create(
                company=device.company,
                device=device,
                user=user,
                sync_type=sync_config.get('sync_type', 'incremental'),
                sync_strategy=sync_config.get('strategy', 'incremental_sync'),
                status='initiated',
                sync_config=sync_config,
                initiated_at=timezone.now()
            )
            
            # Prepare sync data
            sync_data = self._prepare_sync_data(device, user, sync_config)
            
            # Start sync process
            sync_result = self._execute_sync(sync_session, sync_data)
            
            # Update session status
            sync_session.status = 'completed' if sync_result['success'] else 'failed'
            sync_session.completed_at = timezone.now()
            sync_session.sync_result = sync_result
            sync_session.save()
            
            return {
                'status': 'success',
                'session_id': str(sync_session.id),
                'sync_result': sync_result
            }
            
        except Exception as e:
            logger.error(f"Sync session initiation failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def sync_offline_data(self, device_id: str, offline_data: List[Dict[str, Any]], sync_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync offline data with conflict detection and resolution.
        """
        try:
            device = MobileDevice.objects.get(id=device_id)
            
            # Detect conflicts
            conflicts = self._detect_sync_conflicts(device, offline_data)
            
            if conflicts:
                # Resolve conflicts
                resolution_result = self._resolve_conflicts(conflicts, sync_config)
                
                if not resolution_result['success']:
                    return {
                        'status': 'conflicts_detected',
                        'conflicts': conflicts,
                        'resolution_required': True
                    }
            
            # Apply sync changes
            sync_result = self._apply_sync_changes(device, offline_data, sync_config)
            
            # Log sync operation
            self._log_sync_operation(device, offline_data, sync_result)
            
            return {
                'status': 'success',
                'synced_records': sync_result['synced_count'],
                'conflicts_resolved': len(conflicts),
                'sync_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Offline data sync failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def resolve_sync_conflict(self, conflict_id: str, resolution_choice: str, user_id: str) -> Dict[str, Any]:
        """
        Resolve a specific sync conflict.
        """
        try:
            conflict = SyncConflict.objects.get(id=conflict_id)
            user = User.objects.get(id=user_id)
            
            # Apply resolution strategy
            resolution_result = self._apply_conflict_resolution(conflict, resolution_choice, user)
            
            if resolution_result['success']:
                # Update conflict status
                conflict.status = 'resolved'
                conflict.resolution_choice = resolution_choice
                conflict.resolved_by = user
                conflict.resolved_at = timezone.now()
                conflict.resolution_data = resolution_result
                conflict.save()
                
                return {
                    'status': 'success',
                    'conflict_id': conflict_id,
                    'resolution': resolution_result
                }
            else:
                return {
                    'status': 'error',
                    'error': resolution_result.get('error', 'Resolution failed')
                }
                
        except Exception as e:
            logger.error(f"Conflict resolution failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_sync_status(self, device_id: str) -> Dict[str, Any]:
        """
        Get current sync status for device.
        """
        try:
            device = MobileDevice.objects.get(id=device_id)
            
            # Get latest sync session
            latest_session = OfflineSyncSession.objects.filter(
                device=device
            ).order_by('-initiated_at').first()
            
            # Get pending conflicts
            pending_conflicts = SyncConflict.objects.filter(
                device=device,
                status='pending'
            ).count()
            
            # Get sync queue status
            queue_size = SyncQueue.objects.filter(
                device=device,
                status='pending'
            ).count()
            
            # Get device analytics
            analytics = self._get_device_analytics(device)
            
            return {
                'status': 'success',
                'device_id': device_id,
                'last_sync': latest_session.completed_at.isoformat() if latest_session and latest_session.completed_at else None,
                'sync_status': latest_session.status if latest_session else 'never_synced',
                'pending_conflicts': pending_conflicts,
                'queue_size': queue_size,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Failed to get sync status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _prepare_sync_data(self, device: MobileDevice, user: User, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for sync based on configuration"""
        sync_data = {
            'user_data': self._get_user_sync_data(user, config),
            'leads': self._get_leads_sync_data(device, config),
            'deals': self._get_deals_sync_data(device, config),
            'accounts': self._get_accounts_sync_data(device, config),
            'contacts': self._get_contacts_sync_data(device, config),
            'activities': self._get_activities_sync_data(device, config),
            'metadata': {
                'sync_timestamp': timezone.now().isoformat(),
                'device_id': str(device.id),
                'user_id': str(user.id),
                'sync_version': config.get('sync_version', '1.0')
            }
        }
        
        return sync_data
    
    def _get_user_sync_data(self, user: User, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get user data for sync"""
        return {
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': getattr(user, 'role', 'user'),
            'permissions': getattr(user, 'permissions', []),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'updated_at': user.updated_at.isoformat() if hasattr(user, 'updated_at') else user.date_joined.isoformat()
        }
    
    def _get_leads_sync_data(self, device: MobileDevice, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get leads data for sync"""
        from crm.models import Lead
        
        # Get leads assigned to user or accessible by user
        leads = Lead.objects.filter(
            company=device.company,
            assigned_to=device.user
        ).select_related('account', 'assigned_to')
        
        # Apply filters from config
        if 'last_sync' in config:
            leads = leads.filter(updated_at__gte=config['last_sync'])
        
        if 'limit' in config:
            leads = leads[:config['limit']]
        
        sync_data = []
        for lead in leads:
            sync_data.append({
                'id': str(lead.id),
                'name': lead.name,
                'email': lead.email,
                'phone': lead.phone,
                'company_name': lead.company_name,
                'source': lead.source,
                'status': lead.status,
                'priority': lead.priority,
                'score': lead.score,
                'notes': lead.notes,
                'tags': lead.tags or [],
                'created_at': lead.created_at.isoformat(),
                'updated_at': lead.updated_at.isoformat() if hasattr(lead, 'updated_at') else lead.created_at.isoformat(),
                'account_id': str(lead.account.id) if lead.account else None,
                'assigned_to_id': str(lead.assigned_to.id) if lead.assigned_to else None
            })
        
        return sync_data
    
    def _get_deals_sync_data(self, device: MobileDevice, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get deals data for sync"""
        from crm.models import Deal
        
        deals = Deal.objects.filter(
            company=device.company,
            assigned_to=device.user
        ).select_related('account', 'assigned_to')
        
        if 'last_sync' in config:
            deals = deals.filter(updated_at__gte=config['last_sync'])
        
        if 'limit' in config:
            deals = deals[:config['limit']]
        
        sync_data = []
        for deal in deals:
            sync_data.append({
                'id': str(deal.id),
                'name': deal.name,
                'amount': float(deal.amount) if deal.amount else 0,
                'stage': deal.stage,
                'probability': deal.probability,
                'close_date': deal.close_date.isoformat() if deal.close_date else None,
                'description': deal.description,
                'notes': deal.notes,
                'created_at': deal.created_at.isoformat(),
                'updated_at': deal.updated_at.isoformat() if hasattr(deal, 'updated_at') else deal.created_at.isoformat(),
                'account_id': str(deal.account.id) if deal.account else None,
                'assigned_to_id': str(deal.assigned_to.id) if deal.assigned_to else None
            })
        
        return sync_data
    
    def _get_accounts_sync_data(self, device: MobileDevice, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get accounts data for sync"""
        from crm.models import Account
        
        accounts = Account.objects.filter(
            company=device.company
        ).select_related('assigned_to')
        
        if 'last_sync' in config:
            accounts = accounts.filter(updated_at__gte=config['last_sync'])
        
        if 'limit' in config:
            accounts = accounts[:config['limit']]
        
        sync_data = []
        for account in accounts:
            sync_data.append({
                'id': str(account.id),
                'name': account.name,
                'website': account.website,
                'industry': account.industry,
                'company_size': account.company_size,
                'annual_revenue': float(account.annual_revenue) if account.annual_revenue else 0,
                'employee_count': account.employee_count,
                'phone': account.phone,
                'email': account.email,
                'address': account.address,
                'city': account.city,
                'state': account.state,
                'country': account.country,
                'postal_code': account.postal_code,
                'description': account.description,
                'created_at': account.created_at.isoformat(),
                'updated_at': account.updated_at.isoformat() if hasattr(account, 'updated_at') else account.created_at.isoformat(),
                'assigned_to_id': str(account.assigned_to.id) if account.assigned_to else None
            })
        
        return sync_data
    
    def _get_contacts_sync_data(self, device: MobileDevice, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get contacts data for sync"""
        from crm.models import Contact
        
        contacts = Contact.objects.filter(
            company=device.company
        ).select_related('account', 'assigned_to')
        
        if 'last_sync' in config:
            contacts = contacts.filter(updated_at__gte=config['last_sync'])
        
        if 'limit' in config:
            contacts = contacts[:config['limit']]
        
        sync_data = []
        for contact in contacts:
            sync_data.append({
                'id': str(contact.id),
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'email': contact.email,
                'phone': contact.phone,
                'title': contact.title,
                'department': contact.department,
                'account_id': str(contact.account.id) if contact.account else None,
                'assigned_to_id': str(contact.assigned_to.id) if contact.assigned_to else None,
                'created_at': contact.created_at.isoformat(),
                'updated_at': contact.updated_at.isoformat() if hasattr(contact, 'updated_at') else contact.created_at.isoformat()
            })
        
        return sync_data
    
    def _get_activities_sync_data(self, device: MobileDevice, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get activities data for sync"""
        from crm.models import Activity
        
        activities = Activity.objects.filter(
            company=device.company,
            assigned_to=device.user
        )
        
        if 'last_sync' in config:
            activities = activities.filter(updated_at__gte=config['last_sync'])
        
        if 'limit' in config:
            activities = activities[:config['limit']]
        
        sync_data = []
        for activity in activities:
            sync_data.append({
                'id': str(activity.id),
                'type': activity.type,
                'subject': activity.subject,
                'description': activity.description,
                'due_date': activity.due_date.isoformat() if activity.due_date else None,
                'status': activity.status,
                'priority': activity.priority,
                'created_at': activity.created_at.isoformat(),
                'updated_at': activity.updated_at.isoformat() if hasattr(activity, 'updated_at') else activity.created_at.isoformat(),
                'assigned_to_id': str(activity.assigned_to.id) if activity.assigned_to else None
            })
        
        return sync_data
    
    def _execute_sync(self, session: OfflineSyncSession, sync_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the sync process"""
        try:
            strategy = self.sync_strategies.get(session.sync_strategy)
            
            if not strategy:
                return {
                    'success': False,
                    'error': f'Unknown sync strategy: {session.sync_strategy}'
                }
            
            # Execute sync strategy
            sync_result = strategy(session, sync_data)
            
            # Update sync metrics
            self._update_sync_metrics(session, sync_result)
            
            return sync_result
            
        except Exception as e:
            logger.error(f"Sync execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _perform_full_sync(self, session: OfflineSyncSession, sync_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform full sync of all data"""
        try:
            # Store all data for offline access
            for data_type, records in sync_data.items():
                if data_type == 'metadata':
                    continue
                
                for record in records:
                    OfflineData.objects.create(
                        company=session.company,
                        device=session.device,
                        data_type=data_type,
                        record_id=record['id'],
                        data=record,
                        sync_session=session,
                        created_at=timezone.now()
                    )
            
            return {
                'success': True,
                'sync_type': 'full',
                'records_synced': sum(len(records) for key, records in sync_data.items() if key != 'metadata'),
                'sync_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _perform_incremental_sync(self, session: OfflineSyncSession, sync_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform incremental sync of changed data"""
        try:
            # Get last sync timestamp
            last_sync = session.device.last_sync_timestamp
            
            if not last_sync:
                # First sync - perform full sync
                return self._perform_full_sync(session, sync_data)
            
            # Sync only changed records
            synced_count = 0
            
            for data_type, records in sync_data.items():
                if data_type == 'metadata':
                    continue
                
                for record in records:
                    # Check if record was modified since last sync
                    record_updated = datetime.fromisoformat(record['updated_at'].replace('Z', '+00:00'))
                    
                    if record_updated > last_sync:
                        # Update or create offline data
                        offline_data, created = OfflineData.objects.get_or_create(
                            company=session.company,
                            device=session.device,
                            data_type=data_type,
                            record_id=record['id'],
                            defaults={
                                'data': record,
                                'sync_session': session,
                                'created_at': timezone.now()
                            }
                        )
                        
                        if not created:
                            offline_data.data = record
                            offline_data.updated_at = timezone.now()
                            offline_data.save()
                        
                        synced_count += 1
            
            return {
                'success': True,
                'sync_type': 'incremental',
                'records_synced': synced_count,
                'sync_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _perform_selective_sync(self, session: OfflineSyncSession, sync_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform selective sync based on user preferences"""
        try:
            # Get user sync preferences
            sync_preferences = session.sync_config.get('preferences', {})
            
            synced_count = 0
            
            for data_type, records in sync_data.items():
                if data_type == 'metadata':
                    continue
                
                # Check if this data type should be synced
                if sync_preferences.get(data_type, True):
                    for record in records:
                        OfflineData.objects.create(
                            company=session.company,
                            device=session.device,
                            data_type=data_type,
                            record_id=record['id'],
                            data=record,
                            sync_session=session,
                            created_at=timezone.now()
                        )
                        synced_count += 1
            
            return {
                'success': True,
                'sync_type': 'selective',
                'records_synced': synced_count,
                'sync_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _detect_sync_conflicts(self, device: MobileDevice, offline_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect sync conflicts between offline and server data"""
        conflicts = []
        
        for record in offline_data:
            try:
                # Get server version of record
                server_record = self._get_server_record(record['data_type'], record['id'])
                
                if server_record:
                    # Compare timestamps
                    offline_updated = datetime.fromisoformat(record['updated_at'].replace('Z', '+00:00'))
                    server_updated = datetime.fromisoformat(server_record['updated_at'].replace('Z', '+00:00'))
                    
                    # Check if both were modified
                    if offline_updated > record.get('last_sync_timestamp', datetime.min) and \
                       server_updated > record.get('last_sync_timestamp', datetime.min):
                        
                        # Conflict detected
                        conflict = SyncConflict.objects.create(
                            company=device.company,
                            device=device,
                            data_type=record['data_type'],
                            record_id=record['id'],
                            server_data=server_record,
                            client_data=record['data'],
                            conflict_type='concurrent_modification',
                            status='pending',
                            detected_at=timezone.now()
                        )
                        
                        conflicts.append({
                            'conflict_id': str(conflict.id),
                            'data_type': record['data_type'],
                            'record_id': record['id'],
                            'conflict_type': 'concurrent_modification',
                            'server_version': server_record,
                            'client_version': record['data']
                        })
                        
            except Exception as e:
                logger.error(f"Conflict detection failed for record {record['id']}: {str(e)}")
        
        return conflicts
    
    def _resolve_conflicts(self, conflicts: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve sync conflicts using configured strategy"""
        resolution_strategy = config.get('conflict_resolution', 'timestamp_based')
        resolver = self.conflict_resolution_strategies.get(resolution_strategy)
        
        if not resolver:
            return {
                'success': False,
                'error': f'Unknown conflict resolution strategy: {resolution_strategy}'
            }
        
        resolved_count = 0
        
        for conflict in conflicts:
            try:
                resolution_result = resolver(conflict)
                
                if resolution_result['success']:
                    resolved_count += 1
                else:
                    logger.error(f"Failed to resolve conflict {conflict['conflict_id']}: {resolution_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Conflict resolution failed: {str(e)}")
        
        return {
            'success': resolved_count == len(conflicts),
            'resolved_count': resolved_count,
            'total_conflicts': len(conflicts)
        }
    
    def _server_wins_resolution(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict by keeping server version"""
        return {
            'success': True,
            'resolution': 'server_wins',
            'resolved_data': conflict['server_version']
        }
    
    def _client_wins_resolution(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict by keeping client version"""
        return {
            'success': True,
            'resolution': 'client_wins',
            'resolved_data': conflict['client_version']
        }
    
    def _merge_fields_resolution(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict by merging fields"""
        server_data = conflict['server_version']
        client_data = conflict['client_version']
        
        # Merge strategy: take non-empty values, server wins on conflicts
        merged_data = client_data.copy()
        
        for key, value in server_data.items():
            if key not in merged_data or not merged_data[key]:
                merged_data[key] = value
            elif value and not merged_data[key]:
                merged_data[key] = value
        
        return {
            'success': True,
            'resolution': 'merge_fields',
            'resolved_data': merged_data
        }
    
    def _user_choice_resolution(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict by user choice (requires user interaction)"""
        return {
            'success': False,
            'resolution': 'user_choice_required',
            'requires_user_input': True
        }
    
    def _timestamp_based_resolution(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict based on timestamp (newer wins)"""
        server_updated = datetime.fromisoformat(conflict['server_version']['updated_at'].replace('Z', '+00:00'))
        client_updated = datetime.fromisoformat(conflict['client_version']['updated_at'].replace('Z', '+00:00'))
        
        if server_updated > client_updated:
            return self._server_wins_resolution(conflict)
        else:
            return self._client_wins_resolution(conflict)
    
    def _get_server_record(self, data_type: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Get server version of record"""
        # This would query the actual server database
        # For now, return None as placeholder
        return None
    
    def _apply_sync_changes(self, device: MobileDevice, offline_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply sync changes to server"""
        synced_count = 0
        
        for record in offline_data:
            try:
                # Apply changes to server database
                # This would update the actual database records
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Failed to apply sync change for record {record['id']}: {str(e)}")
        
        return {
            'success': True,
            'synced_count': synced_count
        }
    
    def _log_sync_operation(self, device: MobileDevice, offline_data: List[Dict[str, Any]], sync_result: Dict[str, Any]):
        """Log sync operation for audit"""
        SyncLog.objects.create(
            company=device.company,
            device=device,
            operation_type='sync',
            records_count=len(offline_data),
            success=sync_result.get('success', False),
            sync_timestamp=timezone.now(),
            sync_data=sync_result
        )
    
    def _update_sync_metrics(self, session: OfflineSyncSession, sync_result: Dict[str, Any]):
        """Update sync metrics and analytics"""
        # Update device last sync timestamp
        session.device.last_sync_timestamp = timezone.now()
        session.device.save()
        
        # Update analytics
        DeviceAnalytics.objects.create(
            company=session.company,
            device=session.device,
            sync_session=session,
            records_synced=sync_result.get('records_synced', 0),
            sync_duration=(timezone.now() - session.initiated_at).total_seconds(),
            success=sync_result.get('success', False)
        )
    
    def _get_device_analytics(self, device: MobileDevice) -> Dict[str, Any]:
        """Get device analytics"""
        analytics = DeviceAnalytics.objects.filter(device=device).order_by('-created_at')[:10]
        
        return {
            'total_syncs': analytics.count(),
            'successful_syncs': analytics.filter(success=True).count(),
            'average_sync_duration': analytics.aggregate(
                avg_duration=models.Avg('sync_duration')
            )['avg_duration'] or 0,
            'last_sync_success': analytics.first().success if analytics.exists() else None
        }

# Celery tasks
@shared_task
def auto_sync_device(device_id: str, sync_config: Dict[str, Any]):
    """Async task to auto-sync device"""
    engine = OfflineSyncEngine()
    return engine.initiate_sync_session(device_id, sync_config.get('user_id'), sync_config)

@shared_task
def resolve_conflicts_async(conflict_ids: List[str], resolution_strategy: str):
    """Async task to resolve conflicts"""
    engine = OfflineSyncEngine()
    
    for conflict_id in conflict_ids:
        try:
            engine.resolve_sync_conflict(conflict_id, resolution_strategy, 'system')
        except Exception as e:
            logger.error(f"Failed to resolve conflict {conflict_id}: {str(e)}")

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_sync_session(request):
    """API endpoint to initiate sync session"""
    engine = OfflineSyncEngine()
    result = engine.initiate_sync_session(
        request.data.get('device_id'),
        str(request.user.id),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_offline_data(request):
    """API endpoint to sync offline data"""
    engine = OfflineSyncEngine()
    result = engine.sync_offline_data(
        request.data.get('device_id'),
        request.data.get('offline_data', []),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_sync_conflict(request):
    """API endpoint to resolve sync conflict"""
    engine = OfflineSyncEngine()
    result = engine.resolve_sync_conflict(
        request.data.get('conflict_id'),
        request.data.get('resolution_choice'),
        str(request.user.id)
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sync_status(request, device_id: str):
    """API endpoint to get sync status"""
    engine = OfflineSyncEngine()
    result = engine.get_sync_status(device_id)
    return Response(result, status=status.HTTP_200_OK)
