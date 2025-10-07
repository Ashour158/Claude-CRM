# territories/auto_rebalance.py
# Territory Auto-Rebalance and Quota-Based Assignment Engine

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from celery import shared_task

from .models import Territory
from core.models import User, Company
from crm.models import Lead, Deal, Account

logger = logging.getLogger(__name__)

class TerritoryAutoRebalanceEngine:
    """
    Advanced territory auto-rebalance engine that optimizes territory assignments
    based on workload, performance, and quota requirements.
    """
    
    def __init__(self):
        self.rebalance_strategies = {
            'workload_balanced': self._rebalance_by_workload,
            'performance_optimized': self._rebalance_by_performance,
            'quota_based': self._rebalance_by_quota,
            'geographic_optimized': self._rebalance_by_geography,
            'hybrid': self._rebalance_hybrid
        }
    
    def rebalance_territories(self, company_id: str, strategy: str = 'hybrid') -> Dict[str, Any]:
        """
        Rebalance territories for a company using the specified strategy.
        """
        try:
            company = Company.objects.get(id=company_id)
            strategy_func = self.rebalance_strategies.get(strategy)
            
            if not strategy_func:
                raise ValueError(f"Unknown rebalance strategy: {strategy}")
            
            # Get current territory assignments
            current_assignments = self._get_current_assignments(company)
            
            # Calculate optimal assignments
            optimal_assignments = strategy_func(company, current_assignments)
            
            # Apply rebalancing
            rebalance_results = self._apply_rebalancing(company, optimal_assignments)
            
            # Update territory statistics
            self._update_territory_stats(company)
            
            return {
                'status': 'success',
                'strategy': strategy,
                'rebalanced_territories': len(rebalance_results),
                'assignments_changed': sum(1 for r in rebalance_results if r['changed']),
                'results': rebalance_results
            }
            
        except Exception as e:
            logger.error(f"Territory rebalancing failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_current_assignments(self, company: Company) -> Dict[str, List[Dict]]:
        """Get current territory assignments"""
        assignments = {}
        
        territories = Territory.objects.filter(company=company, is_active=True)
        
        for territory in territories:
            users = territory.get_all_users()
            assignments[str(territory.id)] = [
                {
                    'user_id': str(user.id),
                    'user_name': user.get_full_name(),
                    'workload': self._calculate_user_workload(user),
                    'performance': self._calculate_user_performance(user),
                    'quota_progress': self._calculate_quota_progress(user, territory)
                }
                for user in users
            ]
        
        return assignments
    
    def _rebalance_by_workload(self, company: Company, current_assignments: Dict) -> Dict[str, List[str]]:
        """Rebalance territories based on workload distribution"""
        # Calculate total workload across all territories
        total_workload = 0
        territory_workloads = {}
        
        for territory_id, users in current_assignments.items():
            territory_workload = sum(user['workload'] for user in users)
            territory_workloads[territory_id] = territory_workload
            total_workload += territory_workload
        
        # Calculate target workload per territory
        num_territories = len(territory_workloads)
        target_workload = total_workload / num_territories if num_territories > 0 else 0
        
        # Rebalance assignments
        optimal_assignments = {}
        
        for territory_id, users in current_assignments.items():
            current_workload = territory_workloads[territory_id]
            
            if current_workload > target_workload * 1.2:  # Overloaded
                # Move some users to other territories
                optimal_assignments[territory_id] = self._reduce_territory_workload(
                    users, current_workload, target_workload
                )
            elif current_workload < target_workload * 0.8:  # Underloaded
                # Add users from other territories
                optimal_assignments[territory_id] = self._increase_territory_workload(
                    users, current_workload, target_workload, current_assignments
                )
            else:
                # Keep current assignments
                optimal_assignments[territory_id] = [user['user_id'] for user in users]
        
        return optimal_assignments
    
    def _rebalance_by_performance(self, company: Company, current_assignments: Dict) -> Dict[str, List[str]]:
        """Rebalance territories based on performance optimization"""
        # Calculate performance scores for all users
        user_performance = {}
        
        for territory_id, users in current_assignments.items():
            for user in users:
                user_performance[user['user_id']] = user['performance']
        
        # Sort users by performance
        sorted_users = sorted(
            user_performance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Assign top performers to high-value territories
        optimal_assignments = {}
        
        for territory_id, users in current_assignments.items():
            territory = Territory.objects.get(id=territory_id)
            territory_value = self._calculate_territory_value(territory)
            
            if territory_value > 0.8:  # High-value territory
                # Assign top performers
                optimal_assignments[territory_id] = [
                    user_id for user_id, _ in sorted_users[:len(users)]
                ]
            else:
                # Keep current assignments for lower-value territories
                optimal_assignments[territory_id] = [user['user_id'] for user in users]
        
        return optimal_assignments
    
    def _rebalance_by_quota(self, company: Company, current_assignments: Dict) -> Dict[str, List[str]]:
        """Rebalance territories based on quota requirements"""
        optimal_assignments = {}
        
        for territory_id, users in current_assignments.items():
            territory = Territory.objects.get(id=territory_id)
            quota_amount = territory.quota_amount or 0
            
            if quota_amount > 0:
                # Calculate required users based on quota
                required_users = self._calculate_required_users_for_quota(quota_amount)
                
                # Select best users for this quota
                selected_users = self._select_users_for_quota(users, required_users)
                optimal_assignments[territory_id] = [user['user_id'] for user in selected_users]
            else:
                # Keep current assignments for territories without quotas
                optimal_assignments[territory_id] = [user['user_id'] for user in users]
        
        return optimal_assignments
    
    def _rebalance_by_geography(self, company: Company, current_assignments: Dict) -> Dict[str, List[str]]:
        """Rebalance territories based on geographic optimization"""
        optimal_assignments = {}
        
        for territory_id, users in current_assignments.items():
            territory = Territory.objects.get(id=territory_id)
            
            # Get geographic criteria
            countries = territory.countries or []
            states = territory.states or []
            cities = territory.cities or []
            
            # Find users in the same geographic area
            geographic_users = self._find_users_by_geography(countries, states, cities)
            
            if geographic_users:
                optimal_assignments[territory_id] = geographic_users
            else:
                # Keep current assignments if no geographic match
                optimal_assignments[territory_id] = [user['user_id'] for user in users]
        
        return optimal_assignments
    
    def _rebalance_hybrid(self, company: Company, current_assignments: Dict) -> Dict[str, List[str]]:
        """Hybrid rebalancing strategy combining multiple factors"""
        # Get individual strategy results
        workload_result = self._rebalance_by_workload(company, current_assignments)
        performance_result = self._rebalance_by_performance(company, current_assignments)
        quota_result = self._rebalance_by_quota(company, current_assignments)
        geography_result = self._rebalance_by_geography(company, current_assignments)
        
        # Combine results with weights
        weights = {
            'workload': 0.3,
            'performance': 0.3,
            'quota': 0.2,
            'geography': 0.2
        }
        
        optimal_assignments = {}
        
        for territory_id in current_assignments.keys():
            # Calculate weighted score for each user assignment
            user_scores = {}
            
            for user in current_assignments[territory_id]:
                user_id = user['user_id']
                score = 0
                
                # Workload score (lower is better)
                if user_id in workload_result.get(territory_id, []):
                    score += weights['workload'] * 1.0
                
                # Performance score (higher is better)
                if user_id in performance_result.get(territory_id, []):
                    score += weights['performance'] * user['performance']
                
                # Quota score
                if user_id in quota_result.get(territory_id, []):
                    score += weights['quota'] * 1.0
                
                # Geography score
                if user_id in geography_result.get(territory_id, []):
                    score += weights['geography'] * 1.0
                
                user_scores[user_id] = score
            
            # Select users with highest scores
            sorted_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
            optimal_assignments[territory_id] = [user_id for user_id, _ in sorted_users]
        
        return optimal_assignments
    
    def _calculate_user_workload(self, user: User) -> float:
        """Calculate user's current workload"""
        # Count active leads, deals, and tasks
        active_leads = Lead.objects.filter(
            company=user.company,
            assigned_to=user,
            status__in=['new', 'contacted', 'qualified']
        ).count()
        
        active_deals = Deal.objects.filter(
            company=user.company,
            assigned_to=user,
            stage__in=['prospecting', 'qualification', 'proposal', 'negotiation']
        ).count()
        
        # Weight different types of work
        workload = (active_leads * 1.0) + (active_deals * 2.0)
        
        return workload
    
    def _calculate_user_performance(self, user: User) -> float:
        """Calculate user's performance score"""
        # Get performance metrics for the last 90 days
        start_date = timezone.now() - timedelta(days=90)
        
        # Calculate conversion rates
        total_leads = Lead.objects.filter(
            company=user.company,
            assigned_to=user,
            created_at__gte=start_date
        ).count()
        
        converted_leads = Lead.objects.filter(
            company=user.company,
            assigned_to=user,
            created_at__gte=start_date,
            status='converted'
        ).count()
        
        conversion_rate = converted_leads / total_leads if total_leads > 0 else 0
        
        # Calculate deal closure rate
        total_deals = Deal.objects.filter(
            company=user.company,
            assigned_to=user,
            created_at__gte=start_date
        ).count()
        
        closed_deals = Deal.objects.filter(
            company=user.company,
            assigned_to=user,
            created_at__gte=start_date,
            stage='closed_won'
        ).count()
        
        closure_rate = closed_deals / total_deals if total_deals > 0 else 0
        
        # Calculate average deal value
        avg_deal_value = Deal.objects.filter(
            company=user.company,
            assigned_to=user,
            created_at__gte=start_date,
            stage='closed_won'
        ).aggregate(avg_value=models.Avg('amount'))['avg_value'] or 0
        
        # Combine metrics into performance score
        performance_score = (
            conversion_rate * 0.4 +
            closure_rate * 0.4 +
            min(avg_deal_value / 10000, 1.0) * 0.2  # Normalize deal value
        )
        
        return performance_score
    
    def _calculate_quota_progress(self, user: User, territory: Territory) -> float:
        """Calculate user's quota progress"""
        if not territory.quota_amount:
            return 0.0
        
        # Calculate current progress for the quota period
        quota_period = territory.quota_period or 'monthly'
        
        if quota_period == 'monthly':
            start_date = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif quota_period == 'quarterly':
            quarter = (timezone.now().month - 1) // 3
            start_date = timezone.now().replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # yearly
            start_date = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate closed won deals value
        closed_deals_value = Deal.objects.filter(
            company=user.company,
            assigned_to=user,
            stage='closed_won',
            closed_at__gte=start_date
        ).aggregate(total_value=models.Sum('amount'))['total_value'] or 0
        
        progress = closed_deals_value / territory.quota_amount
        return min(progress, 1.0)  # Cap at 100%
    
    def _calculate_territory_value(self, territory: Territory) -> float:
        """Calculate territory value score"""
        # Get territory statistics
        accounts_count = territory.accounts_count or 0
        leads_count = territory.leads_count or 0
        deals_count = territory.deals_count or 0
        total_deal_value = territory.total_deal_value or 0
        
        # Calculate value score (0-1)
        value_score = min(
            (accounts_count * 0.1 + leads_count * 0.2 + deals_count * 0.3 + total_deal_value / 100000) / 10,
            1.0
        )
        
        return value_score
    
    def _calculate_required_users_for_quota(self, quota_amount: float) -> int:
        """Calculate required number of users for a quota"""
        # Assume average user can handle $50,000 quota per month
        avg_user_capacity = 50000
        required_users = max(1, int(quota_amount / avg_user_capacity))
        return required_users
    
    def _select_users_for_quota(self, users: List[Dict], required_count: int) -> List[Dict]:
        """Select best users for quota assignment"""
        # Sort users by performance and quota progress
        sorted_users = sorted(
            users,
            key=lambda x: (x['performance'], 1 - x['quota_progress']),
            reverse=True
        )
        
        return sorted_users[:required_count]
    
    def _find_users_by_geography(self, countries: List[str], states: List[str], cities: List[str]) -> List[str]:
        """Find users by geographic criteria"""
        # This would require additional user location data
        # For now, return empty list as placeholder
        return []
    
    def _reduce_territory_workload(self, users: List[Dict], current_workload: float, target_workload: float) -> List[str]:
        """Reduce territory workload by removing users"""
        # Calculate how many users to remove
        excess_workload = current_workload - target_workload
        users_to_remove = int(excess_workload / 10)  # Assume 10 workload units per user
        
        # Remove users with lowest performance
        sorted_users = sorted(users, key=lambda x: x['performance'])
        remaining_users = sorted_users[users_to_remove:]
        
        return [user['user_id'] for user in remaining_users]
    
    def _increase_territory_workload(self, users: List[Dict], current_workload: float, target_workload: float, all_assignments: Dict) -> List[str]:
        """Increase territory workload by adding users"""
        # Calculate how many users to add
        needed_workload = target_workload - current_workload
        users_to_add = int(needed_workload / 10)  # Assume 10 workload units per user
        
        # Find available users from other territories
        available_users = []
        for territory_id, territory_users in all_assignments.items():
            if len(territory_users) > 1:  # Don't take the last user from a territory
                available_users.extend(territory_users[:-1])
        
        # Select best available users
        sorted_available = sorted(available_users, key=lambda x: x['performance'], reverse=True)
        selected_users = sorted_available[:users_to_add]
        
        # Combine with current users
        current_user_ids = [user['user_id'] for user in users]
        new_user_ids = [user['user_id'] for user in selected_users]
        
        return current_user_ids + new_user_ids
    
    def _apply_rebalancing(self, company: Company, optimal_assignments: Dict[str, List[str]]) -> List[Dict]:
        """Apply the rebalancing changes"""
        results = []
        
        for territory_id, user_ids in optimal_assignments.items():
            try:
                territory = Territory.objects.get(id=territory_id)
                current_users = territory.get_all_users()
                current_user_ids = [str(user.id) for user in current_users]
                
                # Check if assignments changed
                changed = set(current_user_ids) != set(user_ids)
                
                if changed:
                    # Update territory assignments
                    with transaction.atomic():
                        # Clear current assignments
                        territory.users.clear()
                        
                        # Add new assignments
                        for user_id in user_ids:
                            try:
                                user = User.objects.get(id=user_id, company=company)
                                territory.users.add(user)
                            except User.DoesNotExist:
                                logger.warning(f"User not found: {user_id}")
                
                results.append({
                    'territory_id': territory_id,
                    'territory_name': territory.name,
                    'changed': changed,
                    'previous_users': len(current_users),
                    'new_users': len(user_ids)
                })
                
            except Territory.DoesNotExist:
                logger.error(f"Territory not found: {territory_id}")
                results.append({
                    'territory_id': territory_id,
                    'territory_name': 'Unknown',
                    'changed': False,
                    'error': 'Territory not found'
                })
        
        return results
    
    def _update_territory_stats(self, company: Company):
        """Update territory statistics after rebalancing"""
        territories = Territory.objects.filter(company=company, is_active=True)
        
        for territory in territories:
            # Update user count
            territory.users_count = territory.users.count()
            
            # Update other statistics
            territory.accounts_count = Account.objects.filter(
                company=company,
                assigned_to__in=territory.users.all()
            ).count()
            
            territory.leads_count = Lead.objects.filter(
                company=company,
                assigned_to__in=territory.users.all()
            ).count()
            
            territory.deals_count = Deal.objects.filter(
                company=company,
                assigned_to__in=territory.users.all()
            ).count()
            
            territory.total_deal_value = Deal.objects.filter(
                company=company,
                assigned_to__in=territory.users.all(),
                stage='closed_won'
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            territory.save()

# Celery tasks for async processing
@shared_task
def auto_rebalance_territories(company_id: str, strategy: str = 'hybrid'):
    """Celery task to auto-rebalance territories"""
    engine = TerritoryAutoRebalanceEngine()
    return engine.rebalance_territories(company_id, strategy)

@shared_task
def schedule_territory_rebalancing():
    """Scheduled task to rebalance territories"""
    companies = Company.objects.filter(is_active=True)
    
    for company in companies:
        try:
            auto_rebalance_territories.delay(str(company.id), 'hybrid')
            logger.info(f"Scheduled territory rebalancing for company: {company.name}")
        except Exception as e:
            logger.error(f"Failed to schedule rebalancing for company {company.name}: {str(e)}")
