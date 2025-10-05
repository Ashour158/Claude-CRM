# crm/views.py
# CRM Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Account, Contact, Lead
from .serializers import AccountSerializer, ContactSerializer, LeadSerializer

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
        lead = self.get_object()
        # Lead conversion logic
        return Response({'message': 'Lead conversion not implemented yet'})

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        return Response({'message': 'Import functionality not implemented yet'})

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        return Response({'message': 'Export functionality not implemented yet'})