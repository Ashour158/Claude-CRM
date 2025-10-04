# crm/views/contacts.py
# ViewSet for Contact CRUD operations

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.http import HttpResponse
import csv
from io import StringIO

from crm.models import Contact, Account
from crm.serializers.contacts import (
    ContactSerializer, ContactListSerializer,
    ContactCreateSerializer, ContactUpdateSerializer,
    ContactStatsSerializer, ContactImportSerializer,
    BulkContactActionSerializer
)

class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Contact model providing CRUD operations.
    
    list:       GET    /api/v1/contacts/
    create:     POST   /api/v1/contacts/
    retrieve:   GET    /api/v1/contacts/{id}/
    update:     PUT    /api/v1/contacts/{id}/
    partial_update: PATCH /api/v1/contacts/{id}/
    destroy:    DELETE /api/v1/contacts/{id}/
    
    Custom Actions:
    - activities: GET /api/v1/contacts/{id}/activities/
    - deals:      GET /api/v1/contacts/{id}/deals/
    - stats:      GET /api/v1/contacts/stats/
    - import_csv: POST /api/v1/contacts/import/
    - export_csv: GET /api/v1/contacts/export/
    - bulk_action: POST /api/v1/contacts/bulk-action/
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account', 'owner', 'contact_type', 'is_active', 'is_primary']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'mobile', 'title']
    ordering_fields = ['last_name', 'first_name', 'created_at', 'updated_at']
    ordering = ['last_name', 'first_name']
    
    def get_queryset(self):
        """
        Filter contacts by active company
        """
        if not hasattr(self.request, 'active_company'):
            return Contact.objects.none()
        
        queryset = Contact.objects.filter(
            company=self.request.active_company
        ).select_related(
            'account', 'owner', 'reports_to'
        ).annotate(
            activities_count=Count('activity_set'),
            deals_count=Count('deal_set')
        )
        
        return queryset
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        """
        if self.action == 'list':
            return ContactListSerializer
        elif self.action == 'create':
            return ContactCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ContactUpdateSerializer
        elif self.action == 'stats':
            return ContactStatsSerializer
        elif self.action == 'import_csv':
            return ContactImportSerializer
        elif self.action == 'bulk_action':
            return BulkContactActionSerializer
        return ContactSerializer
    
    def perform_create(self, serializer):
        """
        Set company and created_by on contact creation
        """
        serializer.save(
            company=self.request.active_company,
            created_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """
        Set updated_by on contact update
        """
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        """
        Soft delete by setting is_active to False
        """
        if self.request.permissions.get('can_delete'):
            instance.delete()
        else:
            instance.is_active = False
            instance.updated_by = self.request.user
            instance.save()
    
    # ========================================
    # CUSTOM ACTIONS
    # ========================================
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """
        GET /api/v1/contacts/{id}/activities/
        Get all activities for this contact
        """
        contact = self.get_object()
        
        from crm.models.activities import Activity
        activities = Activity.objects.filter(
            company=self.request.active_company,
            contact=contact
        ).order_by('-activity_date')
        
        from crm.serializers.activities import ActivitySerializer
        serializer = ActivitySerializer(activities, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def deals(self, request, pk=None):
        """
        GET /api/v1/contacts/{id}/deals/
        Get all deals for this contact
        """
        contact = self.get_object()
        
        from crm.models.deals import Deal
        deals = Deal.objects.filter(
            company=self.request.active_company,
            contact=contact
        ).order_by('-created_at')
        
        from crm.serializers.deals import DealListSerializer
        serializer = DealListSerializer(deals, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        GET /api/v1/contacts/stats/
        Get contact statistics for dashboard
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_contacts': queryset.count(),
            'active_contacts': queryset.filter(is_active=True).count(),
            'contacts_with_accounts': queryset.filter(account__isnull=False).count(),
            'decision_makers': queryset.filter(contact_type='decision_maker').count(),
            'by_contact_type': {}
        }
        
        # Group by contact type
        types = queryset.values('contact_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats['by_contact_type'] = {
            item['contact_type']: item['count'] 
            for item in types if item['contact_type']
        }
        
        serializer = ContactStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """
        POST /api/v1/contacts/import/
        Import contacts from CSV file
        
        CSV Format:
        first_name,last_name,email,phone,title,account_name,owner_email
        """
        serializer = ContactImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        csv_file = serializer.validated_data['file']
        account_id = serializer.validated_data.get('account_id')
        
        # Get account if provided
        account = None
        if account_id:
            try:
                account = Account.objects.get(
                    id=account_id,
                    company=request.active_company
                )
            except Account.DoesNotExist:
                return Response({
                    'error': 'Account not found.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        decoded_file = csv_file.read().decode('utf-8')
        io_string = StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        created_count = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Get owner if email provided
                owner = None
                if row.get('owner_email'):
                    from core.models import User
                    try:
                        owner = User.objects.get(email=row['owner_email'])
                    except User.DoesNotExist:
                        pass
                
                # Get or create account if name provided
                contact_account = account
                if row.get('account_name') and not account:
                    contact_account, _ = Account.objects.get_or_create(
                        company=request.active_company,
                        name=row['account_name'],
                        defaults={'created_by': request.user}
                    )
                
                # Create contact
                contact = Contact.objects.create(
                    company=request.active_company,
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    email=row.get('email', ''),
                    phone=row.get('phone', ''),
                    mobile=row.get('mobile', ''),
                    title=row.get('title', ''),
                    department=row.get('department', ''),
                    account=contact_account,
                    owner=owner,
                    created_by=request.user
                )
                created_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return Response({
            'message': f'Successfully imported {created_count} contacts.',
            'created_count': created_count,
            'errors': errors
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """
        GET /api/v1/contacts/export/
        Export contacts to CSV file
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Create CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="contacts.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'First Name', 'Last Name', 'Email', 'Phone', 'Mobile',
            'Title', 'Department', 'Account', 'Owner', 'Contact Type',
            'Is Primary', 'Created At'
        ])
        
        # Write data
        for contact in queryset:
            writer.writerow([
                contact.first_name,
                contact.last_name,
                contact.email,
                contact.phone,
                contact.mobile,
                contact.title,
                contact.department,
                contact.account.name if contact.account else '',
                contact.owner.full_name if contact.owner else '',
                contact.contact_type,
                'Yes' if contact.is_primary else 'No',
                contact.created_at.strftime('%Y-%m-%d')
            ])
        
        return response
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """
        POST /api/v1/contacts/bulk-action/
        Perform bulk actions on multiple contacts
        
        Actions: delete, deactivate, activate, assign_owner
        """
        serializer = BulkContactActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact_ids = serializer.validated_data['contact_ids']
        action = serializer.validated_data['action']
        
        # Get contacts
        contacts = Contact.objects.filter(
            id__in=contact_ids,
            company=request.active_company
        )
        
        if not contacts.exists():
            return Response({
                'error': 'No contacts found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        affected_count = 0
        
        if action == 'delete':
            if request.permissions.get('can_delete'):
                affected_count = contacts.count()
                contacts.delete()
            else:
                return Response({
                    'error': 'You do not have permission to delete contacts.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        elif action == 'deactivate':
            affected_count = contacts.update(
                is_active=False,
                updated_by=request.user
            )
        
        elif action == 'activate':
            affected_count = contacts.update(
                is_active=True,
                updated_by=request.user
            )
        
        elif action == 'assign_owner':
            owner_id = serializer.validated_data.get('owner_id')
            from core.models import User
            try:
                owner = User.objects.get(id=owner_id)
                affected_count = contacts.update(
                    owner=owner,
                    updated_by=request.user
                )
            except User.DoesNotExist:
                return Response({
                    'error': 'Owner not found.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'message': f'Successfully performed {action} on {affected_count} contacts.',
            'affected_count': affected_count
        })
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """
        POST /api/v1/contacts/{id}/set-primary/
        Set this contact as primary for its account
        """
        contact = self.get_object()
        
        if not contact.account:
            return Response({
                'error': 'Contact must be associated with an account to set as primary.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Unset other primary contacts for this account
        Contact.objects.filter(
            account=contact.account,
            is_primary=True
        ).exclude(id=contact.id).update(is_primary=False)
        
        # Set this as primary
        contact.is_primary = True
        contact.updated_by = request.user
        contact.save()
        
        return Response({
            'message': 'Contact set as primary successfully.'
        })
    
    @action(detail=True, methods=['post'])
    def merge(self, request, pk=None):
        """
        POST /api/v1/contacts/{id}/merge/
        Merge another contact into this one
        
        Body: { "source_contact_id": "uuid" }
        """
        target_contact = self.get_object()
        source_contact_id = request.data.get('source_contact_id')
        
        if not source_contact_id:
            return Response({
                'error': 'source_contact_id is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            source_contact = Contact.objects.get(
                id=source_contact_id,
                company=request.active_company
            )
            
            if source_contact.id == target_contact.id:
                return Response({
                    'error': 'Cannot merge a contact with itself.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Move activities from source to target
            from crm.models.activities import Activity
            Activity.objects.filter(contact=source_contact).update(
                contact=target_contact
            )
            
            # Move deals from source to target
            from crm.models.deals import Deal
            Deal.objects.filter(contact=source_contact).update(
                contact=target_contact
            )
            
            # Delete source contact
            source_contact.delete()
            
            return Response({
                'message': 'Contacts merged successfully.',
                'target_contact': ContactSerializer(target_contact).data
            })
            
        except Contact.DoesNotExist:
            return Response({
                'error': 'Source contact not found.'
            }, status=status.HTTP_404_NOT_FOUND)