# compliance/access_review.py
# Automated access review engine

from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Max
from .models import AccessReview, StaleAccess


class AccessReviewEngine:
    """Engine for automated access reviews"""
    
    # Configuration
    STALE_ACCESS_THRESHOLD_DAYS = 90  # 90 days of inactivity
    
    def create_review(self, company) -> AccessReview:
        """
        Create a new access review
        
        Args:
            company: Company instance
            
        Returns:
            AccessReview instance
        """
        # Calculate review period (last quarter)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)
        
        review = AccessReview.objects.create(
            company=company,
            review_period_start=start_date,
            review_period_end=end_date,
            status='pending'
        )
        
        return review
    
    def run_review(self, review: AccessReview) -> dict:
        """
        Run access review
        
        Args:
            review: AccessReview instance
            
        Returns:
            Dictionary with review results
        """
        result = {
            'total_users': 0,
            'stale_access_found': 0,
            'details': []
        }
        
        # Update status
        review.status = 'in_progress'
        review.save()
        
        try:
            # Check user access
            result = self._review_user_access(review)
            
            # Check role assignments
            role_result = self._review_role_assignments(review)
            result['role_review'] = role_result
            
            # Update review
            review.status = 'completed'
            review.total_users_reviewed = result['total_users']
            review.stale_access_found = result['stale_access_found']
            review.review_data = result
            review.completed_at = timezone.now()
            review.save()
        
        except Exception as e:
            review.status = 'pending'
            review.save()
            raise
        
        return result
    
    def _review_user_access(self, review: AccessReview) -> dict:
        """Review user access patterns"""
        from core.models import UserCompanyAccess, User
        from django.contrib.auth import get_user_model
        
        result = {
            'total_users': 0,
            'stale_access_found': 0,
            'details': []
        }
        
        # Get all users with access to this company
        user_accesses = UserCompanyAccess.objects.filter(
            company=review.company,
            is_active=True
        ).select_related('user')
        
        result['total_users'] = user_accesses.count()
        
        # Check each user's last activity
        cutoff_date = timezone.now() - timedelta(days=self.STALE_ACCESS_THRESHOLD_DAYS)
        
        for access in user_accesses:
            user = access.user
            
            # Check last login
            last_activity = user.last_login
            
            if not last_activity or last_activity < cutoff_date:
                # Stale access detected
                days_inactive = (timezone.now() - last_activity).days if last_activity else 999
                
                stale = StaleAccess.objects.create(
                    access_review=review,
                    company=review.company,
                    user=user,
                    resource_type='company_access',
                    resource_id=str(access.id),
                    last_accessed=last_activity,
                    days_inactive=days_inactive
                )
                
                result['stale_access_found'] += 1
                result['details'].append({
                    'user': user.email,
                    'days_inactive': days_inactive,
                    'resource': 'company_access'
                })
        
        return result
    
    def _review_role_assignments(self, review: AccessReview) -> dict:
        """Review role assignments"""
        from core.models import UserCompanyAccess
        
        result = {
            'total_roles': 0,
            'excessive_permissions': [],
            'details': []
        }
        
        # Get all role assignments
        accesses = UserCompanyAccess.objects.filter(
            company=review.company,
            is_active=True
        ).select_related('user')
        
        result['total_roles'] = accesses.count()
        
        # Check for admin roles
        admin_count = accesses.filter(role='admin').count()
        if admin_count > 5:  # Threshold for admin users
            result['excessive_permissions'].append({
                'role': 'admin',
                'count': admin_count,
                'recommendation': 'Review admin role assignments'
            })
        
        return result


class StaleAccessResolver:
    """Utility to resolve stale access"""
    
    def revoke_access(self, stale_access: StaleAccess) -> bool:
        """
        Revoke stale access
        
        Args:
            stale_access: StaleAccess instance
            
        Returns:
            True if successful
        """
        from core.models import UserCompanyAccess
        
        try:
            # Find and deactivate the access
            if stale_access.resource_type == 'company_access':
                access = UserCompanyAccess.objects.get(id=stale_access.resource_id)
                access.is_active = False
                access.save()
            
            # Mark as resolved
            stale_access.resolution = 'revoked'
            stale_access.is_resolved = True
            stale_access.resolved_at = timezone.now()
            stale_access.save()
            
            return True
        
        except Exception:
            return False
    
    def retain_access(self, stale_access: StaleAccess, reason: str = None) -> bool:
        """
        Retain stale access with justification
        
        Args:
            stale_access: StaleAccess instance
            reason: Justification for retention
            
        Returns:
            True if successful
        """
        try:
            stale_access.resolution = 'retained'
            stale_access.is_resolved = True
            stale_access.resolved_at = timezone.now()
            stale_access.save()
            
            return True
        
        except Exception:
            return False
