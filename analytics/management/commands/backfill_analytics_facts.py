# analytics/management/commands/backfill_analytics_facts.py
"""
Management command to backfill historical data into analytics fact tables.
This command populates fact tables from existing CRM data.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from analytics.models import (
    FactDealStageTransition, FactActivity, FactLeadConversion
)
from deals.models import Deal
from activities.models import Activity
from crm.models import Lead
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Backfill analytics fact tables from historical CRM data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Number of days of history to backfill (default: 365)'
        )
        parser.add_argument(
            '--fact-type',
            type=str,
            choices=['all', 'deals', 'activities', 'leads'],
            default='all',
            help='Which fact table to backfill (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually creating records'
        )

    def handle(self, *args, **options):
        days = options['days']
        fact_type = options['fact_type']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting backfill for last {days} days')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No records will be created')
            )
        
        # Backfill deal stage transitions
        if fact_type in ['all', 'deals']:
            self.backfill_deal_transitions(cutoff_date, dry_run)
        
        # Backfill activities
        if fact_type in ['all', 'activities']:
            self.backfill_activities(cutoff_date, dry_run)
        
        # Backfill lead conversions
        if fact_type in ['all', 'leads']:
            self.backfill_lead_conversions(cutoff_date, dry_run)
        
        self.stdout.write(
            self.style.SUCCESS('Backfill completed successfully')
        )

    def backfill_deal_transitions(self, cutoff_date, dry_run):
        """Backfill deal stage transition facts from existing deals"""
        self.stdout.write('Backfilling deal stage transitions...')
        
        # Get all deals created after cutoff date
        deals = Deal.objects.filter(created_at__gte=cutoff_date)
        created_count = 0
        
        for deal in deals:
            # Create initial transition record for deal creation
            transition_data = {
                'company': deal.company,
                'deal': deal,
                'from_stage': '',
                'to_stage': deal.stage,
                'transition_date': deal.created_at,
                'days_in_previous_stage': 0,
                'deal_amount': deal.amount,
                'probability': deal.probability,
                'weighted_amount': deal.weighted_amount,
                'owner': deal.owner,
                'region': getattr(deal, 'region', ''),
                'gdpr_consent': True,
            }
            
            if not dry_run:
                FactDealStageTransition.objects.get_or_create(
                    deal=deal,
                    transition_date=deal.created_at,
                    defaults=transition_data
                )
            created_count += 1
            
            # If deal is closed, create closing transition
            if deal.status in ['won', 'lost'] and deal.actual_close_date:
                days_in_stage = (deal.actual_close_date - deal.created_at.date()).days
                close_stage = 'closed_won' if deal.status == 'won' else 'closed_lost'
                
                close_data = {
                    'company': deal.company,
                    'deal': deal,
                    'from_stage': deal.stage if deal.stage != close_stage else 'negotiation',
                    'to_stage': close_stage,
                    'transition_date': timezone.make_aware(
                        datetime.combine(deal.actual_close_date, datetime.min.time())
                    ),
                    'days_in_previous_stage': days_in_stage,
                    'deal_amount': deal.amount,
                    'probability': 100 if deal.status == 'won' else 0,
                    'weighted_amount': deal.amount if deal.status == 'won' else 0,
                    'owner': deal.owner,
                    'region': getattr(deal, 'region', ''),
                    'gdpr_consent': True,
                }
                
                if not dry_run:
                    FactDealStageTransition.objects.get_or_create(
                        deal=deal,
                        to_stage=close_stage,
                        transition_date__date=deal.actual_close_date,
                        defaults=close_data
                    )
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'  Created {created_count} deal transition records'
            )
        )

    def backfill_activities(self, cutoff_date, dry_run):
        """Backfill activity facts from existing activities"""
        self.stdout.write('Backfilling activity facts...')
        
        # Get all activities after cutoff date
        activities = Activity.objects.filter(activity_date__gte=cutoff_date)
        created_count = 0
        
        for activity in activities:
            # Determine related entity
            related_entity_type = ''
            related_entity_id = None
            
            if activity.content_type and activity.object_id:
                related_entity_type = activity.content_type.model
                related_entity_id = activity.object_id
            
            activity_data = {
                'company': activity.company,
                'activity_type': activity.activity_type,
                'activity_date': activity.activity_date,
                'subject': activity.subject,
                'duration_minutes': activity.duration_minutes or 0,
                'status': activity.status,
                'outcome': '',
                'related_entity_type': related_entity_type,
                'related_entity_id': related_entity_id,
                'assigned_to': activity.assigned_to,
                'is_completed': activity.status == 'completed',
                'is_overdue': False,  # Could calculate based on due_date
                'completion_date': activity.updated_at if activity.status == 'completed' else None,
                'region': getattr(activity, 'region', ''),
                'gdpr_consent': True,
            }
            
            if not dry_run:
                FactActivity.objects.get_or_create(
                    activity_type=activity.activity_type,
                    activity_date=activity.activity_date,
                    assigned_to=activity.assigned_to,
                    subject=activity.subject,
                    defaults=activity_data
                )
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'  Created {created_count} activity records'
            )
        )

    def backfill_lead_conversions(self, cutoff_date, dry_run):
        """Backfill lead conversion facts from existing leads"""
        self.stdout.write('Backfilling lead conversion facts...')
        
        # Get all leads created after cutoff date
        leads = Lead.objects.filter(created_at__gte=cutoff_date)
        created_count = 0
        
        for lead in leads:
            # Create 'created' event
            created_data = {
                'company': lead.company,
                'lead': lead,
                'event_type': 'created',
                'event_date': lead.created_at,
                'lead_status': lead.lead_status,
                'lead_source': getattr(lead, 'source', ''),
                'lead_score': lead.lead_score,
                'days_since_creation': 0,
                'days_in_previous_status': 0,
                'owner': lead.owner,
                'region': getattr(lead, 'region', ''),
                'gdpr_consent': True,
            }
            
            if not dry_run:
                FactLeadConversion.objects.get_or_create(
                    lead=lead,
                    event_type='created',
                    event_date=lead.created_at,
                    defaults=created_data
                )
            created_count += 1
            
            # If lead is qualified, create 'qualified' event
            if lead.lead_status in ['qualified', 'converted']:
                days_since = (timezone.now() - lead.created_at).days
                qualified_data = {
                    'company': lead.company,
                    'lead': lead,
                    'event_type': 'qualified',
                    'event_date': lead.updated_at,
                    'lead_status': lead.lead_status,
                    'lead_source': getattr(lead, 'source', ''),
                    'lead_score': lead.lead_score,
                    'days_since_creation': days_since,
                    'days_in_previous_status': days_since,
                    'owner': lead.owner,
                    'region': getattr(lead, 'region', ''),
                    'gdpr_consent': True,
                }
                
                if not dry_run:
                    FactLeadConversion.objects.get_or_create(
                        lead=lead,
                        event_type='qualified',
                        defaults=qualified_data
                    )
                created_count += 1
            
            # If lead is converted, create 'converted' event
            if lead.lead_status == 'converted':
                days_since = (timezone.now() - lead.created_at).days
                
                # Try to find associated account/deal
                # This would need to be customized based on your conversion logic
                converted_data = {
                    'company': lead.company,
                    'lead': lead,
                    'event_type': 'converted',
                    'event_date': lead.updated_at,
                    'lead_status': lead.lead_status,
                    'lead_source': getattr(lead, 'source', ''),
                    'lead_score': lead.lead_score,
                    'days_since_creation': days_since,
                    'days_in_previous_status': 0,  # Would need historical data
                    'owner': lead.owner,
                    'region': getattr(lead, 'region', ''),
                    'gdpr_consent': True,
                }
                
                if not dry_run:
                    FactLeadConversion.objects.get_or_create(
                        lead=lead,
                        event_type='converted',
                        defaults=converted_data
                    )
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'  Created {created_count} lead conversion records'
            )
        )
