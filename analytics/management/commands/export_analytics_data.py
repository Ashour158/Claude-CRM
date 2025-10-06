# analytics/management/commands/export_analytics_data.py
"""
Management command to export analytics data.
Can be used for scheduled exports or manual data extraction.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from analytics.models import AnalyticsExportJob
from analytics.tasks import process_analytics_export
import csv
import json
from io import StringIO
from datetime import timedelta


class Command(BaseCommand):
    help = 'Export analytics data to CSV or JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            required=True,
            choices=['deal_transitions', 'activities', 'lead_conversions'],
            help='Data source to export'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='csv',
            choices=['csv', 'json'],
            help='Export format (default: csv)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of data to export (default: 30)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path'
        )
        parser.add_argument(
            '--region',
            type=str,
            help='Filter by region'
        )

    def handle(self, *args, **options):
        source = options['source']
        export_format = options['format']
        days = options['days']
        output_path = options.get('output')
        region = options.get('region')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Exporting {source} data for last {days} days to {export_format}'
            )
        )
        
        # Get data based on source
        cutoff_date = timezone.now() - timedelta(days=days)
        
        if source == 'deal_transitions':
            from analytics.models import FactDealStageTransition
            queryset = FactDealStageTransition.objects.filter(
                transition_date__gte=cutoff_date
            )
            if region:
                queryset = queryset.filter(region=region)
            data = self.export_deal_transitions(queryset, export_format)
            
        elif source == 'activities':
            from analytics.models import FactActivity
            queryset = FactActivity.objects.filter(
                activity_date__gte=cutoff_date
            )
            if region:
                queryset = queryset.filter(region=region)
            data = self.export_activities(queryset, export_format)
            
        elif source == 'lead_conversions':
            from analytics.models import FactLeadConversion
            queryset = FactLeadConversion.objects.filter(
                event_date__gte=cutoff_date
            )
            if region:
                queryset = queryset.filter(region=region)
            data = self.export_lead_conversions(queryset, export_format)
        
        # Write to file or stdout
        if output_path:
            with open(output_path, 'w') as f:
                f.write(data)
            self.stdout.write(
                self.style.SUCCESS(f'Exported {queryset.count()} records to {output_path}')
            )
        else:
            self.stdout.write(data)
        
        self.stdout.write(
            self.style.SUCCESS('Export completed successfully')
        )

    def export_deal_transitions(self, queryset, format):
        """Export deal stage transitions"""
        if format == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Deal ID', 'Deal Name', 'From Stage', 'To Stage',
                'Transition Date', 'Days in Previous Stage',
                'Deal Amount', 'Probability', 'Weighted Amount',
                'Owner', 'Region'
            ])
            
            # Data rows
            for record in queryset.select_related('deal', 'owner'):
                writer.writerow([
                    str(record.deal.id) if record.deal else '',
                    record.deal.name if record.deal else '',
                    record.from_stage,
                    record.to_stage,
                    record.transition_date.isoformat(),
                    record.days_in_previous_stage,
                    str(record.deal_amount) if record.deal_amount else '',
                    record.probability,
                    str(record.weighted_amount) if record.weighted_amount else '',
                    record.owner.email if record.owner else '',
                    record.region
                ])
            
            return output.getvalue()
        
        else:  # JSON
            data = []
            for record in queryset.select_related('deal', 'owner'):
                data.append({
                    'deal_id': str(record.deal.id) if record.deal else None,
                    'deal_name': record.deal.name if record.deal else None,
                    'from_stage': record.from_stage,
                    'to_stage': record.to_stage,
                    'transition_date': record.transition_date.isoformat(),
                    'days_in_previous_stage': record.days_in_previous_stage,
                    'deal_amount': str(record.deal_amount) if record.deal_amount else None,
                    'probability': record.probability,
                    'weighted_amount': str(record.weighted_amount) if record.weighted_amount else None,
                    'owner': record.owner.email if record.owner else None,
                    'region': record.region
                })
            return json.dumps(data, indent=2)

    def export_activities(self, queryset, format):
        """Export activity facts"""
        if format == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Activity Type', 'Activity Date', 'Subject',
                'Duration (min)', 'Status', 'Is Completed',
                'Related Entity Type', 'Related Entity ID',
                'Assigned To', 'Region'
            ])
            
            # Data rows
            for record in queryset.select_related('assigned_to'):
                writer.writerow([
                    record.activity_type,
                    record.activity_date.isoformat(),
                    record.subject,
                    record.duration_minutes,
                    record.status,
                    'Yes' if record.is_completed else 'No',
                    record.related_entity_type,
                    str(record.related_entity_id) if record.related_entity_id else '',
                    record.assigned_to.email if record.assigned_to else '',
                    record.region
                ])
            
            return output.getvalue()
        
        else:  # JSON
            data = []
            for record in queryset.select_related('assigned_to'):
                data.append({
                    'activity_type': record.activity_type,
                    'activity_date': record.activity_date.isoformat(),
                    'subject': record.subject,
                    'duration_minutes': record.duration_minutes,
                    'status': record.status,
                    'is_completed': record.is_completed,
                    'related_entity_type': record.related_entity_type,
                    'related_entity_id': str(record.related_entity_id) if record.related_entity_id else None,
                    'assigned_to': record.assigned_to.email if record.assigned_to else None,
                    'region': record.region
                })
            return json.dumps(data, indent=2)

    def export_lead_conversions(self, queryset, format):
        """Export lead conversion facts"""
        if format == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Lead ID', 'Event Type', 'Event Date',
                'Lead Status', 'Lead Source', 'Lead Score',
                'Days Since Creation', 'Days in Previous Status',
                'Conversion Value', 'Owner', 'Region'
            ])
            
            # Data rows
            for record in queryset.select_related('lead', 'owner'):
                writer.writerow([
                    str(record.lead.id) if record.lead else '',
                    record.event_type,
                    record.event_date.isoformat(),
                    record.lead_status,
                    record.lead_source,
                    record.lead_score,
                    record.days_since_creation,
                    record.days_in_previous_status,
                    str(record.conversion_value) if record.conversion_value else '',
                    record.owner.email if record.owner else '',
                    record.region
                ])
            
            return output.getvalue()
        
        else:  # JSON
            data = []
            for record in queryset.select_related('lead', 'owner'):
                data.append({
                    'lead_id': str(record.lead.id) if record.lead else None,
                    'event_type': record.event_type,
                    'event_date': record.event_date.isoformat(),
                    'lead_status': record.lead_status,
                    'lead_source': record.lead_source,
                    'lead_score': record.lead_score,
                    'days_since_creation': record.days_since_creation,
                    'days_in_previous_status': record.days_in_previous_status,
                    'conversion_value': str(record.conversion_value) if record.conversion_value else None,
                    'owner': record.owner.email if record.owner else None,
                    'region': record.region
                })
            return json.dumps(data, indent=2)
