# core/views.py
# Core views including health check and user management

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from .models import (
    Company, UserCompanyAccess, AuditLog, Permission, Role, UserRole,
    UserActivity, UserPreference, UserInvitation
)
from .serializers import (
    CompanySerializer, UserCompanyAccessSerializer, AuditLogSerializer,
    PermissionSerializer, RoleSerializer, UserRoleSerializer,
    UserActivitySerializer, UserPreferenceSerializer, UserInvitationSerializer,
    UserSerializer, UserDetailSerializer, BulkUserActionSerializer, UserStatsSerializer
)

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
    serializer = UserDetailSerializer(user)
    return Response(serializer.data)

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

class UserViewSet(viewsets.ModelViewSet):
    """Enhanced user management viewset"""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'email_verified']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['email', 'first_name', 'last_name', 'date_joined']
    ordering = ['-date_joined']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_queryset(self):
        # Filter users by company access
        company = getattr(self.request, 'company', None)
        if company:
            return User.objects.filter(
                company_access__company=company,
                company_access__is_active=True
            ).distinct()
        return User.objects.none()
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get user statistics"""
        company = getattr(request, 'company', None)
        users = User.objects.filter(
            company_access__company=company,
            company_access__is_active=True
        ).distinct()
        
        active_users = users.filter(is_active=True).count()
        inactive_users = users.filter(is_active=False).count()
        
        # Get pending invitations
        pending_invitations = UserInvitation.objects.filter(
            company=company,
            status='pending'
        ).count()
        
        # Get users by role
        users_by_role = UserCompanyAccess.objects.filter(
            company=company,
            is_active=True
        ).values('role').annotate(count=Count('user')).order_by('role')
        
        # Get recent activities
        recent_activities = UserActivity.objects.filter(
            user__company_access__company=company
        ).order_by('-created_at')[:10]
        
        data = {
            'total_users': users.count(),
            'active_users': active_users,
            'inactive_users': inactive_users,
            'pending_invitations': pending_invitations,
            'users_by_role': {item['role']: item['count'] for item in users_by_role},
            'recent_activities': UserActivitySerializer(recent_activities, many=True).data
        }
        
        serializer = UserStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on users"""
        serializer = BulkUserActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_ids = serializer.validated_data['user_ids']
        action_type = serializer.validated_data['action']
        
        users = User.objects.filter(id__in=user_ids)
        
        if action_type == 'activate':
            users.update(is_active=True)
        elif action_type == 'deactivate':
            users.update(is_active=False)
        elif action_type == 'delete':
            users.delete()
        
        return Response({'message': f'Successfully performed {action_type} on {users.count()} users'})
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """Get user activities"""
        user = self.get_object()
        activities = UserActivity.objects.filter(user=user).order_by('-created_at')[:50]
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)

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

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """Permission viewset"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['module']
    search_fields = ['name', 'description']

class RoleViewSet(viewsets.ModelViewSet):
    """Role management viewset"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_system_role']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        company = getattr(self.request, 'company', None)
        if company:
            return Role.objects.filter(company=company)
        return Role.objects.none()
    
    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        """Assign permissions to role"""
        role = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        
        permissions = Permission.objects.filter(id__in=permission_ids)
        role.permissions.set(permissions)
        
        return Response({'message': f'Assigned {permissions.count()} permissions to role'})

class UserRoleViewSet(viewsets.ModelViewSet):
    """User role assignment viewset"""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'role', 'is_active']
    
    def get_queryset(self):
        company = getattr(self.request, 'company', None)
        if company:
            return UserRole.objects.filter(role__company=company)
        return UserRole.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """User activity tracking viewset"""
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'activity_type', 'module']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        company = getattr(self.request, 'company', None)
        if company:
            return UserActivity.objects.filter(
                user__company_access__company=company
            )
        return UserActivity.objects.none()

class UserPreferenceViewSet(viewsets.ModelViewSet):
    """User preference management viewset"""
    queryset = UserPreference.objects.all()
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserPreference.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Get current user's preferences"""
        preference, created = UserPreference.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(preference)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_my_preferences(self, request):
        """Update current user's preferences"""
        preference, created = UserPreference.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class UserInvitationViewSet(viewsets.ModelViewSet):
    """User invitation management viewset"""
    queryset = UserInvitation.objects.all()
    serializer_class = UserInvitationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'company']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        company = getattr(self.request, 'company', None)
        if company:
            return UserInvitation.objects.filter(company=company)
        return UserInvitation.objects.none()
    
    def perform_create(self, serializer):
        company = getattr(self.request, 'company', None)
        expires_at = timezone.now() + timedelta(days=7)
        serializer.save(
            company=company,
            invited_by=self.request.user,
            expires_at=expires_at
        )
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend invitation"""
        invitation = self.get_object()
        if invitation.status == 'pending':
            invitation.expires_at = timezone.now() + timedelta(days=7)
            invitation.save()
            # Here you would send the invitation email
            return Response({'message': 'Invitation resent successfully'})
        return Response(
            {'error': 'Only pending invitations can be resent'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel invitation"""
        invitation = self.get_object()
        if invitation.status == 'pending':
            invitation.status = 'cancelled'
            invitation.save()
            return Response({'message': 'Invitation cancelled successfully'})
        return Response(
            {'error': 'Only pending invitations can be cancelled'},
            status=status.HTTP_400_BAD_REQUEST
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