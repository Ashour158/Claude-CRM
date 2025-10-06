# sharing/enforcement.py
# Sharing enforcement engine

from django.db.models import Q, QuerySet
from typing import Optional
from .models import SharingRule, RecordShare
from .predicate import PredicateEvaluator


class SharingEnforcer:
    """
    Enforces sharing rules on querysets.
    
    Enforcement logic (layered):
    1. Ownership check (owner_id or user_id field matches current user)
    2. Predicate-based rules (SharingRule with OR semantics)
    3. Explicit record shares (RecordShare)
    4. Default deny (empty queryset if none of the above match)
    """
    
    @classmethod
    def enforce_sharing(
        cls,
        queryset: QuerySet,
        user,
        company,
        object_type: str,
        ownership_field: str = 'owner'
    ) -> QuerySet:
        """
        Apply sharing enforcement to a queryset.
        
        Args:
            queryset: The base queryset to filter
            user: The current user
            company: The current company
            object_type: Type of object ('lead', 'deal', 'account', 'contact', 'activity')
            ownership_field: Field name for ownership check (default: 'owner')
            
        Returns:
            Filtered queryset containing only records the user can access
        """
        # Start with no access (default deny)
        access_q = Q(pk__in=[])
        
        # 1. Ownership check - user owns the record
        if ownership_field:
            ownership_q = Q(**{ownership_field: user})
            access_q |= ownership_q
        
        # 2. Rule-based access
        rules_q = cls._get_rules_q(company, object_type)
        if rules_q:
            access_q |= rules_q
        
        # 3. Explicit record shares
        shares_q = cls._get_shares_q(user, company, object_type, queryset.model)
        if shares_q:
            access_q |= shares_q
        
        return queryset.filter(access_q).distinct()
    
    @classmethod
    def _get_rules_q(cls, company, object_type: str) -> Optional[Q]:
        """
        Get Q object for all active sharing rules (OR semantics).
        """
        rules = SharingRule.objects.filter(
            company=company,
            object_type=object_type,
            is_active=True
        )
        
        if not rules.exists():
            return None
        
        combined_q = Q(pk__in=[])  # Start with empty
        
        for rule in rules:
            try:
                rule_q = PredicateEvaluator.evaluate(rule.predicate)
                combined_q |= rule_q
            except Exception as e:
                # Log error but don't fail - skip invalid rules
                print(f"Error evaluating rule {rule.id}: {e}")
                continue
        
        return combined_q if combined_q else None
    
    @classmethod
    def _get_shares_q(cls, user, company, object_type: str, model_class) -> Optional[Q]:
        """
        Get Q object for explicit record shares.
        """
        shares = RecordShare.objects.filter(
            company=company,
            object_type=object_type,
            user=user
        ).values_list('object_id', flat=True)
        
        if not shares:
            return None
        
        return Q(pk__in=list(shares))
    
    @classmethod
    def can_user_access_record(
        cls,
        user,
        company,
        record,
        object_type: str,
        ownership_field: str = 'owner'
    ) -> bool:
        """
        Check if a user can access a specific record.
        
        Args:
            user: The user to check
            company: The company context
            record: The record instance
            object_type: Type of object
            ownership_field: Field name for ownership check
            
        Returns:
            True if user has access, False otherwise
        """
        # Check ownership
        if ownership_field and hasattr(record, ownership_field):
            owner = getattr(record, ownership_field)
            if owner and owner.id == user.id:
                return True
        
        # Check rules
        rules = SharingRule.objects.filter(
            company=company,
            object_type=object_type,
            is_active=True
        )
        
        for rule in rules:
            try:
                rule_q = PredicateEvaluator.evaluate(rule.predicate)
                # Check if record matches this rule
                if record.__class__.objects.filter(pk=record.pk).filter(rule_q).exists():
                    return True
            except Exception:
                continue
        
        # Check explicit shares
        share_exists = RecordShare.objects.filter(
            company=company,
            object_type=object_type,
            object_id=record.pk,
            user=user
        ).exists()
        
        return share_exists
