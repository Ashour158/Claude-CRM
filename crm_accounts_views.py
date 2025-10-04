# crm/views/accounts.py
# ViewSet for Account CRUD operations

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q
from django.http import HttpResponse
import csv
from io import StringIO

from crm.models import Account
from crm.serializers.accounts import (
    AccountSerializer, AccountListSerializer,
    AccountCreateSerializer, AccountUpdateSerializer,
    AccountStatsSerializer, AccountImportSerializer
)

class AccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Account model providing CRUD operations.
    
    list:       GET    /api/v1/accounts/
    create:     POST   /api/v1/accounts/
    retrieve:   GET    /api/v1/accounts/{id}/
    update:     PUT    /api/v1/accounts/{id}/
    partial_update: PATCH /api/v1/accounts/{id}/
    destroy:    DELETE /api/v1/accounts/{id}/
    
    Custom Actions:
    - contacts: GET /api/v1/accounts/{id}/contacts/
    - deals:    GET /api/v1/accounts/{id}/deals/
    - activities: GET /api/v1/accounts/{id}/activities/
    - stats:    GET /api/v1/accounts/stats/
    - import_csv: POST /api/v1/accounts/import/
    - export_csv: GET /api/v1/accounts/export/
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account_type', 'industry', 'territory', 'owner', 'is_active']
    search_fields = ['name', 'legal_name', 'email', 'phone', 'website', 'account_number']
    ordering_fields = ['name', 'created_at', 'updated_at', 'annual_revenue']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter accounts by active company.
        Uses company from request context (set by middleware).
        """
        if not hasattr(self.request, 'active_company'):
            return Account.objects.none()
        
        queryset = Account.objects.filter(
            company=self.request.active_company
        ).select_related(
            'owner', 'territory', 'parent_account'
        ).annotate(
            contacts_count=Count('contacts'),
            deals_count=Count('deals')
        )
        
        return queryset
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list':
            return AccountListSerializer
        elif self.action == 'create':
            return AccountCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AccountUpdateSerializer
        elif self.action == 'stats':
            return AccountStatsSerializer
        elif self.action == 'import_csv':
            return AccountImportSerializer
        return AccountSerializer
    
    def perform_create(self, serializer):
        """
        Set company and created_by on account creation.
        """
        serializer.save(
            company=self.request.active_company,
            created_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """
        Set updated_by on account update.
        """
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        """
        Soft delete by setting is_active to False.
        Hard delete only if user has delete permission.
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
    def contacts(self, request, pk=None):
        """
        GET /api/v1/accounts/{id}/contacts/
        Get all contacts for this account.
        """
        account = self.get_object()
        contacts = account.contacts.filter(is_active=True)
        
        # Import here to avoid circular import
        from crm.serializers.contacts import ContactListSerializer
        serializer = ContactListSerializer(contacts, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def deals(self, request, pk=None):
        """
        GET /api/v1/accounts/{id}/deals/
        Get all deals for this account.
        """
        account = self.get_object()
        deals = account.deals.all().order_by('-created_at')
        
        # Import here to avoid circular import
        from crm.serializers.deals import DealListSerializer
        serializer = DealListSerializer(deals, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """
        GET /api/v1/accounts/{id}/activities/
        Get all activities for this account.
        """
        account = self.get_object()
        
        # Import here to avoid circular import
        from crm.models import Activity
        activities = Activity.objects.filter(
            company=self.request.active_company,
            related_to_type='account',
            related_to_id=account.id
        ).order_by('-activity_date')
        
        from crm.serializers.activities import ActivitySerializer
        serializer = ActivitySerializer(activities, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        GET /api/v1/accounts/stats/
        Get account statistics for dashboard.
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_accounts': queryset.count(),
            'active_accounts': queryset.filter(is_active=True).count(),
            'customers': queryset.filter(account_type='customer').count(),
            'prospects': queryset.filter(account_type='prospect').count(),
            'by_industry': {},
            'total_revenue': 0
        }
        
        # Group by industry
        industries = queryset.values('industry').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        stats['by_industry'] = {
            item['industry']: item['count'] 
            for item in industries if item['industry']
        }
        
        # Total annual revenue
        revenue_sum = queryset.aggregate(
            total=Sum('annual_revenue')
        )
        stats['total_revenue'] = revenue_sum['total'] or 0
        
        serializer = AccountStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """
        POST /api/v1/accounts/import/
        Import accounts from CSV file.
        
        CSV Format:
        name,email,phone,industry,account_type,owner_email
        """
        serializer = AccountImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        csv_file = serializer.validated_data['file']
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
                
                # Create account
                account = Account.objects.create(
                    company=request.active_company,
                    name=row['name'],
                    email=row.get('email', ''),
                    phone=row.get('phone', ''),
                    industry=row.get('industry', ''),
                    account_type=row.get('account_type', 'prospect'),
                    owner=owner,
                    created_by=request.user
                )
                created_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return Response({
            'message': f'Successfully imported {created_count} accounts.',
            'created_count': created_count,
            'errors': errors
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """
        GET /api/v1/accounts/export/
        Export accounts to CSV file.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Create CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="accounts.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Account Number', 'Name', 'Legal Name', 'Email', 'Phone',
            'Website', 'Account Type', 'Industry', 'Annual Revenue',
            'Employee Count', 'Owner', 'Territory', 'Created At'
        ])
        
        # Write data
        for account in queryset:
            writer.writerow([
                account.account_number,
                account.name,
                account.legal_name,
                account.email,
                account.phone,
                account.website,
                account.account_type,
                account.industry,
                account.annual_revenue or '',
                account.employee_count or '',
                account.owner.full_name if account.owner else '',
                account.territory.name if account.territory else '',
                account.created_at.strftime('%Y-%m-%d')
            ])
        
        return response
    
    @action(detail=True, methods=['post'])
    def assign_territory(self, request, pk=None):
        """
        POST /api/v1/accounts/{id}/assign-territory/
        Manually assign account to a territory.
        """
        account = self.get_object()
        territory_id = request.data.get('territory_id')
        
        if not territory_id:
            return Response({
                'error': 'territory_id is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from territories.models import Territory
            territory = Territory.objects.get(
                id=territory_id,
                company=request.active_company
            )
            
            account.territory = territory
            account.updated_by = request.user
            account.save()
            
            return Response({
                'message': 'Territory assigned successfully.',
                'territory': {
                    'id': str(territory.id),
                    'name': territory.name
                }
            })
            
        except Territory.DoesNotExist:
            return Response({
                'error': 'Territory not found.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def assign_owner(self, request, pk=None):
        """
        POST /api/v1/accounts/{id}/assign-owner/
        Assign account to a user.
        """
        account = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({
                'error': 'user_id is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from core.models import User
            user = User.objects.get(id=user_id)
            
            # Check if user has access to this company
            if not user.has_company_access(request.active_company):
                return Response({
                    'error': 'User does not have access to this company.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            account.owner = user
            account.updated_by = request.user
            account.save()
            
            return Response({
                'message': 'Owner assigned successfully.',
                'owner': {
                    'id': str(user.id),
                    'name': user.full_name,
                    'email': user.email
                }
            })
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)