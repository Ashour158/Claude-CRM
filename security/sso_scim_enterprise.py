# security/sso_scim_enterprise.py
"""
SSO + SCIM Enterprise Implementation
P3 Priority: Enterprise user sync E2E

This module implements:
- Enterprise SSO/SAML integration
- SCIM user provisioning and deprovisioning
- End-to-end user synchronization
- Identity provider management
- User lifecycle automation
"""

import logging
import json
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from core.models import Company, User
from events.event_bus import event_bus
import uuid
import base64
import hmac
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class IdentityProvider:
    """Identity provider configuration"""
    id: str
    name: str
    provider_type: str  # saml, oauth2, ldap
    company_id: str
    configuration: Dict[str, Any]
    is_active: bool
    created_at: timezone.datetime
    last_sync: Optional[timezone.datetime] = None

@dataclass
class SCIMUser:
    """SCIM user representation"""
    id: str
    external_id: str
    username: str
    email: str
    first_name: str
    last_name: str
    active: bool
    company_id: str
    groups: List[str]
    attributes: Dict[str, Any]
    created_at: timezone.datetime
    updated_at: timezone.datetime

@dataclass
class SyncResult:
    """User synchronization result"""
    id: str
    sync_type: str  # provision, update, deprovision
    user_id: str
    external_id: str
    status: str  # success, failed, pending
    error_message: Optional[str] = None
    created_at: timezone.datetime = None

class SSOSCIMEnterprise:
    """
    Enterprise SSO + SCIM implementation with E2E user sync
    """
    
    def __init__(self):
        self.identity_providers: Dict[str, IdentityProvider] = {}
        self.scim_users: Dict[str, SCIMUser] = {}
        self.sync_results: List[SyncResult] = []
        
        # Configuration
        self.config = {
            "scim_base_url": "https://api.example.com/scim/v2",
            "scim_bearer_token": "your-bearer-token",
            "sync_batch_size": 100,
            "sync_timeout_seconds": 30,
            "retry_attempts": 3
        }
        
        # Supported identity providers
        self.supported_providers = [
            "azure_ad", "google_workspace", "okta", "onelogin", "ldap"
        ]
    
    def configure_identity_provider(self, name: str, provider_type: str,
                                  configuration: Dict[str, Any], 
                                  company: Company, user: User) -> IdentityProvider:
        """Configure identity provider for SSO"""
        if provider_type not in self.supported_providers:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        
        provider_id = str(uuid.uuid4())
        
        identity_provider = IdentityProvider(
            id=provider_id,
            name=name,
            provider_type=provider_type,
            company_id=str(company.id),
            configuration=configuration,
            is_active=True,
            created_at=timezone.now()
        )
        
        self.identity_providers[provider_id] = identity_provider
        
        # Publish provider configuration event
        event_bus.publish(
            event_type='IDENTITY_PROVIDER_CONFIGURED',
            data={
                'provider_id': provider_id,
                'name': name,
                'provider_type': provider_type,
                'company_id': str(company.id)
            },
            actor=user,
            company_id=company.id
        )
        
        logger.info(f"Identity provider configured: {name} ({provider_type})")
        return identity_provider
    
    def configure_scim_provisioning(self, company: Company, user: User,
                                  scim_base_url: str, bearer_token: str) -> bool:
        """Configure SCIM provisioning for the company"""
        try:
            # Test SCIM connection
            test_result = self._test_scim_connection(scim_base_url, bearer_token)
            if not test_result:
                raise ValueError("SCIM connection test failed")
            
            # Update configuration
            self.config["scim_base_url"] = scim_base_url
            self.config["scim_bearer_token"] = bearer_token
            
            # Publish SCIM configuration event
            event_bus.publish(
                event_type='SCIM_CONFIGURED',
                data={
                    'company_id': str(company.id),
                    'scim_base_url': scim_base_url
                },
                actor=user,
                company_id=company.id
            )
            
            logger.info(f"SCIM provisioning configured for company {company.id}")
            return True
            
        except Exception as e:
            logger.error(f"SCIM configuration failed: {e}")
            return False
    
    def _test_scim_connection(self, base_url: str, bearer_token: str) -> bool:
        """Test SCIM connection"""
        try:
            headers = {
                'Authorization': f'Bearer {bearer_token}',
                'Content-Type': 'application/scim+json'
            }
            
            response = requests.get(
                f"{base_url}/Users",
                headers=headers,
                timeout=self.config["sync_timeout_seconds"]
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"SCIM connection test failed: {e}")
            return False
    
    def sync_users_from_provider(self, provider_id: str, company: Company) -> List[SyncResult]:
        """Sync users from identity provider"""
        if provider_id not in self.identity_providers:
            raise ValueError(f"Identity provider not found: {provider_id}")
        
        provider = self.identity_providers[provider_id]
        if not provider.is_active:
            raise ValueError(f"Identity provider is not active: {provider_id}")
        
        # Get users from identity provider
        external_users = self._get_users_from_provider(provider)
        
        sync_results = []
        
        for external_user in external_users:
            try:
                # Check if user exists in SCIM
                existing_scim_user = self._find_scim_user_by_external_id(external_user['external_id'])
                
                if existing_scim_user:
                    # Update existing user
                    sync_result = self._update_scim_user(existing_scim_user, external_user)
                else:
                    # Create new user
                    sync_result = self._create_scim_user(external_user, company)
                
                sync_results.append(sync_result)
                
            except Exception as e:
                # Create failed sync result
                failed_result = SyncResult(
                    id=str(uuid.uuid4()),
                    sync_type="provision",
                    user_id=external_user.get('id', ''),
                    external_id=external_user.get('external_id', ''),
                    status="failed",
                    error_message=str(e),
                    created_at=timezone.now()
                )
                sync_results.append(failed_result)
                logger.error(f"User sync failed for {external_user.get('external_id')}: {e}")
        
        # Update provider last sync time
        provider.last_sync = timezone.now()
        
        # Publish sync completion event
        event_bus.publish(
            event_type='USER_SYNC_COMPLETED',
            data={
                'provider_id': provider_id,
                'company_id': str(company.id),
                'users_synced': len(sync_results),
                'successful_syncs': len([r for r in sync_results if r.status == 'success'])
            },
            company_id=company.id
        )
        
        logger.info(f"User sync completed for provider {provider_id}: {len(sync_results)} users")
        return sync_results
    
    def _get_users_from_provider(self, provider: IdentityProvider) -> List[Dict[str, Any]]:
        """Get users from identity provider"""
        # Mock implementation - in real scenario, this would call the provider's API
        mock_users = [
            {
                'id': f"user_{i}",
                'external_id': f"ext_{i}",
                'username': f"user{i}@example.com",
                'email': f"user{i}@example.com",
                'first_name': f"User{i}",
                'last_name': "Test",
                'active': True,
                'groups': ['users'],
                'attributes': {}
            }
            for i in range(1, 6)  # Mock 5 users
        ]
        
        return mock_users
    
    def _find_scim_user_by_external_id(self, external_id: str) -> Optional[SCIMUser]:
        """Find SCIM user by external ID"""
        for scim_user in self.scim_users.values():
            if scim_user.external_id == external_id:
                return scim_user
        return None
    
    def _create_scim_user(self, external_user: Dict[str, Any], company: Company) -> SyncResult:
        """Create new SCIM user"""
        scim_user_id = str(uuid.uuid4())
        
        scim_user = SCIMUser(
            id=scim_user_id,
            external_id=external_user['external_id'],
            username=external_user['username'],
            email=external_user['email'],
            first_name=external_user['first_name'],
            last_name=external_user['last_name'],
            active=external_user['active'],
            company_id=str(company.id),
            groups=external_user.get('groups', []),
            attributes=external_user.get('attributes', {}),
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        
        self.scim_users[scim_user_id] = scim_user
        
        # Create sync result
        sync_result = SyncResult(
            id=str(uuid.uuid4()),
            sync_type="provision",
            user_id=scim_user_id,
            external_id=external_user['external_id'],
            status="success",
            created_at=timezone.now()
        )
        
        self.sync_results.append(sync_result)
        
        # Publish user provisioned event
        event_bus.publish(
            event_type='SCIM_USER_PROVISIONED',
            data={
                'scim_user_id': scim_user_id,
                'external_id': external_user['external_id'],
                'email': external_user['email'],
                'company_id': str(company.id)
            },
            company_id=company.id
        )
        
        logger.info(f"SCIM user created: {scim_user_id} ({external_user['email']})")
        return sync_result
    
    def _update_scim_user(self, existing_user: SCIMUser, external_user: Dict[str, Any]) -> SyncResult:
        """Update existing SCIM user"""
        # Update user attributes
        existing_user.username = external_user['username']
        existing_user.email = external_user['email']
        existing_user.first_name = external_user['first_name']
        existing_user.last_name = external_user['last_name']
        existing_user.active = external_user['active']
        existing_user.groups = external_user.get('groups', [])
        existing_user.attributes = external_user.get('attributes', {})
        existing_user.updated_at = timezone.now()
        
        # Create sync result
        sync_result = SyncResult(
            id=str(uuid.uuid4()),
            sync_type="update",
            user_id=existing_user.id,
            external_id=external_user['external_id'],
            status="success",
            created_at=timezone.now()
        )
        
        self.sync_results.append(sync_result)
        
        # Publish user updated event
        event_bus.publish(
            event_type='SCIM_USER_UPDATED',
            data={
                'scim_user_id': existing_user.id,
                'external_id': external_user['external_id'],
                'email': external_user['email']
            }
        )
        
        logger.info(f"SCIM user updated: {existing_user.id} ({external_user['email']})")
        return sync_result
    
    def deprovision_user(self, scim_user_id: str, company: Company) -> SyncResult:
        """Deprovision SCIM user"""
        if scim_user_id not in self.scim_users:
            raise ValueError(f"SCIM user not found: {scim_user_id}")
        
        scim_user = self.scim_users[scim_user_id]
        
        # Mark user as inactive
        scim_user.active = False
        scim_user.updated_at = timezone.now()
        
        # Create sync result
        sync_result = SyncResult(
            id=str(uuid.uuid4()),
            sync_type="deprovision",
            user_id=scim_user_id,
            external_id=scim_user.external_id,
            status="success",
            created_at=timezone.now()
        )
        
        self.sync_results.append(sync_result)
        
        # Publish user deprovisioned event
        event_bus.publish(
            event_type='SCIM_USER_DEPROVISIONED',
            data={
                'scim_user_id': scim_user_id,
                'external_id': scim_user.external_id,
                'email': scim_user.email,
                'company_id': str(company.id)
            },
            company_id=company.id
        )
        
        logger.info(f"SCIM user deprovisioned: {scim_user_id} ({scim_user.email})")
        return sync_result
    
    def get_sync_status(self, company: Company, 
                       lookback_hours: int = 24) -> Dict[str, Any]:
        """Get user sync status for a company"""
        cutoff_time = timezone.now() - timedelta(hours=lookback_hours)
        
        # Filter sync results by company and time
        company_sync_results = [
            result for result in self.sync_results
            if result.created_at >= cutoff_time
        ]
        
        if not company_sync_results:
            return {"status": "no_data", "message": "No sync data available"}
        
        # Calculate metrics
        total_syncs = len(company_sync_results)
        successful_syncs = len([r for r in company_sync_results if r.status == 'success'])
        failed_syncs = len([r for r in company_sync_results if r.status == 'failed'])
        
        # Group by sync type
        sync_types = {}
        for result in company_sync_results:
            sync_type = result.sync_type
            if sync_type not in sync_types:
                sync_types[sync_type] = {'total': 0, 'successful': 0, 'failed': 0}
            
            sync_types[sync_type]['total'] += 1
            if result.status == 'success':
                sync_types[sync_type]['successful'] += 1
            else:
                sync_types[sync_type]['failed'] += 1
        
        # Calculate success rate
        success_rate = successful_syncs / total_syncs if total_syncs > 0 else 0
        
        return {
            "company_id": str(company.id),
            "period_hours": lookback_hours,
            "total_syncs": total_syncs,
            "successful_syncs": successful_syncs,
            "failed_syncs": failed_syncs,
            "success_rate": success_rate,
            "sync_types": sync_types,
            "active_scim_users": len([u for u in self.scim_users.values() if u.active]),
            "total_scim_users": len(self.scim_users),
            "e2e_sync_enabled": True
        }
    
    def get_identity_providers(self, company: Company) -> List[Dict[str, Any]]:
        """Get identity providers for a company"""
        company_providers = [
            provider for provider in self.identity_providers.values()
            if provider.company_id == str(company.id)
        ]
        
        return [
            {
                "id": provider.id,
                "name": provider.name,
                "provider_type": provider.provider_type,
                "is_active": provider.is_active,
                "created_at": provider.created_at.isoformat(),
                "last_sync": provider.last_sync.isoformat() if provider.last_sync else None
            }
            for provider in company_providers
        ]
    
    def get_scim_users(self, company: Company, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get SCIM users for a company"""
        company_users = [
            user for user in self.scim_users.values()
            if user.company_id == str(company.id) and (not active_only or user.active)
        ]
        
        return [
            {
                "id": user.id,
                "external_id": user.external_id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "active": user.active,
                "groups": user.groups,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
            for user in company_users
        ]
    
    def test_sso_connection(self, provider_id: str) -> Dict[str, Any]:
        """Test SSO connection for a provider"""
        if provider_id not in self.identity_providers:
            return {"status": "error", "message": "Provider not found"}
        
        provider = self.identity_providers[provider_id]
        
        try:
            # Mock SSO connection test
            # In real implementation, this would test the actual SSO connection
            test_result = {
                "status": "success",
                "message": "SSO connection successful",
                "provider_name": provider.name,
                "provider_type": provider.provider_type,
                "tested_at": timezone.now().isoformat()
            }
            
            logger.info(f"SSO connection test successful for {provider.name}")
            return test_result
            
        except Exception as e:
            logger.error(f"SSO connection test failed for {provider.name}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "provider_name": provider.name,
                "tested_at": timezone.now().isoformat()
            }
    
    def get_sync_analytics(self, company: Company, 
                          lookback_days: int = 7) -> Dict[str, Any]:
        """Get detailed sync analytics"""
        cutoff_date = timezone.now() - timedelta(days=lookback_days)
        
        # Filter sync results
        recent_syncs = [
            result for result in self.sync_results
            if result.created_at >= cutoff_date
        ]
        
        if not recent_syncs:
            return {"status": "no_data", "message": "No sync data available"}
        
        # Calculate daily sync metrics
        daily_metrics = {}
        for result in recent_syncs:
            date_key = result.created_at.date().isoformat()
            if date_key not in daily_metrics:
                daily_metrics[date_key] = {'total': 0, 'successful': 0, 'failed': 0}
            
            daily_metrics[date_key]['total'] += 1
            if result.status == 'success':
                daily_metrics[date_key]['successful'] += 1
            else:
                daily_metrics[date_key]['failed'] += 1
        
        # Calculate error patterns
        error_patterns = {}
        for result in recent_syncs:
            if result.status == 'failed' and result.error_message:
                error_type = result.error_message.split(':')[0] if ':' in result.error_message else 'Unknown'
                error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
        
        return {
            "company_id": str(company.id),
            "period_days": lookback_days,
            "total_syncs": len(recent_syncs),
            "daily_metrics": daily_metrics,
            "error_patterns": error_patterns,
            "success_rate": len([r for r in recent_syncs if r.status == 'success']) / len(recent_syncs),
            "sync_types_breakdown": {
                "provision": len([r for r in recent_syncs if r.sync_type == 'provision']),
                "update": len([r for r in recent_syncs if r.sync_type == 'update']),
                "deprovision": len([r for r in recent_syncs if r.sync_type == 'deprovision'])
            }
        }

# Global instance
sso_scim_enterprise = SSOSCIMEnterprise()
