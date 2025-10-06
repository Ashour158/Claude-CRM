# crm/views.py
# CRM Views

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from .models import Account, Contact, Lead
from .serializers import AccountSerializer, ContactSerializer, LeadSerializer
from crm.leads.api.serializers import LeadConversionResultSerializer

logger = logging.getLogger(__name__)

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'email', 'phone', 'industry']
    filterset_fields = ['account_type', 'industry', 'is_active']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        account = self.get_object()
        contacts = account.contacts.all()
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def deals(self, request, pk=None):
        account = self.get_object()
        deals = account.deals.all()
        return Response({'deals': []})  # Placeholder

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        account = self.get_object()
        activities = account.activities.all()
        return Response({'activities': []})  # Placeholder

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        # CSV import logic
        return Response({'message': 'Import functionality not implemented yet'})

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        # CSV export logic
        return Response({'message': 'Export functionality not implemented yet'})

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    filterset_fields = ['account', 'owner', 'is_active']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        contact = self.get_object()
        activities = contact.activities.all()
        return Response({'activities': []})  # Placeholder

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        return Response({'message': 'Import functionality not implemented yet'})

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        return Response({'message': 'Export functionality not implemented yet'})

class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'company_name', 'email']
    filterset_fields = ['status', 'source', 'rating', 'owner']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        """
        Convert lead to Account + Contact.
        
        POST /api/crm/leads/{id}/convert/
        Body: {}
        
        Returns LeadConversionResultSerializer
        """
        lead = self.get_object()
        
        # Check if already converted
        if lead.status == 'converted':
            logger.info(
                f"Lead conversion attempted but lead already converted: "
                f"lead_id={lead.id}, account_id={lead.converted_account_id}, "
                f"contact_id={lead.converted_contact_id}"
            )
            return Response(
                {
                    'error': 'Lead has already been converted.',
                    'lead_id': lead.id,
                    'contact_id': lead.converted_contact_id,
                    'account_id': lead.converted_account_id,
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or find account
        created_account = False
        account = None
        if lead.company_name:
            # Check for duplicate account
            account = Account.objects.filter(
                company=lead.company,
                name__iexact=lead.company_name
            ).first()
            
            if not account:
                account = Account.objects.create(
                    company=lead.company,
                    name=lead.company_name,
                    email=lead.email if lead.email else '',
                    phone=lead.phone if lead.phone else '',
                    industry=lead.industry if lead.industry else '',
                    annual_revenue=lead.annual_revenue,
                    employee_count=lead.employee_count,
                    billing_city=lead.city,
                    billing_state=lead.state,
                    billing_postal_code=lead.postal_code,
                    billing_country=lead.country,
                    owner=lead.owner,
                )
                created_account = True
                logger.info(f"Created new account during lead conversion: account_id={account.id}, lead_id={lead.id}")
            else:
                logger.info(f"Using existing account for lead conversion: account_id={account.id}, lead_id={lead.id}")
        
        # Create contact
        contact = Contact.objects.create(
            company=lead.company,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            mobile=lead.mobile,
            title=lead.title,
            account=account,
            mailing_city=lead.city,
            mailing_state=lead.state,
            mailing_postal_code=lead.postal_code,
            mailing_country=lead.country,
            owner=lead.owner,
        )
        
        # Update lead
        lead.status = 'converted'
        lead.converted_at = timezone.now()
        lead.converted_account = account
        lead.converted_contact = contact
        lead.save()
        
        # Log successful conversion
        logger.info(
            f"Lead conversion successful: lead_id={lead.id}, "
            f"contact_id={contact.id}, account_id={account.id if account else None}, "
            f"created_account={created_account}, status=converted"
        )
        
        # Return conversion result
        result = {
            'lead_id': lead.id,
            'contact_id': contact.id,
            'account_id': account.id if account else None,
            'created_account': created_account,
            'status': 'converted',
            'message': 'Lead successfully converted to contact' + (' and account' if created_account else '')
        }
        
        serializer = LeadConversionResultSerializer(data=result)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        return Response({'message': 'Import functionality not implemented yet'})

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        return Response({'message': 'Export functionality not implemented yet'})