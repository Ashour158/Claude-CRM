# crm/views/leads.py
# ViewSet for Lead CRUD and conversion

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.http import HttpResponse
import csv
from io import StringIO

from crm.models import Lead
from crm.serializers.leads import (
    LeadSerializer, LeadListSerializer, LeadCreateSerializer,
    LeadUpdateSerializer, LeadConvertSerializer, LeadStatsSerializer,
    LeadImportSerializer, BulkLeadActionSerializer, LeadScoringSerializer
)

class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lead model with conversion capability
    
    Custom Actions:
    - convert: POST /api/v1/leads/{id}/convert/
    - qualify: POST /api/v1/leads/{id}/qualify/
    - disqualify: POST /api/v1/leads/{id}/disqualify/
    - score: POST /api/v1/leads/{id}/score/
    - stats: GET /api/v1/leads/stats/
    - import_csv: POST /api/v1/leads/import/
    - export_csv: GET /api/v1/leads/export/
    - bulk_action: POST /api/v1/leads/bulk-action/
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['lead_status', 'rating', 'lead_source', 'territory', 'owner', 'is_active']
    search_fields = ['first_name', 'last_name', 'company_name', 'email', 'phone']
    ordering_fields = ['created_at', 'updated_at', 'lead_score', 'last_name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if not hasattr(self.request, 'active_company'):
            return Lead.objects.none()
        
        return Lead.objects.filter(
            company=self.request.active_company
        ).select_related(
            'owner', 'territory'
        ).annotate(
            activities_count=Count('activity_set')
        )
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer
        elif self.action == 'create':
            return LeadCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return LeadUpdateSerializer
        elif self.action == 'convert':
            return LeadConvertSerializer
        elif self.action == 'stats':
            return LeadStatsSerializer
        elif self.action == 'import_csv':
            return LeadImportSerializer
        elif self.action == 'bulk_action':
            return BulkLeadActionSerializer
        elif self.action == 'score':
            return LeadScoringSerializer
        return LeadSerializer
    
    def perform_create(self, serializer):
        serializer.save(
            company=self.request.active_company,
            created_by=self.request.user
        )
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    # ========================================
    # LEAD CONVERSION
    # ========================================
    
    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        """
        POST /api/v1/leads/{id}/convert/
        Convert lead to Account + Contact + Deal
        
        Body: {
            "create_deal": true,
            "deal_amount": 10000.00,
            "deal_name": "Optional deal name",
            "deal_close_date": "2025-12-31"
        }
        """
        lead = self.get_object()
        
        if lead.lead_status == 'converted':
            return Response({
                'error': 'Lead has already been converted.',
                'converted_account_id': str(lead.converted_account_id) if lead.converted_account else None,
                'converted_contact_id': str(lead.converted_contact_id) if lead.converted_contact else None,
                'converted_deal_id': str(lead.converted_deal_id) if lead.converted_deal else None,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = LeadConvertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        create_deal = serializer.validated_data.get('create_deal', True)
        deal_amount = serializer.validated_data.get('deal_amount')
        
        # Perform conversion
        account, contact, deal = lead.convert(
            create_deal=create_deal,
            deal_amount=deal_amount
        )
        
        return Response({
            'message': 'Lead converted successfully.',
            'account_id': str(account.id),
            'contact_id': str(contact.id),
            'deal_id': str(deal.id) if deal else None,
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def qualify(self, request, pk=None):
        """
        POST /api/v1/leads/{id}/qualify/
        Mark lead as qualified
        """
        lead = self.get_object()
        lead.lead_status = 'qualified'
        lead.updated_by = request.user
        lead.save()
        
        return Response({
            'message': 'Lead marked as qualified.',
            'lead': LeadSerializer(lead).data
        })
    
    @action(detail=True, methods=['post'])
    def disqualify(self, request, pk=None):
        """
        POST /api/v1/leads/{id}/disqualify/
        Mark lead as unqualified
        """
        lead = self.get_object()
        lead.lead_status = 'unqualified'
        lead.updated_by = request.user
        lead.save()
        
        return Response({
            'message': 'Lead marked as unqualified.',
            'lead': LeadSerializer(lead).data
        })
    
    # ========================================
    # LEAD SCORING
    # ========================================
    
    @action(detail=True, methods=['post'])
    def score(self, request, pk=None):
        """
        POST /api/v1/leads/{id}/score/
        Calculate and update lead score
        """
        lead = self.get_object()
        old_score = lead.lead_score
        new_score = lead.calculate_lead_score()
        lead.lead_score = new_score
        lead.save()
        
        factors = {
            'has_email': bool(lead.email),
            'has_phone': bool(lead.phone or lead.mobile),
            'has_company': bool(lead.company_name),
            'has_industry': bool(lead.industry),
            'has_revenue': bool(lead.annual_revenue),
            'has_budget': bool(lead.budget),
            'rating': lead.rating,
            'has_activities': lead.activities_count > 0,
            'is_recent': lead.days_since_creation <= 7
        }
        
        recommendation = ''
        if new_score >= 80:
            recommendation = 'Hot lead! Contact immediately and qualify.'
        elif new_score >= 60:
            recommendation = 'Warm lead. Schedule follow-up within 24 hours.'
        elif new_score >= 40:
            recommendation = 'Average lead. Add to nurture campaign.'
        else:
            recommendation = 'Cold lead. Consider disqualifying or long-term nurture.'
        
        return Response({
            'lead_id': str(lead.id),
            'score': new_score,
            'previous_score': old_score,
            'factors': factors,
            'recommendation': recommendation
        })
    
    # ========================================
    # STATISTICS
    # ========================================
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        GET /api/v1/leads/stats/
        Get lead statistics
        """
        queryset = self.get_queryset()
        
        total = queryset.count()
        converted_count = queryset.filter(lead_status='converted').count()
        
        stats = {
            'total_leads': total,
            'new_leads': queryset.filter(lead_status='new').count(),
            'qualified_leads': queryset.filter(lead_status='qualified').count(),
            'converted_leads': converted_count,
            'hot_leads': queryset.filter(rating='hot').count(),
            'by_source': {},
            'by_status': {},
            'conversion_rate': (converted_count / total * 100) if total > 0 else 0,
            'avg_lead_score': queryset.aggregate(Avg('lead_score'))['lead_score__avg'] or 0
        }
        
        # Group by source
        sources = queryset.values('lead_source').annotate(count=Count('id'))
        stats['by_source'] = {item['lead_source']: item['count'] for item in sources if item['lead_source']}
        
        # Group by status
        statuses = queryset.values('lead_status').annotate(count=Count('id'))
        stats['by_status'] = {item['lead_status']: item['count'] for item in statuses}
        
        serializer = LeadStatsSerializer(stats)
        return Response(serializer.data)
    
    # ========================================
    # IMPORT/EXPORT
    # ========================================
    
    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """
        POST /api/v1/leads/import/
        Import leads from CSV
        """
        serializer = LeadImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        csv_file = serializer.validated_data['file']
        owner_id = serializer.validated_data.get('owner_id')
        
        owner = None
        if owner_id:
            from core.models import User
            try:
                owner = User.objects.get(id=owner_id)
            except User.DoesNotExist:
                pass
        
        decoded_file = csv_file.read().decode('utf-8')
        io_string = StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        created_count = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):
            try:
                lead = Lead.objects.create(
                    company=request.active_company,
                    first_name=row.get('first_name', ''),
                    last_name=row.get('last_name', ''),
                    company_name=row.get('company_name', ''),
                    email=row.get('email', ''),
                    phone=row.get('phone', ''),
                    mobile=row.get('mobile', ''),
                    title=row.get('title', ''),
                    lead_source=row.get('lead_source', 'other'),
                    industry=row.get('industry', ''),
                    owner=owner,
                    created_by=request.user
                )
                
                # Auto-score and assign
                lead.lead_score = lead.calculate_lead_score()
                lead.auto_assign_territory()
                lead.save()
                
                created_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return Response({
            'message': f'Successfully imported {created_count} leads.',
            'created_count': created_count,
            'errors': errors
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """
        GET /api/v1/leads/export/
        Export leads to CSV
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leads.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'First Name', 'Last Name', 'Company', 'Email', 'Phone',
            'Title', 'Status', 'Rating', 'Score', 'Source',
            'Industry', 'Owner', 'Created At'
        ])
        
        for lead in queryset:
            writer.writerow([
                lead.first_name,
                lead.last_name,
                lead.company_name,
                lead.email,
                lead.phone,
                lead.title,
                lead.lead_status,
                lead.rating,
                lead.lead_score,
                lead.lead_source,
                lead.industry,
                lead.owner.full_name if lead.owner else '',
                lead.created_at.strftime('%Y-%m-%d')
            ])
        
        return response
    
    # ========================================
    # BULK ACTIONS
    # ========================================
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """
        POST /api/v1/leads/bulk-action/
        Perform bulk actions on leads
        """
        serializer = BulkLeadActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        lead_ids = serializer.validated_data['lead_ids']
        action_type = serializer.validated_data['action']
        
        leads = Lead.objects.filter(
            id__in=lead_ids,
            company=request.active_company
        )
        
        if not leads.exists():
            return Response({
                'error': 'No leads found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        affected_count = 0
        
        if action_type == 'delete':
            if request.permissions.get('can_delete'):
                affected_count = leads.count()
                leads.delete()
            else:
                return Response({
                    'error': 'You do not have permission to delete leads.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        elif action_type == 'qualify':
            affected_count = leads.update(
                lead_status='qualified',
                updated_by=request.user
            )
        
        elif action_type == 'disqualify':
            affected_count = leads.update(
                lead_status='unqualified',
                updated_by=request.user
            )
        
        elif action_type == 'assign_owner':
            owner_id = serializer.validated_data.get('owner_id')
            from core.models import User
            try:
                owner = User.objects.get(id=owner_id)
                affected_count = leads.update(owner=owner, updated_by=request.user)
            except User.DoesNotExist:
                return Response({
                    'error': 'Owner not found.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        elif action_type == 'assign_territory':
            territory_id = serializer.validated_data.get('territory_id')
            from territories.models import Territory
            try:
                territory = Territory.objects.get(id=territory_id, company=request.active_company)
                affected_count = leads.update(territory=territory, updated_by=request.user)
            except Territory.DoesNotExist:
                return Response({
                    'error': 'Territory not found.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'message': f'Successfully performed {action_type} on {affected_count} leads.',
            'affected_count': affected_count
        })