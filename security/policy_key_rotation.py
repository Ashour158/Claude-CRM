# security/policy_key_rotation.py
"""
Policy Key Rotation Implementation
P1 Priority: Signed bundles 100% w/ new key

This module implements:
- Automated policy key rotation
- Bundle signing with new keys
- Key lifecycle management
- Rotation scheduling and validation
- Compliance tracking
"""

import logging
import hashlib
import hmac
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from core.models import Company, User
from events.event_bus import event_bus
import uuid
import base64
import secrets

logger = logging.getLogger(__name__)

@dataclass
class PolicyKey:
    """Policy key with metadata"""
    id: str
    key_name: str
    key_type: str
    key_value: str
    created_at: timezone.datetime
    expires_at: timezone.datetime
    is_active: bool
    rotation_count: int
    usage_count: int
    last_used: Optional[timezone.datetime]

@dataclass
class PolicyBundle:
    """Policy bundle with signing information"""
    id: str
    bundle_name: str
    bundle_content: Dict[str, Any]
    signature: str
    key_id: str
    signed_at: timezone.datetime
    version: str
    is_valid: bool
    validation_errors: List[str]

@dataclass
class RotationSchedule:
    """Key rotation schedule"""
    id: str
    key_name: str
    rotation_interval_days: int
    next_rotation: timezone.datetime
    auto_rotation: bool
    notification_days: List[int]  # Days before rotation to notify
    is_active: bool

class PolicyKeyRotation:
    """
    Policy key rotation with automated bundle signing
    """
    
    def __init__(self):
        self.policy_keys: Dict[str, PolicyKey] = {}
        self.policy_bundles: Dict[str, PolicyBundle] = {}
        self.rotation_schedules: Dict[str, RotationSchedule] = {}
        self.rotation_history: List[Dict[str, Any]] = []
        
        # Key rotation configuration
        self.rotation_config = {
            "default_rotation_days": 90,
            "key_length": 256,
            "signature_algorithm": "HMAC-SHA256",
            "bundle_validation": True,
            "auto_rotation": True
        }
    
    def create_policy_key(self, key_name: str, key_type: str = "HMAC",
                        rotation_interval_days: int = 90,
                        created_by: User = None) -> PolicyKey:
        """Create a new policy key"""
        key_id = str(uuid.uuid4())
        
        # Generate key value
        if key_type == "HMAC":
            key_value = base64.b64encode(secrets.token_bytes(self.rotation_config["key_length"] // 8)).decode()
        else:
            key_value = secrets.token_hex(self.rotation_config["key_length"] // 8)
        
        policy_key = PolicyKey(
            id=key_id,
            key_name=key_name,
            key_type=key_type,
            key_value=key_value,
            created_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=rotation_interval_days),
            is_active=True,
            rotation_count=0,
            usage_count=0,
            last_used=None
        )
        
        self.policy_keys[key_id] = policy_key
        
        # Create rotation schedule
        self._create_rotation_schedule(key_name, rotation_interval_days)
        
        # Publish key creation event
        event_bus.publish(
            event_type='POLICY_KEY_CREATED',
            data={
                'key_id': key_id,
                'key_name': key_name,
                'key_type': key_type,
                'rotation_interval_days': rotation_interval_days,
                'expires_at': policy_key.expires_at.isoformat()
            },
            actor=created_by,
            company_id=created_by.company.id if created_by else None
        )
        
        logger.info(f"Policy key created: {key_name} ({key_id})")
        return policy_key
    
    def _create_rotation_schedule(self, key_name: str, rotation_interval_days: int):
        """Create rotation schedule for a key"""
        schedule_id = str(uuid.uuid4())
        
        schedule = RotationSchedule(
            id=schedule_id,
            key_name=key_name,
            rotation_interval_days=rotation_interval_days,
            next_rotation=timezone.now() + timedelta(days=rotation_interval_days),
            auto_rotation=self.rotation_config["auto_rotation"],
            notification_days=[7, 3, 1],  # Notify 7, 3, and 1 days before rotation
            is_active=True
        )
        
        self.rotation_schedules[schedule_id] = schedule
        logger.info(f"Rotation schedule created for {key_name}: every {rotation_interval_days} days")
    
    def sign_policy_bundle(self, bundle_name: str, bundle_content: Dict[str, Any],
                          key_id: str, version: str = "1.0") -> PolicyBundle:
        """Sign a policy bundle with the specified key"""
        if key_id not in self.policy_keys:
            raise ValueError(f"Policy key not found: {key_id}")
        
        key = self.policy_keys[key_id]
        if not key.is_active:
            raise ValueError(f"Policy key is not active: {key_id}")
        
        # Create bundle signature
        bundle_json = json.dumps(bundle_content, sort_keys=True)
        signature = self._create_signature(bundle_json, key.key_value, key.key_type)
        
        # Create policy bundle
        bundle_id = str(uuid.uuid4())
        policy_bundle = PolicyBundle(
            id=bundle_id,
            bundle_name=bundle_name,
            bundle_content=bundle_content,
            signature=signature,
            key_id=key_id,
            signed_at=timezone.now(),
            version=version,
            is_valid=True,
            validation_errors=[]
        )
        
        self.policy_bundles[bundle_id] = policy_bundle
        
        # Update key usage
        key.usage_count += 1
        key.last_used = timezone.now()
        
        # Publish bundle signing event
        event_bus.publish(
            event_type='POLICY_BUNDLE_SIGNED',
            data={
                'bundle_id': bundle_id,
                'bundle_name': bundle_name,
                'key_id': key_id,
                'version': version,
                'signature': signature
            }
        )
        
        logger.info(f"Policy bundle signed: {bundle_name} with key {key_id}")
        return policy_bundle
    
    def _create_signature(self, content: str, key_value: str, key_type: str) -> str:
        """Create signature for content using the key"""
        if key_type == "HMAC":
            signature = hmac.new(
                key_value.encode(),
                content.encode(),
                hashlib.sha256
            ).hexdigest()
        else:
            # For other key types, use HMAC as fallback
            signature = hmac.new(
                key_value.encode(),
                content.encode(),
                hashlib.sha256
            ).hexdigest()
        
        return signature
    
    def validate_policy_bundle(self, bundle_id: str) -> Tuple[bool, List[str]]:
        """Validate a policy bundle signature"""
        if bundle_id not in self.policy_bundles:
            return False, ["Bundle not found"]
        
        bundle = self.policy_bundles[bundle_id]
        key_id = bundle.key_id
        
        if key_id not in self.policy_keys:
            return False, ["Key not found"]
        
        key = self.policy_keys[key_id]
        if not key.is_active:
            return False, ["Key is not active"]
        
        # Recreate signature
        bundle_json = json.dumps(bundle.bundle_content, sort_keys=True)
        expected_signature = self._create_signature(bundle_json, key.key_value, key.key_type)
        
        # Validate signature
        if bundle.signature != expected_signature:
            bundle.is_valid = False
            bundle.validation_errors.append("Invalid signature")
            return False, ["Invalid signature"]
        
        # Check key expiration
        if key.expires_at < timezone.now():
            bundle.is_valid = False
            bundle.validation_errors.append("Key expired")
            return False, ["Key expired"]
        
        bundle.is_valid = True
        bundle.validation_errors = []
        return True, []
    
    def rotate_policy_key(self, key_id: str, rotated_by: User = None) -> PolicyKey:
        """Rotate a policy key"""
        if key_id not in self.policy_keys:
            raise ValueError(f"Policy key not found: {key_id}")
        
        old_key = self.policy_keys[key_id]
        
        # Create new key
        new_key = PolicyKey(
            id=str(uuid.uuid4()),
            key_name=old_key.key_name,
            key_type=old_key.key_type,
            key_value=base64.b64encode(secrets.token_bytes(self.rotation_config["key_length"] // 8)).decode(),
            created_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=old_key.expires_at - old_key.created_at).days,
            is_active=True,
            rotation_count=old_key.rotation_count + 1,
            usage_count=0,
            last_used=None
        )
        
        # Deactivate old key
        old_key.is_active = False
        
        # Add new key
        self.policy_keys[new_key.id] = new_key
        
        # Update rotation schedule
        self._update_rotation_schedule(old_key.key_name)
        
        # Record rotation history
        rotation_record = {
            "id": str(uuid.uuid4()),
            "old_key_id": key_id,
            "new_key_id": new_key.id,
            "key_name": old_key.key_name,
            "rotated_at": timezone.now().isoformat(),
            "rotated_by": str(rotated_by.id) if rotated_by else None,
            "rotation_count": new_key.rotation_count
        }
        self.rotation_history.append(rotation_record)
        
        # Re-sign all bundles with old key using new key
        self._resign_bundles_with_new_key(key_id, new_key.id)
        
        # Publish rotation event
        event_bus.publish(
            event_type='POLICY_KEY_ROTATED',
            data={
                'old_key_id': key_id,
                'new_key_id': new_key.id,
                'key_name': old_key.key_name,
                'rotation_count': new_key.rotation_count,
                'bundles_updated': len([b for b in self.policy_bundles.values() if b.key_id == key_id])
            },
            actor=rotated_by,
            company_id=rotated_by.company.id if rotated_by else None
        )
        
        logger.info(f"Policy key rotated: {old_key.key_name} ({key_id} -> {new_key.id})")
        return new_key
    
    def _update_rotation_schedule(self, key_name: str):
        """Update rotation schedule for a key"""
        for schedule in self.rotation_schedules.values():
            if schedule.key_name == key_name:
                schedule.next_rotation = timezone.now() + timedelta(days=schedule.rotation_interval_days)
                break
    
    def _resign_bundles_with_new_key(self, old_key_id: str, new_key_id: str):
        """Re-sign all bundles that were signed with the old key"""
        bundles_to_update = [
            bundle for bundle in self.policy_bundles.values()
            if bundle.key_id == old_key_id
        ]
        
        for bundle in bundles_to_update:
            # Re-sign with new key
            bundle_json = json.dumps(bundle.bundle_content, sort_keys=True)
            new_signature = self._create_signature(
                bundle_json, 
                self.policy_keys[new_key_id].key_value,
                self.policy_keys[new_key_id].key_type
            )
            
            bundle.signature = new_signature
            bundle.key_id = new_key_id
            bundle.signed_at = timezone.now()
            bundle.is_valid = True
            bundle.validation_errors = []
            
            logger.info(f"Bundle {bundle.bundle_name} re-signed with new key {new_key_id}")
    
    def check_rotation_schedules(self) -> List[Dict[str, Any]]:
        """Check for keys that need rotation"""
        now = timezone.now()
        keys_to_rotate = []
        
        for schedule in self.rotation_schedules.values():
            if not schedule.is_active:
                continue
            
            # Check if rotation is due
            if now >= schedule.next_rotation:
                # Find the key
                key = next((k for k in self.policy_keys.values() 
                          if k.key_name == schedule.key_name and k.is_active), None)
                
                if key:
                    keys_to_rotate.append({
                        "schedule_id": schedule.id,
                        "key_id": key.id,
                        "key_name": key.key_name,
                        "rotation_due": True,
                        "next_rotation": schedule.next_rotation.isoformat()
                    })
            
            # Check for notification periods
            days_until_rotation = (schedule.next_rotation - now).days
            if days_until_rotation in schedule.notification_days:
                key = next((k for k in self.policy_keys.values() 
                          if k.key_name == schedule.key_name and k.is_active), None)
                
                if key:
                    keys_to_rotate.append({
                        "schedule_id": schedule.id,
                        "key_id": key.id,
                        "key_name": key.key_name,
                        "rotation_due": False,
                        "notification": True,
                        "days_until_rotation": days_until_rotation
                    })
        
        return keys_to_rotate
    
    def auto_rotate_keys(self) -> List[Dict[str, Any]]:
        """Automatically rotate keys that are due"""
        rotation_results = []
        keys_to_rotate = self.check_rotation_schedules()
        
        for key_info in keys_to_rotate:
            if key_info.get("rotation_due", False):
                try:
                    new_key = self.rotate_policy_key(key_info["key_id"])
                    rotation_results.append({
                        "key_name": key_info["key_name"],
                        "old_key_id": key_info["key_id"],
                        "new_key_id": new_key.id,
                        "status": "success",
                        "rotated_at": timezone.now().isoformat()
                    })
                except Exception as e:
                    rotation_results.append({
                        "key_name": key_info["key_name"],
                        "key_id": key_info["key_id"],
                        "status": "failed",
                        "error": str(e),
                        "rotated_at": timezone.now().isoformat()
                    })
        
        return rotation_results
    
    def get_rotation_status(self) -> Dict[str, Any]:
        """Get overall rotation status"""
        total_keys = len(self.policy_keys)
        active_keys = len([k for k in self.policy_keys.values() if k.is_active])
        expired_keys = len([k for k in self.policy_keys.values() 
                          if k.expires_at < timezone.now()])
        
        # Check bundles signed with new keys
        total_bundles = len(self.policy_bundles)
        valid_bundles = len([b for b in self.policy_bundles.values() if b.is_valid])
        
        # Calculate signing success rate
        signing_success_rate = (valid_bundles / total_bundles * 100) if total_bundles > 0 else 100
        
        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "expired_keys": expired_keys,
            "total_bundles": total_bundles,
            "valid_bundles": valid_bundles,
            "signing_success_rate": signing_success_rate,
            "target_met": signing_success_rate >= 100,  # 100% signed bundles target
            "rotation_history_count": len(self.rotation_history),
            "schedules_active": len([s for s in self.rotation_schedules.values() if s.is_active])
        }
    
    def get_key_lifecycle_report(self, key_id: str) -> Dict[str, Any]:
        """Get lifecycle report for a specific key"""
        if key_id not in self.policy_keys:
            return {"error": "Key not found"}
        
        key = self.policy_keys[key_id]
        
        # Get bundles signed with this key
        key_bundles = [b for b in self.policy_bundles.values() if b.key_id == key_id]
        
        # Get rotation history for this key
        key_rotations = [r for r in self.rotation_history if r["old_key_id"] == key_id or r["new_key_id"] == key_id]
        
        return {
            "key_id": key_id,
            "key_name": key.key_name,
            "key_type": key.key_type,
            "created_at": key.created_at.isoformat(),
            "expires_at": key.expires_at.isoformat(),
            "is_active": key.is_active,
            "rotation_count": key.rotation_count,
            "usage_count": key.usage_count,
            "last_used": key.last_used.isoformat() if key.last_used else None,
            "bundles_signed": len(key_bundles),
            "valid_bundles": len([b for b in key_bundles if b.is_valid]),
            "rotation_history": key_rotations,
            "days_until_expiry": (key.expires_at - timezone.now()).days if key.is_active else 0
        }

# Global instance
policy_key_rotation = PolicyKeyRotation()
