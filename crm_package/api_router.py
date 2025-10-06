"""
CRM API Router - Future /api/v1/ URL structure.

This module defines the routing structure for the CRM API once domain
modules are fully migrated. The routes are commented out to avoid import
errors until the endpoints are implemented.

To enable a route:
1. Uncomment the path() entry
2. Ensure the corresponding api.urls module exists in the domain package
3. Update this file incrementally as each domain is migrated

Future URL structure:
    /api/v1/accounts/       - Account endpoints
    /api/v1/contacts/       - Contact endpoints
    /api/v1/leads/          - Lead endpoints
    /api/v1/deals/          - Deal endpoints
    /api/v1/activities/     - Activity endpoints
    /api/v1/products/       - Product endpoints
    /api/v1/marketing/      - Marketing endpoints
    /api/v1/vendors/        - Vendor endpoints
    /api/v1/sales/          - Sales/quote endpoints
    /api/v1/workflow/       - Workflow endpoints
    /api/v1/territories/    - Territory endpoints
    /api/v1/system/         - System configuration
"""

from django.urls import path, include

app_name = 'crm'

urlpatterns = [
    # Accounts
    # path('api/v1/accounts/', include('crm_package.accounts.api.urls')),
    
    # Contacts
    # path('api/v1/contacts/', include('crm_package.contacts.api.urls')),
    
    # Leads
    # path('api/v1/leads/', include('crm_package.leads.api.urls')),
    
    # Deals
    # path('api/v1/deals/', include('crm_package.deals.api.urls')),
    
    # Activities
    # path('api/v1/activities/', include('crm_package.activities.api.urls')),
    
    # Products
    # path('api/v1/products/', include('crm_package.products.api.urls')),
    
    # Marketing
    # path('api/v1/marketing/', include('crm_package.marketing.api.urls')),
    
    # Vendors
    # path('api/v1/vendors/', include('crm_package.vendors.api.urls')),
    
    # Sales
    # path('api/v1/sales/', include('crm_package.sales.api.urls')),
    
    # Workflow
    # path('api/v1/workflow/', include('crm_package.workflow.api.urls')),
    
    # Territories
    # path('api/v1/territories/', include('crm_package.territories.api.urls')),
    
    # System
    # path('api/v1/system/', include('crm_package.system.api.urls')),
]
