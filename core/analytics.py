# core/analytics.py
# Advanced analytics for Phase 9

from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Advanced analytics service"""
    
    @staticmethod
    def get_dashboard_metrics(company, user=None, days=30):
        """Get dashboard metrics for the last N days"""
        from crm.models import Lead, Account, Contact
        from deals.models import Deal
        from activities.models import Activity, Task
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Base queryset for company
        leads_qs = Lead.objects.filter(company=company, created_at__gte=start_date)
        accounts_qs = Account.objects.filter(company=company, created_at__gte=start_date)
        contacts_qs = Contact.objects.filter(company=company, created_at__gte=start_date)
        deals_qs = Deal.objects.filter(company=company, created_at__gte=start_date)
        activities_qs = Activity.objects.filter(company=company, created_at__gte=start_date)
        tasks_qs = Task.objects.filter(company=company, created_at__gte=start_date)
        
        # Filter by user if specified
        if user:
            leads_qs = leads_qs.filter(owner=user)
            accounts_qs = accounts_qs.filter(owner=user)
            contacts_qs = contacts_qs.filter(owner=user)
            deals_qs = deals_qs.filter(owner=user)
            activities_qs = activities_qs.filter(owner=user)
            tasks_qs = tasks_qs.filter(owner=user)
        
        # Calculate metrics
        metrics = {
            'leads': {
                'total': leads_qs.count(),
                'new': leads_qs.filter(status='new').count(),
                'qualified': leads_qs.filter(status='qualified').count(),
                'converted': leads_qs.filter(status='converted').count(),
            },
            'accounts': {
                'total': accounts_qs.count(),
                'active': accounts_qs.filter(status='active').count(),
            },
            'contacts': {
                'total': contacts_qs.count(),
            },
            'deals': {
                'total': deals_qs.count(),
                'total_value': deals_qs.aggregate(Sum('amount'))['amount__sum'] or 0,
                'average_value': deals_qs.aggregate(Avg('amount'))['amount__avg'] or 0,
                'won': deals_qs.filter(stage='closed_won').count(),
                'lost': deals_qs.filter(stage='closed_lost').count(),
                'open': deals_qs.exclude(stage__in=['closed_won', 'closed_lost']).count(),
            },
            'activities': {
                'total': activities_qs.count(),
                'calls': activities_qs.filter(activity_type='call').count(),
                'meetings': activities_qs.filter(activity_type='meeting').count(),
                'emails': activities_qs.filter(activity_type='email').count(),
            },
            'tasks': {
                'total': tasks_qs.count(),
                'pending': tasks_qs.filter(status='pending').count(),
                'completed': tasks_qs.filter(status='completed').count(),
                'overdue': tasks_qs.filter(
                    status='pending',
                    due_date__lt=timezone.now()
                ).count(),
            },
        }
        
        return metrics
    
    @staticmethod
    def get_sales_pipeline(company, user=None):
        """Get sales pipeline analysis"""
        from deals.models import Deal
        
        deals_qs = Deal.objects.filter(company=company)
        if user:
            deals_qs = deals_qs.filter(owner=user)
        
        pipeline = deals_qs.values('stage').annotate(
            count=Count('id'),
            total_value=Sum('amount'),
            avg_value=Avg('amount')
        ).order_by('stage')
        
        return list(pipeline)
    
    @staticmethod
    def get_lead_conversion_rate(company, user=None, days=30):
        """Calculate lead conversion rate"""
        from crm.models import Lead
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        leads_qs = Lead.objects.filter(company=company, created_at__gte=start_date)
        if user:
            leads_qs = leads_qs.filter(owner=user)
        
        total_leads = leads_qs.count()
        converted_leads = leads_qs.filter(status='converted').count()
        
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        return {
            'total_leads': total_leads,
            'converted_leads': converted_leads,
            'conversion_rate': round(conversion_rate, 2),
        }
    
    @staticmethod
    def get_deal_win_rate(company, user=None, days=30):
        """Calculate deal win rate"""
        from deals.models import Deal
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        deals_qs = Deal.objects.filter(company=company, created_at__gte=start_date)
        if user:
            deals_qs = deals_qs.filter(owner=user)
        
        total_closed = deals_qs.filter(stage__in=['closed_won', 'closed_lost']).count()
        won_deals = deals_qs.filter(stage='closed_won').count()
        
        win_rate = (won_deals / total_closed * 100) if total_closed > 0 else 0
        
        return {
            'total_closed': total_closed,
            'won_deals': won_deals,
            'win_rate': round(win_rate, 2),
        }
    
    @staticmethod
    def get_activity_summary(company, user=None, days=30):
        """Get activity summary"""
        from activities.models import Activity
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        activities_qs = Activity.objects.filter(
            company=company,
            created_at__gte=start_date
        )
        if user:
            activities_qs = activities_qs.filter(owner=user)
        
        summary = activities_qs.values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return list(summary)
    
    @staticmethod
    def get_revenue_forecast(company, user=None, months=3):
        """Get revenue forecast based on open deals"""
        from deals.models import Deal
        
        deals_qs = Deal.objects.filter(
            company=company,
            stage__in=['prospecting', 'qualification', 'proposal', 'negotiation']
        )
        if user:
            deals_qs = deals_qs.filter(owner=user)
        
        forecast = deals_qs.aggregate(
            total_pipeline=Sum('amount'),
            weighted_pipeline=Sum(F('amount') * F('probability') / 100.0),
            deal_count=Count('id')
        )
        
        return {
            'total_pipeline': forecast['total_pipeline'] or 0,
            'weighted_pipeline': forecast['weighted_pipeline'] or 0,
            'deal_count': forecast['deal_count'] or 0,
        }
    
    @staticmethod
    def get_top_performers(company, metric='deals_won', limit=10):
        """Get top performing users"""
        from django.contrib.auth import get_user_model
        from deals.models import Deal
        
        User = get_user_model()
        
        if metric == 'deals_won':
            top_users = Deal.objects.filter(
                company=company,
                stage='closed_won'
            ).values('owner__email', 'owner__first_name', 'owner__last_name').annotate(
                count=Count('id'),
                total_value=Sum('amount')
            ).order_by('-count')[:limit]
        else:
            # Default to deal count
            top_users = Deal.objects.filter(company=company).values(
                'owner__email', 'owner__first_name', 'owner__last_name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:limit]
        
        return list(top_users)
    
    @staticmethod
    def get_trending_data(company, days=30):
        """Get trending data for charts"""
        from deals.models import Deal
        from crm.models import Lead
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate date range
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date.date())
            current_date += timedelta(days=1)
        
        # Get daily data
        trending = {
            'dates': [str(d) for d in date_range],
            'leads': [],
            'deals': [],
            'revenue': [],
        }
        
        for date in date_range:
            next_date = date + timedelta(days=1)
            
            # Leads created
            leads_count = Lead.objects.filter(
                company=company,
                created_at__date=date
            ).count()
            trending['leads'].append(leads_count)
            
            # Deals created
            deals_count = Deal.objects.filter(
                company=company,
                created_at__date=date
            ).count()
            trending['deals'].append(deals_count)
            
            # Revenue (won deals)
            revenue = Deal.objects.filter(
                company=company,
                stage='closed_won',
                created_at__date=date
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            trending['revenue'].append(float(revenue))
        
        return trending
