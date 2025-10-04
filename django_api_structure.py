# ========================================
# Django REST Framework API Structure
# Complete API endpoint organization
# ========================================

"""
API ENDPOINT STRUCTURE

Base URL: /api/v1/

AUTHENTICATION & USER MANAGEMENT
POST   /api/v1/auth/register/
POST   /api/v1/auth/login/
POST   /api/v1/auth/logout/
POST   /api/v1/auth/refresh-token/
POST   /api/v1/auth/password-reset/
POST   /api/v1/auth/password-reset-confirm/
POST   /api/v1/auth/verify-email/
GET    /api/v1/auth/me/
PATCH  /api/v1/auth/me/

COMPANY MANAGEMENT (Admin only)
GET    /api/v1/companies/
POST   /api/v1/companies/
GET    /api/v1/companies/{id}/
PATCH  /api/v1/companies/{id}/
DELETE /api/v1/companies/{id}/
POST   /api/v1/companies/{id}/switch/  # Switch active company
GET    /api/v1/companies/{id}/users/
POST   /api/v1/companies/{id}/users/   # Add user to company
DELETE /api/v1/companies/{id}/users/{user_id}/

USER COMPANY ACCESS
GET    /api/v1/user-access/
GET    /api/v1/user-access/{id}/
PATCH  /api/v1/user-access/{id}/

TERRITORIES
GET    /api/v1/territories/
POST   /api/v1/territories/
GET    /api/v1/territories/{id}/
PATCH  /api/v1/territories/{id}/
DELETE /api/v1/territories/{id}/
GET    /api/v1/territories/{id}/children/
POST   /api/v1/territories/{id}/assign-accounts/
POST   /api/v1/territories/{id}/assign-leads/

TERRITORY RULES
GET    /api/v1/territory-rules/
POST   /api/v1/territory-rules/
GET    /api/v1/territory-rules/{id}/
PATCH  /api/v1/territory-rules/{id}/
DELETE /api/v1/territory-rules/{id}/
POST   /api/v1/territory-rules/evaluate/  # Test rule

ACCOUNTS
GET    /api/v1/accounts/
POST   /api/v1/accounts/
GET    /api/v1/accounts/{id}/
PATCH  /api/v1/accounts/{id}/
DELETE /api/v1/accounts/{id}/
GET    /api/v1/accounts/{id}/contacts/
GET    /api/v1/accounts/{id}/deals/
GET    /api/v1/accounts/{id}/activities/
POST   /api/v1/accounts/import/  # CSV import
GET    /api/v1/accounts/export/  # CSV export

CONTACTS
GET    /api/v1/contacts/
POST   /api/v1/contacts/
GET    /api/v1/contacts/{id}/
PATCH  /api/v1/contacts/{id}/
DELETE /api/v1/contacts/{id}/
GET    /api/v1/contacts/{id}/activities/
POST   /api/v1/contacts/import/
GET    /api/v1/contacts/export/

LEADS
GET    /api/v1/leads/
POST   /api/v1/leads/
GET    /api/v1/leads/{id}/
PATCH  /api/v1/leads/{id}/
DELETE /api/v1/leads/{id}/
POST   /api/v1/leads/{id}/convert/  # Convert to Contact/Account/Deal
POST   /api/v1/leads/{id}/assign/
GET    /api/v1/leads/{id}/activities/
POST   /api/v1/leads/import/
GET    /api/v1/leads/export/

PIPELINE STAGES
GET    /api/v1/pipeline-stages/
POST   /api/v1/pipeline-stages/
GET    /api/v1/pipeline-stages/{id}/
PATCH  /api/v1/pipeline-stages/{id}/
DELETE /api/v1/pipeline-stages/{id}/
POST   /api/v1/pipeline-stages/reorder/

DEALS/OPPORTUNITIES
GET    /api/v1/deals/
POST   /api/v1/deals/
GET    /api/v1/deals/{id}/
PATCH  /api/v1/deals/{id}/
DELETE /api/v1/deals/{id}/
POST   /api/v1/deals/{id}/change-stage/
POST   /api/v1/deals/{id}/mark-won/
POST   /api/v1/deals/{id}/mark-lost/
GET    /api/v1/deals/{id}/activities/
GET    /api/v1/deals/pipeline/  # Kanban view data
GET    /api/v1/deals/forecast/

ACTIVITIES
GET    /api/v1/activities/
POST   /api/v1/activities/
GET    /api/v1/activities/{id}/
PATCH  /api/v1/activities/{id}/
DELETE /api/v1/activities/{id}/
POST   /api/v1/activities/log-call/
POST   /api/v1/activities/log-email/
POST   /api/v1/activities/log-meeting/

TASKS
GET    /api/v1/tasks/
POST   /api/v1/tasks/
GET    /api/v1/tasks/{id}/
PATCH  /api/v1/tasks/{id}/
DELETE /api/v1/tasks/{id}/
POST   /api/v1/tasks/{id}/complete/
POST   /api/v1/tasks/{id}/reopen/
GET    /api/v1/tasks/my-tasks/
GET    /api/v1/tasks/today/
GET    /api/v1/tasks/overdue/

EVENTS/CALENDAR
GET    /api/v1/events/
POST   /api/v1/events/
GET    /api/v1/events/{id}/
PATCH  /api/v1/events/{id}/
DELETE /api/v1/events/{id}/
GET    /api/v1/events/calendar/  # Calendar view with filters

PRODUCTS
GET    /api/v1/products/
POST   /api/v1/products/
GET    /api/v1/products/{id}/
PATCH  /api/v1/products/{id}/
DELETE /api/v1/products/{id}/
POST   /api/v1/products/import/
GET    /api/v1/products/export/

PRODUCT CATEGORIES
GET    /api/v1/product-categories/
POST   /api/v1/product-categories/
GET    /api/v1/product-categories/{id}/
PATCH  /api/v1/product-categories/{id}/
DELETE /api/v1/product-categories/{id}/

PRICE LISTS
GET    /api/v1/price-lists/
POST   /api/v1/price-lists/
GET    /api/v1/price-lists/{id}/
PATCH  /api/v1/price-lists/{id}/
DELETE /api/v1/price-lists/{id}/
GET    /api/v1/price-lists/{id}/items/
POST   /api/v1/price-lists/{id}/items/

RFQs (Field Sales)
GET    /api/v1/rfqs/
POST   /api/v1/rfqs/
GET    /api/v1/rfqs/{id}/
PATCH  /api/v1/rfqs/{id}/
DELETE /api/v1/rfqs/{id}/
POST   /api/v1/rfqs/{id}/submit/
POST   /api/v1/rfqs/{id}/convert-to-quote/
GET    /api/v1/rfqs/{id}/items/
POST   /api/v1/rfqs/{id}/items/

QUOTES
GET    /api/v1/quotes/
POST   /api/v1/quotes/
GET    /api/v1/quotes/{id}/
PATCH  /api/v1/quotes/{id}/
DELETE /api/v1/quotes/{id}/
POST   /api/v1/quotes/{id}/submit-for-approval/
POST   /api/v1/quotes/{id}/approve/
POST   /api/v1/quotes/{id}/reject/
POST   /api/v1/quotes/{id}/send/  # Email to customer
POST   /api/v1/quotes/{id}/generate-pdf/
POST   /api/v1/quotes/{id}/convert-to-order/
POST   /api/v1/quotes/{id}/create-version/
GET    /api/v1/quotes/{id}/items/
POST   /api/v1/quotes/{id}/items/

QUOTE APPROVALS
GET    /api/v1/quote-approvals/
GET    /api/v1/quote-approvals/pending/
POST   /api/v1/quote-approvals/{id}/approve/
POST   /api/v1/quote-approvals/{id}/reject/

QUOTE TEMPLATES
GET    /api/v1/quote-templates/
POST   /api/v1/quote-templates/
GET    /api/v1/quote-templates/{id}/
PATCH  /api/v1/quote-templates/{id}/
DELETE /api/v1/quote-templates/{id}/
POST   /api/v1/quote-templates/{id}/set-default/
POST   /api/v1/quote-templates/{id}/preview/

SALES ORDERS
GET    /api/v1/sales-orders/
POST   /api/v1/sales-orders/
GET    /api/v1/sales-orders/{id}/
PATCH  /api/v1/sales-orders/{id}/
DELETE /api/v1/sales-orders/{id}/
POST   /api/v1/sales-orders/{id}/confirm/
POST   /api/v1/sales-orders/{id}/ship/
POST   /api/v1/sales-orders/{id}/deliver/
POST   /api/v1/sales-orders/{id}/cancel/
POST   /api/v1/sales-orders/{id}/generate-pdf/
GET    /api/v1/sales-orders/{id}/items/
POST   /api/v1/sales-orders/{id}/items/

SHIPMENTS
GET    /api/v1/shipments/
POST   /api/v1/shipments/
GET    /api/v1/shipments/{id}/
PATCH  /api/v1/shipments/{id}/
POST   /api/v1/shipments/{id}/ship/
POST   /api/v1/shipments/{id}/deliver/
GET    /api/v1/shipments/{id}/track/

INVOICES
GET    /api/v1/invoices/
POST   /api/v1/invoices/
GET    /api/v1/invoices/{id}/
PATCH  /api/v1/invoices/{id}/
DELETE /api/v1/invoices/{id}/
POST   /api/v1/invoices/{id}/send/
POST   /api/v1/invoices/{id}/generate-pdf/
POST   /api/v1/invoices/{id}/record-payment/
GET    /api/v1/invoices/overdue/
GET    /api/v1/invoices/aging-report/

PAYMENTS
GET    /api/v1/payments/
POST   /api/v1/payments/
GET    /api/v1/payments/{id}/
PATCH  /api/v1/payments/{id}/
DELETE /api/v1/payments/{id}/

VENDORS
GET    /api/v1/vendors/
POST   /api/v1/vendors/
GET    /api/v1/vendors/{id}/
PATCH  /api/v1/vendors/{id}/
DELETE /api/v1/vendors/{id}/
POST   /api/v1/vendors/{id}/approve/
POST   /api/v1/vendors/{id}/blacklist/
GET    /api/v1/vendors/{id}/performance/
GET    /api/v1/vendors/{id}/scorecards/
GET    /api/v1/vendors/{id}/purchase-orders/
POST   /api/v1/vendors/import/
GET    /api/v1/vendors/export/

VENDOR CONTACTS
GET    /api/v1/vendor-contacts/
POST   /api/v1/vendor-contacts/
GET    /api/v1/vendor-contacts/{id}/
PATCH  /api/v1/vendor-contacts/{id}/
DELETE /api/v1/vendor-contacts/{id}/

VENDOR SCORECARDS
GET    /api/v1/vendor-scorecards/
POST   /api/v1/vendor-scorecards/
GET    /api/v1/vendor-scorecards/{id}/
PATCH  /api/v1/vendor-scorecards/{id}/
POST   /api/v1/vendor-scorecards/{id}/finalize/

PURCHASE REQUISITIONS
GET    /api/v1/purchase-requisitions/
POST   /api/v1/purchase-requisitions/
GET    /api/v1/purchase-requisitions/{id}/
PATCH  /api/v1/purchase-requisitions/{id}/
DELETE /api/v1/purchase-requisitions/{id}/
POST   /api/v1/purchase-requisitions/{id}/submit/
POST   /api/v1/purchase-requisitions/{id}/approve/
POST   /api/v1/purchase-requisitions/{id}/reject/
POST   /api/v1/purchase-requisitions/{id}/convert-to-rfq/

VENDOR RFQs (Procurement)
GET    /api/v1/vendor-rfqs/
POST   /api/v1/vendor-rfqs/
GET    /api/v1/vendor-rfqs/{id}/
PATCH  /api/v1/vendor-rfqs/{id}/
DELETE /api/v1/vendor-rfqs/{id}/
POST   /api/v1/vendor-rfqs/{id}/send-to-vendors/
GET    /api/v1/vendor-rfqs/{id}/responses/

VENDOR QUOTES (from vendors)
GET    /api/v1/vendor-quotes/
POST   /api/v1/vendor-quotes/
GET    /api/v1/vendor-quotes/{id}/
PATCH  /api/v1/vendor-quotes/{id}/
POST   /api/v1/vendor-quotes/{id}/evaluate/
POST   /api/v1/vendor-quotes/{id}/award/
GET    /api/v1/vendor-quotes/comparison/  # Compare multiple vendor quotes

PURCHASE ORDERS
GET    /api/v1/purchase-orders/
POST   /api/v1/purchase-orders/
GET    /api/v1/purchase-orders/{id}/
PATCH  /api/v1/purchase-orders/{id}/
DELETE /api/v1/purchase-orders/{id}/
POST   /api/v1/purchase-orders/{id}/submit-for-approval/
POST   /api/v1/purchase-orders/{id}/approve/
POST   /api/v1/purchase-orders/{id}/send/
POST   /api/v1/purchase-orders/{id}/acknowledge/
POST   /api/v1/purchase-orders/{id}/receive/
POST   /api/v1/purchase-orders/{id}/generate-pdf/
GET    /api/v1/purchase-orders/{id}/items/

GOODS RECEIPTS
GET    /api/v1/goods-receipts/
POST   /api/v1/goods-receipts/
GET    /api/v1/goods-receipts/{id}/
PATCH  /api/v1/goods-receipts/{id}/

CUSTOM FIELDS
GET    /api/v1/custom-fields/
POST   /api/v1/custom-fields/
GET    /api/v1/custom-fields/{id}/
PATCH  /api/v1/custom-fields/{id}/
DELETE /api/v1/custom-fields/{id}/

NOTIFICATIONS
GET    /api/v1/notifications/
GET    /api/v1/notifications/unread/
POST   /api/v1/notifications/{id}/mark-read/
POST   /api/v1/notifications/mark-all-read/
DELETE /api/v1/notifications/{id}/

EMAIL TEMPLATES
GET    /api/v1/email-templates/
POST   /api/v1/email-templates/
GET    /api/v1/email-templates/{id}/
PATCH  /api/v1/email-templates/{id}/
DELETE /api/v1/email-templates/{id}/
POST   /api/v1/email-templates/{id}/preview/

DOCUMENT TEMPLATES
GET    /api/v1/document-templates/
POST   /api/v1/document-templates/
GET    /api/v1/document-templates/{id}/
PATCH  /api/v1/document-templates/{id}/
DELETE /api/v1/document-templates/{id}/
POST   /api/v1/document-templates/{id}/set-default/
POST   /api/v1/document-templates/{id}/preview/

WORKFLOW RULES
GET    /api/v1/workflow-rules/
POST   /api/v1/workflow-rules/
GET    /api/v1/workflow-rules/{id}/
PATCH  /api/v1/workflow-rules/{id}/
DELETE /api/v1/workflow-rules/{id}/
POST   /api/v1/workflow-rules/{id}/test/
GET    /api/v1/workflow-rules/{id}/executions/

AUDIT LOGS
GET    /api/v1/audit-logs/
GET    /api/v1/audit-logs/entity/{entity_type}/{entity_id}/
GET    /api/v1/audit-logs/user/{user_id}/

REPORTS & ANALYTICS
GET    /api/v1/reports/pipeline-summary/
GET    /api/v1/reports/sales-forecast/
GET    /api/v1/reports/territory-performance/
GET    /api/v1/reports/win-loss-analysis/
GET    /api/v1/reports/conversion-funnel/
GET    /api/v1/reports/activity-summary/
GET    /api/v1/reports/dso-analysis/
GET    /api/v1/reports/aging-report/
GET    /api/v1/reports/vendor-performance/
GET    /api/v1/reports/quota-attainment/
POST   /api/v1/reports/custom/  # Custom report builder
GET    /api/v1/reports/export/{report_id}/

DASHBOARDS
GET    /api/v1/dashboards/
POST   /api/v1/dashboards/
GET    /api/v1/dashboards/{id}/
PATCH  /api/v1/dashboards/{id}/
DELETE /api/v1/dashboards/{id}/
GET    /api/v1/dashboards/{id}/widgets/
POST   /api/v1/dashboards/{id}/widgets/
GET    /api/v1/dashboards/default/

SEARCH (Global)
GET    /api/v1/search/?q={query}&entity_type={type}

FILE UPLOADS
POST   /api/v1/files/upload/
GET    /api/v1/files/{id}/
DELETE /api/v1/files/{id}/

"""

# ========================================
# SERIALIZER EXAMPLE (for reference)
# ========================================

from rest_framework import serializers
from .models import Account, Contact, Lead, Deal

class AccountSerializer(serializers.ModelSerializer):
    """Account serializer with nested relationships"""
    
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    territory_name = serializers.CharField(source='territory.name', read_only=True)
    contacts_count = serializers.SerializerMethodField()
    deals_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            'id', 'name', 'legal_name', 'account_number', 'website',
            'account_type', 'industry', 'annual_revenue', 'employee_count',
            'phone', 'email',
            'billing_address_line1', 'billing_address_line2', 'billing_city',
            'billing_state', 'billing_postal_code', 'billing_country',
            'shipping_address_line1', 'shipping_address_line2', 'shipping_city',
            'shipping_state', 'shipping_postal_code', 'shipping_country',
            'parent_account', 'territory', 'territory_name', 'owner', 'owner_name',
            'payment_terms', 'credit_limit', 'tax_id',
            'custom_fields', 'is_active',
            'contacts_count', 'deals_count',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_contacts_count(self, obj):
        return obj.contacts.count()
    
    def get_deals_count(self, obj):
        return obj.deals.count()

class ContactSerializer(serializers.ModelSerializer):
    """Contact serializer"""
    
    account_name = serializers.CharField(source='account.name', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'title', 'department',
            'email', 'phone', 'mobile',
            'linkedin_url', 'twitter_handle',
            'account', 'account_name', 'reports_to', 'owner', 'owner_name',
            'mailing_address_line1', 'mailing_address_line2', 'mailing_city',
            'mailing_state', 'mailing_postal_code', 'mailing_country',
            'email_opt_out', 'do_not_call',
            'custom_fields', 'is_active',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'full_name', 'created_at', 'updated_at']

# ========================================
# VIEWSET EXAMPLE
# ========================================

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

class AccountViewSet(viewsets.ModelViewSet):
    """
    Account ViewSet with CRUD operations
    
    list: GET /api/v1/accounts/
    create: POST /api/v1/accounts/
    retrieve: GET /api/v1/accounts/{id}/
    update: PUT /api/v1/accounts/{id}/
    partial_update: PATCH /api/v1/accounts/{id}/
    destroy: DELETE /api/v1/accounts/{id}/
    """
    
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account_type', 'industry', 'territory', 'owner', 'is_active']
    search_fields = ['name', 'legal_name', 'email', 'phone', 'website']
    ordering_fields = ['name', 'created_at', 'annual_revenue']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter by company based on user's active company"""
        user = self.request.user
        # Get active company from session or user's primary company
        active_company_id = self.request.session.get('active_company_id')
        return Account.objects.filter(company_id=active_company_id)
    
    def perform_create(self, serializer):
        """Set company and created_by on creation"""
        active_company_id = self.request.session.get('active_company_id')
        serializer.save(
            company_id=active_company_id,
            created_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """
        GET /api/v1/accounts/{id}/contacts/
        Get all contacts for this account
        """
        account = self.get_object()
        contacts = account.contacts.all()
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def deals(self, request, pk=None):
        """
        GET /api/v1/accounts/{id}/deals/
        Get all deals for this account
        """
        account = self.get_object()
        deals = account.deals.all()
        serializer = DealSerializer(deals, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """
        GET /api/v1/accounts/{id}/activities/
        Get all activities for this account
        """
        account = self.get_object()
        activities = Activity.objects.filter(
            related_to_type='account',
            related_to_id=account.id
        ).order_by('-activity_date')
        serializer = ActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """
        POST /api/v1/accounts/import/
        Import accounts from CSV
        """
        # Handle CSV import logic
        pass
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """
        GET /api/v1/accounts/export/
        Export accounts to CSV
        """
        # Handle CSV export logic
        pass

# ========================================
# URL ROUTING EXAMPLE
# ========================================

from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# Register all viewsets
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'user-access', UserCompanyAccessViewSet, basename='user-access')
router.register(r'territories', TerritoryViewSet, basename='territory')
router.register(r'territory-rules', TerritoryRuleViewSet, basename='territory-rule')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'deals', DealViewSet, basename='deal')
router.register(r'pipeline-stages', PipelineStageViewSet, basename='pipeline-stage')
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'events', EventViewSet, basename='event')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-categories', ProductCategoryViewSet, basename='product-category')
router.register(r'price-lists', PriceListViewSet, basename='price-list')
router.register(r'rfqs', RFQViewSet, basename='rfq')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'quote-templates', QuoteTemplateViewSet, basename='quote-template')
router.register(r'sales-orders', SalesOrderViewSet, basename='sales-order')
router.register(r'shipments', ShipmentViewSet, basename='shipment')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'vendor-contacts', VendorContactViewSet, basename='vendor-contact')
router.register(r'vendor-scorecards', VendorScorecardViewSet, basename='vendor-scorecard')
router.register(r'purchase-requisitions', PurchaseRequisitionViewSet, basename='purchase-requisition')
router.register(r'vendor-rfqs', VendorRFQViewSet, basename='vendor-rfq')
router.register(r'vendor-quotes', VendorQuoteViewSet, basename='vendor-quote')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'goods-receipts', GoodsReceiptViewSet, basename='goods-receipt')
router.register(r'custom-fields', CustomFieldViewSet, basename='custom-field')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'email-templates', EmailTemplateViewSet, basename='email-template')
router.register(r'document-templates', DocumentTemplateViewSet, basename='document-template')
router.register(r'workflow-rules', WorkflowRuleViewSet, basename='workflow-rule')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'dashboards', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/', include('crm.urls.auth')),  # Auth endpoints
    path('api/v1/reports/', include('crm.urls.reports')),  # Reports endpoints
    path('api/v1/search/', GlobalSearchView.as_view(), name='global-search'),
]

# ========================================
# MIDDLEWARE FOR MULTI-TENANT ISOLATION
# ========================================

class MultiTenantMiddleware:
    """
    Middleware to set active company context for Row-Level Security
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Get active company from session or default to primary
            active_company_id = request.session.get('active_company_id')
            
            if not active_company_id:
                # Get user's primary company
                access = UserCompanyAccess.objects.filter(
                    user=request.user,
                    is_active=True,
                    is_primary=True
                ).first()
                
                if access:
                    active_company_id = str(access.company_id)
                    request.session['active_company_id'] = active_company_id
            
            # Set PostgreSQL session variable for RLS
            if active_company_id:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SET LOCAL app.current_user_id = %s",
                        [str(request.user.id)]
                    )
        
        response = self.get_response(request)
        return response

# ========================================
# PERMISSION CLASSES
# ========================================

from rest_framework.permissions import BasePermission

class HasCompanyAccess(BasePermission):
    """Check if user has access to the company"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        active_company_id = request.session.get('active_company_id')
        if not active_company_id:
            return False
        
        # Check if user has access to this company
        return UserCompanyAccess.objects.filter(
            user=request.user,
            company_id=active_company_id,
            is_active=True
        ).exists()

class CanCreateInCompany(BasePermission):
    """Check if user can create in active company"""
    
    def has_permission(self, request, view):
        if request.method != 'POST':
            return True
        
        active_company_id = request.session.get('active_company_id')
        access = UserCompanyAccess.objects.filter(
            user=request.user,
            company_id=active_company_id,
            is_active=True,
            can_create=True
        ).exists()
        
        return access

class CanDeleteInCompany(BasePermission):
    """Check if user can delete in active company"""
    
    def has_permission(self, request, view):
        if request.method != 'DELETE':
            return True
        
        active_company_id = request.session.get('active_company_id')
        access = UserCompanyAccess.objects.filter(
            user=request.user,
            company_id=active_company_id,
            is_active=True,
            can_delete=True
        ).exists()
        
        return access

# ========================================
# PAGINATION
# ========================================

from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100

# ========================================
# FILTERS
# ========================================

import django_filters

class AccountFilter(django_filters.FilterSet):
    """Advanced filtering for accounts"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    annual_revenue_min = django_filters.NumberFilter(field_name='annual_revenue', lookup_expr='gte')
    annual_revenue_max = django_filters.NumberFilter(field_name='annual_revenue', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Account
        fields = ['account_type', 'industry', 'territory', 'owner', 'is_active']

# ========================================
# API DOCUMENTATION
# ========================================

"""
All endpoints return JSON responses in the following format:

SUCCESS Response (200, 201):
{
    "id": "uuid",
    "field1": "value1",
    "field2": "value2",
    ...
}

LIST Response (200):
{
    "count": 100,
    "next": "http://api/next-page",
    "previous": null,
    "results": [
        {...},
        {...}
    ]
}

ERROR Response (400, 404, 500):
{
    "error": "Error message",
    "details": {...}
}

AUTHENTICATION:
All API requests require JWT token in header:
Authorization: Bearer <access_token>

MULTI-TENANT:
Active company is determined by session.
Switch company: POST /api/v1/companies/{id}/switch/
"""