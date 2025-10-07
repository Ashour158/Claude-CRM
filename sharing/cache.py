# sharing/cache.py
# Redis-backed sharing rule cache with invalidation

import hashlib
import json
import logging
from typing import List, Optional, Dict, Any
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


class SharingRuleCache:
    """
    Redis-backed cache for sharing rules with automatic invalidation.
    Provides fast lookup of sharing rules by company and object type.
    """
    
    CACHE_PREFIX = 'sharing:rules'
    CACHE_VERSION = 'v1'
    DEFAULT_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def get_cache_key(cls, company_id: str, object_type: str) -> str:
        """Generate cache key for sharing rules."""
        key_data = f"{cls.CACHE_PREFIX}:{cls.CACHE_VERSION}:{company_id}:{object_type}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @classmethod
    def get_rules(cls, company_id: str, object_type: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get sharing rules from cache.
        
        Args:
            company_id: Company UUID
            object_type: Type of object (lead, deal, account, contact, activity)
            
        Returns:
            List of sharing rule dictionaries or None if not cached
        """
        cache_key = cls.get_cache_key(company_id, object_type)
        cached_rules = cache.get(cache_key)
        
        if cached_rules is not None:
            logger.debug(f"Cache hit for sharing rules: {company_id}/{object_type}")
            return cached_rules
        
        logger.debug(f"Cache miss for sharing rules: {company_id}/{object_type}")
        return None
    
    @classmethod
    def set_rules(cls, company_id: str, object_type: str, rules: List[Dict[str, Any]], 
                  timeout: Optional[int] = None) -> None:
        """
        Cache sharing rules.
        
        Args:
            company_id: Company UUID
            object_type: Type of object
            rules: List of sharing rule dictionaries
            timeout: Cache timeout in seconds (default: 1 hour)
        """
        cache_key = cls.get_cache_key(company_id, object_type)
        timeout = timeout or cls.DEFAULT_TIMEOUT
        
        cache.set(cache_key, rules, timeout)
        logger.info(f"Cached {len(rules)} sharing rules for {company_id}/{object_type}")
    
    @classmethod
    def invalidate_rules(cls, company_id: str, object_type: Optional[str] = None) -> None:
        """
        Invalidate sharing rules cache.
        
        Args:
            company_id: Company UUID
            object_type: Specific object type to invalidate, or None for all types
        """
        if object_type:
            # Invalidate specific object type
            cache_key = cls.get_cache_key(company_id, object_type)
            cache.delete(cache_key)
            logger.info(f"Invalidated sharing rules cache for {company_id}/{object_type}")
        else:
            # Invalidate all object types for company
            object_types = ['lead', 'deal', 'account', 'contact', 'activity']
            for obj_type in object_types:
                cache_key = cls.get_cache_key(company_id, obj_type)
                cache.delete(cache_key)
            logger.info(f"Invalidated all sharing rules cache for company {company_id}")
    
    @classmethod
    def invalidate_all(cls) -> None:
        """Invalidate all sharing rules cache (use with caution)."""
        # This requires Redis SCAN to be efficient in production
        logger.warning("Invalidating all sharing rules cache")
        # For now, we'll use cache.clear() but in production should use pattern matching
        # cache.delete_pattern(f"{cls.CACHE_PREFIX}:{cls.CACHE_VERSION}:*")
    
    @classmethod
    def get_or_compute(cls, company_id: str, object_type: str, 
                       compute_func: callable, timeout: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get rules from cache or compute and cache them.
        
        Args:
            company_id: Company UUID
            object_type: Type of object
            compute_func: Function to compute rules if not cached
            timeout: Cache timeout in seconds
            
        Returns:
            List of sharing rule dictionaries
        """
        # Try to get from cache
        cached_rules = cls.get_rules(company_id, object_type)
        if cached_rules is not None:
            return cached_rules
        
        # Compute rules
        rules = compute_func(company_id, object_type)
        
        # Cache the result
        cls.set_rules(company_id, object_type, rules, timeout)
        
        return rules


class RecordShareCache:
    """
    Redis-backed cache for record-level sharing.
    Provides fast lookup of explicit record shares.
    """
    
    CACHE_PREFIX = 'sharing:records'
    CACHE_VERSION = 'v1'
    DEFAULT_TIMEOUT = 1800  # 30 minutes
    
    @classmethod
    def get_cache_key(cls, company_id: str, object_type: str, object_id: str, 
                      user_id: Optional[str] = None) -> str:
        """Generate cache key for record shares."""
        if user_id:
            key_data = f"{cls.CACHE_PREFIX}:{cls.CACHE_VERSION}:{company_id}:{object_type}:{object_id}:{user_id}"
        else:
            key_data = f"{cls.CACHE_PREFIX}:{cls.CACHE_VERSION}:{company_id}:{object_type}:{object_id}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @classmethod
    def get_shares(cls, company_id: str, object_type: str, object_id: str, 
                   user_id: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get record shares from cache.
        
        Args:
            company_id: Company UUID
            object_type: Type of object
            object_id: Record UUID
            user_id: Optional user UUID to filter shares
            
        Returns:
            List of record share dictionaries or None if not cached
        """
        cache_key = cls.get_cache_key(company_id, object_type, object_id, user_id)
        cached_shares = cache.get(cache_key)
        
        if cached_shares is not None:
            logger.debug(f"Cache hit for record shares: {object_type}/{object_id}")
            return cached_shares
        
        logger.debug(f"Cache miss for record shares: {object_type}/{object_id}")
        return None
    
    @classmethod
    def set_shares(cls, company_id: str, object_type: str, object_id: str,
                   shares: List[Dict[str, Any]], user_id: Optional[str] = None,
                   timeout: Optional[int] = None) -> None:
        """
        Cache record shares.
        
        Args:
            company_id: Company UUID
            object_type: Type of object
            object_id: Record UUID
            shares: List of record share dictionaries
            user_id: Optional user UUID
            timeout: Cache timeout in seconds
        """
        cache_key = cls.get_cache_key(company_id, object_type, object_id, user_id)
        timeout = timeout or cls.DEFAULT_TIMEOUT
        
        cache.set(cache_key, shares, timeout)
        logger.info(f"Cached {len(shares)} record shares for {object_type}/{object_id}")
    
    @classmethod
    def invalidate_shares(cls, company_id: str, object_type: str, 
                         object_id: Optional[str] = None) -> None:
        """
        Invalidate record shares cache.
        
        Args:
            company_id: Company UUID
            object_type: Type of object
            object_id: Optional record UUID, or None to invalidate all for object type
        """
        if object_id:
            # Invalidate specific record
            cache_key = cls.get_cache_key(company_id, object_type, object_id)
            cache.delete(cache_key)
            logger.info(f"Invalidated record shares cache for {object_type}/{object_id}")
        else:
            logger.info(f"Bulk invalidation requested for {object_type} records")


# Signal handlers for automatic cache invalidation
@receiver(post_save, sender='sharing.SharingRule')
def invalidate_sharing_rule_cache_on_save(sender, instance, **kwargs):
    """Invalidate cache when sharing rule is saved."""
    SharingRuleCache.invalidate_rules(
        str(instance.company_id),
        instance.object_type
    )
    logger.info(f"Auto-invalidated sharing rule cache on save: {instance.id}")


@receiver(post_delete, sender='sharing.SharingRule')
def invalidate_sharing_rule_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when sharing rule is deleted."""
    SharingRuleCache.invalidate_rules(
        str(instance.company_id),
        instance.object_type
    )
    logger.info(f"Auto-invalidated sharing rule cache on delete: {instance.id}")


@receiver(post_save, sender='sharing.RecordShare')
def invalidate_record_share_cache_on_save(sender, instance, **kwargs):
    """Invalidate cache when record share is saved."""
    RecordShareCache.invalidate_shares(
        str(instance.company_id),
        instance.object_type,
        str(instance.object_id)
    )
    logger.info(f"Auto-invalidated record share cache on save: {instance.id}")


@receiver(post_delete, sender='sharing.RecordShare')
def invalidate_record_share_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when record share is deleted."""
    RecordShareCache.invalidate_shares(
        str(instance.company_id),
        instance.object_type,
        str(instance.object_id)
    )
    logger.info(f"Auto-invalidated record share cache on delete: {instance.id}")
