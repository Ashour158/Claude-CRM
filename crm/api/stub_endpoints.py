# crm/api/stub_endpoints.py
# Stub endpoints for Phase 2 UX feature scaffolding

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def saved_views(request):
    """Stub endpoint for saved list views."""
    if request.method == 'GET':
        return Response({
            'message': 'Saved views endpoint - implementation pending',
            'views': []
        })
    else:
        return Response({
            'message': 'Create saved view - implementation pending',
            'status': 'TODO'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_actions(request):
    """Stub endpoint for bulk actions."""
    ids = request.data.get('ids', [])
    
    if not ids or not isinstance(ids, list):
        return Response(
            {'error': 'Invalid or missing ids array'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'message': 'Bulk action endpoint - implementation pending',
        'status': 'TODO',
        'affected_count': len(ids)
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_search(request):
    """Stub endpoint for global search."""
    query = request.query_params.get('q', '')
    
    if not query:
        return Response(
            {'error': 'Query parameter "q" is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'message': 'Global search endpoint - implementation pending',
        'query': query,
        'results': {},
        'total_count': 0
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def kanban_board(request):
    """Stub endpoint for kanban board."""
    return Response({
        'message': 'Kanban board endpoint - implementation pending',
        'stages': [],
        'total_pipeline_value': 0
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def settings_summary(request):
    """Stub endpoint for settings summary."""
    return Response({
        'message': 'Settings summary endpoint - implementation pending',
        'sections': []
    })
