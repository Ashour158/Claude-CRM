# core/views.py
# Core views including health check

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from django.utils import timezone
from .models import Company, UserCompanyAccess, AuditLog
from .serializers import CompanySerializer, UserCompanyAccessSerializer, AuditLogSerializer

User = get_user_model()

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'CRM system is running',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get current user profile"""
    user = request.user
    return Response({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'date_joined': user.date_joined,
        'company': getattr(request, 'company', None).name if hasattr(request, 'company') and request.company else None
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_status(request):
    """Get system status"""
    return Response({
        'status': 'operational',
        'timestamp': timezone.now().isoformat(),
        'user_count': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count()
    })

class CompanyViewSet(viewsets.ModelViewSet):
    """Company viewset"""
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Company.objects.filter(
            user_access__user=self.request.user,
            user_access__is_active=True
        )

class UserCompanyAccessViewSet(viewsets.ModelViewSet):
    """User company access viewset"""
    queryset = UserCompanyAccess.objects.all()
    serializer_class = UserCompanyAccessSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserCompanyAccess.objects.filter(user=self.request.user)

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log viewset"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AuditLog.objects.filter(
            company=getattr(self.request, 'company', None)
        )