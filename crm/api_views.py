# crm/api_views.py
# Phase 2 API Endpoints
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models import Q

from .models import Account, Contact, Lead
from activities.models import Activity
from deals.models import Deal


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activities_timeline(request):
    """
    GET /api/v1/activities/timeline/
    
    Returns a timeline of activities with optional filtering by:
    - object_type: app_label.model (e.g., "crm.account", "crm.lead")
    - object_id: specific record ID
    - activity_type: type of activity
    - date_from/date_to: date range
    
    Response structure:
    {
        "count": 123,
        "results": [
            {
                "id": "uuid",
                "activity_type": "call",
                "subject": "Follow-up call",
                "activity_date": "2024-01-15T10:30:00Z",
                "related_to": {
                    "type": "crm.lead",
                    "id": "lead-uuid",
                    "name": "Acme Corp"
                },
                "assigned_to": {
                    "id": "user-uuid",
                    "name": "John Doe"
                }
            }
        ]
    }
    """
    # Get query parameters
    object_type = request.GET.get('object_type')
    object_id = request.GET.get('object_id')
    activity_type = request.GET.get('activity_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Build queryset
    activities = Activity.objects.filter(company=request.user.company_access.first().company)
    
    # Apply filters
    if object_type:
        try:
            app_label, model = object_type.split('.')
            ct = ContentType.objects.get(app_label=app_label, model=model)
            activities = activities.filter(content_type=ct)
        except (ValueError, ContentType.DoesNotExist):
            return Response({'error': 'Invalid object_type pattern'}, status=status.HTTP_400_BAD_REQUEST)
    
    if object_id:
        activities = activities.filter(object_id=object_id)
    
    if activity_type:
        activities = activities.filter(activity_type=activity_type)
    
    if date_from:
        activities = activities.filter(activity_date__gte=date_from)
    
    if date_to:
        activities = activities.filter(activity_date__lte=date_to)
    
    # Order by date descending
    activities = activities.order_by('-activity_date')[:100]  # Limit for performance
    
    # Build response
    results = []
    for activity in activities:
        results.append({
            'id': str(activity.id) if hasattr(activity, 'id') else None,
            'activity_type': activity.activity_type,
            'subject': activity.subject,
            'activity_date': activity.activity_date.isoformat() if activity.activity_date else None,
            'related_to': {
                'type': f"{activity.content_type.app_label}.{activity.content_type.model}" if activity.content_type else None,
                'id': str(activity.object_id) if activity.object_id else None,
                'name': str(activity.content_object) if activity.content_object else None
            } if activity.content_type else None,
            'assigned_to': {
                'id': str(activity.assigned_to.id) if activity.assigned_to else None,
                'name': activity.assigned_to.get_full_name() if activity.assigned_to else None
            } if activity.assigned_to else None
        })
    
    return Response({
        'count': len(results),
        'results': results
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lead_convert(request, id):
    """
    POST /api/v1/leads/convert/<id>/
    
    Convert a lead to Account, Contact, and optionally Deal.
    
    Request body:
    {
        "create_account": true,
        "create_contact": true,
        "create_deal": false,
        "deal_amount": 50000.00,
        "deal_name": "Acme Corp Deal"
    }
    
    Response:
    {
        "success": true,
        "account": {"id": "uuid", "name": "Acme Corp"},
        "contact": {"id": "uuid", "name": "John Doe"},
        "deal": {"id": "uuid", "name": "Acme Corp Deal"} or null
    }
    """
    try:
        lead = Lead.objects.get(id=id, company=request.user.company_access.first().company)
    except Lead.DoesNotExist:
        return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if lead.status == 'converted':
        return Response({'error': 'Lead already converted'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Parse request parameters
    create_account = request.data.get('create_account', True)
    create_contact = request.data.get('create_contact', True)
    create_deal = request.data.get('create_deal', False)
    
    result = {
        'success': True,
        'account': None,
        'contact': None,
        'deal': None
    }
    
    # Create Account if requested
    if create_account and lead.company_name:
        account = Account.objects.create(
            company=lead.company,
            name=lead.company_name,
            industry=lead.industry,
            phone=lead.phone,
            website=lead.website,
            billing_city=lead.city,
            billing_state=lead.state,
            billing_country=lead.country,
            owner=lead.owner
        )
        result['account'] = {'id': str(account.id), 'name': account.name}
        lead.converted_account = account
    
    # Create Contact if requested
    if create_contact:
        contact = Contact.objects.create(
            company=lead.company,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            mobile=lead.mobile,
            title=lead.title,
            account=result['account'] and Account.objects.get(id=result['account']['id']) or None,
            owner=lead.owner
        )
        result['contact'] = {'id': str(contact.id), 'name': contact.full_name}
        lead.converted_contact = contact
    
    # Create Deal if requested
    if create_deal:
        deal_name = request.data.get('deal_name', f"{lead.company_name or lead.full_name} - Deal")
        deal_amount = request.data.get('deal_amount', lead.budget)
        
        deal = Deal.objects.create(
            company=lead.company,
            name=deal_name,
            amount=deal_amount,
            account=result['account'] and Account.objects.get(id=result['account']['id']) or None,
            contact=result['contact'] and Contact.objects.get(id=result['contact']['id']) or None,
            stage='prospecting',
            status='open',
            owner=lead.owner
        )
        result['deal'] = {'id': str(deal.id), 'name': deal.name}
    
    # Update lead status
    lead.status = 'converted'
    lead.converted_at = timezone.now()
    lead.save()
    
    return Response(result)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def saved_views(request):
    """
    GET|POST /api/v1/meta/saved-views/
    
    Manage saved views (filters, columns, sorting) for list pages.
    
    GET Response:
    {
        "results": [
            {
                "id": "uuid",
                "name": "My Open Leads",
                "entity_type": "lead",
                "definition": {
                    "filters": {"status": "open", "owner": "me"},
                    "columns": ["name", "company", "status", "created_at"],
                    "sort": ["-created_at"]
                },
                "is_default": false
            }
        ]
    }
    
    POST Request:
    {
        "name": "My Open Leads",
        "entity_type": "lead",
        "definition": {
            "filters": {"status": "open"},
            "columns": ["name", "status"],
            "sort": ["-created_at"]
        }
    }
    """
    if request.method == 'GET':
        # Return stub saved views (in-memory placeholder)
        return Response({
            'results': [
                {
                    'id': '1',
                    'name': 'All Open Leads',
                    'entity_type': 'lead',
                    'definition': {
                        'filters': {'status': 'open'},
                        'columns': ['name', 'company_name', 'status', 'rating'],
                        'sort': ['-created_at']
                    },
                    'is_default': True
                },
                {
                    'id': '2',
                    'name': 'Hot Prospects',
                    'entity_type': 'lead',
                    'definition': {
                        'filters': {'rating': 'hot', 'status': 'qualified'},
                        'columns': ['name', 'company_name', 'budget', 'owner'],
                        'sort': ['-lead_score']
                    },
                    'is_default': False
                }
            ]
        })
    
    elif request.method == 'POST':
        # Validate POST data
        name = request.data.get('name')
        entity_type = request.data.get('entity_type')
        definition = request.data.get('definition', {})
        
        if not name:
            return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not entity_type:
            return Response({'error': 'entity_type is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(definition, dict):
            return Response({'error': 'definition must be an object'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate definition structure
        if 'filters' in definition and not isinstance(definition['filters'], dict):
            return Response({'error': 'definition.filters must be an object'}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'columns' in definition and not isinstance(definition['columns'], list):
            return Response({'error': 'definition.columns must be an array'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Return created saved view (stub - not persisted)
        return Response({
            'id': 'generated-uuid',
            'name': name,
            'entity_type': entity_type,
            'definition': definition,
            'is_default': False
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leads_bulk(request):
    """
    POST /api/v1/leads/bulk/
    
    Perform bulk operations on leads.
    
    Request body:
    {
        "action": "update_field",
        "lead_ids": ["uuid1", "uuid2", "uuid3"],
        "field": "status",
        "value": "contacted"
    }
    
    Supported actions: update_field, assign_owner, delete, add_tag
    
    Response:
    {
        "success": true,
        "processed": 3,
        "errors": []
    }
    """
    action = request.data.get('action')
    lead_ids = request.data.get('lead_ids', [])
    
    if not action:
        return Response({'error': 'action is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate action
    allowed_actions = ['update_field', 'assign_owner', 'delete', 'add_tag']
    if action not in allowed_actions:
        return Response({
            'error': f'Invalid action. Allowed: {", ".join(allowed_actions)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not lead_ids or not isinstance(lead_ids, list):
        return Response({'error': 'lead_ids must be a non-empty array'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Stub response - actual bulk operations not implemented
    return Response({
        'success': True,
        'processed': len(lead_ids),
        'errors': [],
        'message': f'Bulk {action} stub - not yet implemented'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_search(request):
    """
    GET /api/v1/search
    
    Global search across entities.
    
    Query parameters:
    - q: search query string
    - types: comma-separated entity types (account,contact,lead,deal)
    
    Response:
    {
        "query": "acme",
        "results": {
            "accounts": {
                "count": 5,
                "items": [{"id": "uuid", "name": "Acme Corp", "type": "account"}]
            },
            "contacts": {
                "count": 12,
                "items": [{"id": "uuid", "name": "John Doe", "type": "contact"}]
            },
            "leads": {
                "count": 3,
                "items": []
            },
            "deals": {
                "count": 8,
                "items": []
            }
        },
        "total_count": 28
    }
    """
    query = request.GET.get('q', '').strip()
    types = request.GET.get('types', 'account,contact,lead,deal').split(',')
    
    if not query:
        return Response({'error': 'q parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    company = request.user.company_access.first().company if hasattr(request.user, 'company_access') else None
    
    results = {}
    total_count = 0
    
    # Search accounts
    if 'account' in types and company:
        accounts = Account.objects.filter(
            company=company,
            name__icontains=query
        )[:5]
        results['accounts'] = {
            'count': accounts.count(),
            'items': [{'id': str(a.id), 'name': a.name, 'type': 'account'} for a in accounts]
        }
        total_count += accounts.count()
    
    # Search contacts
    if 'contact' in types and company:
        contacts = Contact.objects.filter(
            company=company
        ).filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query)
        )[:5]
        results['contacts'] = {
            'count': contacts.count(),
            'items': [{'id': str(c.id), 'name': c.full_name, 'type': 'contact'} for c in contacts]
        }
        total_count += contacts.count()
    
    # Search leads
    if 'lead' in types and company:
        leads = Lead.objects.filter(
            company=company
        ).filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(company_name__icontains=query)
        )[:5]
        results['leads'] = {
            'count': leads.count(),
            'items': [{'id': str(l.id), 'name': l.full_name or l.company_name, 'type': 'lead'} for l in leads]
        }
        total_count += leads.count()
    
    # Search deals (placeholder)
    if 'deal' in types:
        results['deals'] = {
            'count': 0,
            'items': []
        }
    
    return Response({
        'query': query,
        'results': results,
        'total_count': total_count
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def deals_board(request):
    """
    GET /api/v1/deals/board/
    
    Returns deals organized by kanban board stages.
    
    Response:
    {
        "stages": [
            {
                "code": "prospecting",
                "name": "Prospecting",
                "deals_count": 15,
                "total_amount": 500000,
                "items": [
                    {
                        "id": "uuid",
                        "name": "Acme Corp Deal",
                        "amount": 50000,
                        "account": {"id": "uuid", "name": "Acme Corp"},
                        "probability": 10
                    }
                ]
            }
        ]
    }
    """
    # Placeholder kanban board structure
    stages = [
        {
            'code': 'prospecting',
            'name': 'Prospecting',
            'deals_count': 0,
            'total_amount': 0,
            'items': []
        },
        {
            'code': 'qualification',
            'name': 'Qualification',
            'deals_count': 0,
            'total_amount': 0,
            'items': []
        },
        {
            'code': 'proposal',
            'name': 'Proposal',
            'deals_count': 0,
            'total_amount': 0,
            'items': []
        },
        {
            'code': 'negotiation',
            'name': 'Negotiation',
            'deals_count': 0,
            'total_amount': 0,
            'items': []
        },
        {
            'code': 'closed_won',
            'name': 'Closed Won',
            'deals_count': 0,
            'total_amount': 0,
            'items': []
        },
        {
            'code': 'closed_lost',
            'name': 'Closed Lost',
            'deals_count': 0,
            'total_amount': 0,
            'items': []
        }
    ]
    
    return Response({'stages': stages})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def settings_summary(request):
    """
    GET /api/v1/settings/summary/
    
    Returns consolidated settings and configuration summary.
    
    Response:
    {
        "company": {
            "name": "Acme Corp",
            "users_count": 25,
            "storage_used_mb": 1250
        },
        "modules": {
            "crm": {"enabled": true, "records_count": 1500},
            "deals": {"enabled": true, "records_count": 450},
            "activities": {"enabled": true, "records_count": 3200}
        },
        "custom_fields": {
            "total": 15,
            "by_entity": {
                "account": 5,
                "contact": 4,
                "lead": 3,
                "deal": 3
            }
        },
        "integrations": {
            "active": 3,
            "available": 12
        }
    }
    """
    company = request.user.company_access.first().company if hasattr(request.user, 'company_access') else None
    
    return Response({
        'company': {
            'name': company.name if company else 'Demo Company',
            'users_count': 0,
            'storage_used_mb': 0
        },
        'modules': {
            'crm': {'enabled': True, 'records_count': 0},
            'deals': {'enabled': True, 'records_count': 0},
            'activities': {'enabled': True, 'records_count': 0}
        },
        'custom_fields': {
            'total': 0,
            'by_entity': {
                'account': 0,
                'contact': 0,
                'lead': 0,
                'deal': 0
            }
        },
        'integrations': {
            'active': 0,
            'available': 0
        }
    })
