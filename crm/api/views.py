# crm/api/views.py
"""
API views for CRM endpoints
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from crm.leads.models import Lead
from crm.leads.services.conversion_service import ConversionService
from crm.activities.selectors.timeline_selector import TimelineSelector
from core.models import Company


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def timeline_list(request):
    """
    GET /api/v1/activities/timeline/
    
    Fetch timeline events for an entity or organization
    
    Query params:
        - entity_type: Type of entity (account, contact, lead, deal)
        - entity_id: ID of the entity
        - event_types: Comma-separated list of event types
        - limit: Max number of events (default 50)
    """
    # Get organization from request context (set by middleware)
    organization = getattr(request, 'organization', None)
    if not organization:
        return Response(
            {'error': 'Organization not found in request context'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Parse query parameters
    entity_type = request.query_params.get('entity_type')
    entity_id = request.query_params.get('entity_id')
    event_types = request.query_params.get('event_types', '').split(',') if request.query_params.get('event_types') else None
    limit = int(request.query_params.get('limit', 50))
    
    # Get target object if specified
    target = None
    if entity_type and entity_id:
        # Map entity type to model
        model_map = {
            'account': 'crm.accounts.models.Account',
            'contact': 'crm.contacts.models.Contact',
            'lead': 'crm.leads.models.Lead',
            'deal': 'deals.models.Deal',
        }
        
        if entity_type in model_map:
            from django.apps import apps
            model_path = model_map[entity_type].split('.')
            model = apps.get_model(model_path[0], model_path[1]) if len(model_path) == 2 else apps.get_model('.'.join(model_path[:-1]), model_path[-1])
            try:
                target = model.objects.for_organization(organization).get(id=entity_id)
            except model.DoesNotExist:
                return Response(
                    {'error': f'{entity_type.capitalize()} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
    
    # Fetch timeline
    events = TimelineSelector.fetch_timeline(
        organization=organization,
        target=target,
        event_types=event_types,
        limit=limit
    )
    
    # Serialize events
    events_data = [
        {
            'id': str(event.id),
            'event_type': event.event_type,
            'title': event.title,
            'description': event.description,
            'event_date': event.event_date.isoformat(),
            'actor': {
                'id': str(event.actor.id) if event.actor else None,
                'name': event.actor.get_full_name() if event.actor else 'System',
                'email': event.actor.email if event.actor else None,
            } if event.actor else None,
            'metadata': event.metadata,
        }
        for event in events
    ]
    
    return Response({
        'count': len(events_data),
        'events': events_data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def convert_lead(request):
    """
    POST /api/v1/leads/convert/
    
    Convert a lead to Account, Contact, and optionally Deal
    
    Request body:
        - lead_id: ID of the lead to convert
        - create_deal: Whether to create a deal (default true)
        - deal_data: Optional deal-specific data
            - name: Deal name
            - amount: Deal amount
    """
    # Get organization from request context
    organization = getattr(request, 'organization', None)
    if not organization:
        return Response(
            {'error': 'Organization not found in request context'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Parse request data
    lead_id = request.data.get('lead_id')
    create_deal = request.data.get('create_deal', True)
    deal_data = request.data.get('deal_data', {})
    
    if not lead_id:
        return Response(
            {'error': 'lead_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get lead
    try:
        lead = Lead.objects.for_organization(organization).get(id=lead_id)
    except Lead.DoesNotExist:
        return Response(
            {'error': 'Lead not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if lead can be converted
    can_convert, reason = ConversionService.can_convert_lead(lead)
    if not can_convert:
        return Response(
            {'error': reason},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Convert lead
    try:
        account, contact, deal = ConversionService.convert_lead(
            lead=lead,
            create_deal=create_deal,
            deal_data=deal_data,
            user=request.user
        )
        
        return Response({
            'success': True,
            'message': 'Lead converted successfully',
            'account': {
                'id': str(account.id),
                'name': account.name,
            },
            'contact': {
                'id': str(contact.id),
                'name': contact.get_full_name(),
            },
            'deal': {
                'id': str(deal.id) if deal else None,
                'name': deal.name if deal else None,
                'amount': str(deal.amount) if deal else None,
            } if deal else None,
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
