# core/views/auth.py
# Authentication views and API endpoints

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.utils import timezone
from datetime import timedelta
import secrets

from core.models import User, Company, UserCompanyAccess, UserSession
from core.serializers.auth import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, AuthTokenSerializer,
    MessageSerializer
)

# ========================================
# HELPER FUNCTIONS
# ========================================

def get_tokens_for_user(user):
    """Generate JWT tokens for user"""
    refresh = RefreshToken.for_user(user)
    
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'token_type': 'Bearer',
        'expires_in': 3600  # 1 hour in seconds
    }

def create_user_session(user, request, company=None):
    """Create a user session"""
    tokens = get_tokens_for_user(user)
    
    # Get user's primary company if not specified
    if not company:
        company = user.get_primary_company()
    
    # Create session
    session = UserSession.objects.create(
        user=user,
        company=company,
        token=tokens['access_token'],
        refresh_token=tokens['refresh_token'],
        expires_at=timezone.now() + timedelta(hours=1),
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Update user login info
    user.last_login_at = timezone.now()
    user.last_login_ip = get_client_ip(request)
    user.login_count += 1
    user.save()
    
    return tokens, session

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# ========================================
# REGISTRATION
# ========================================

class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Register a new user
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate email verification token
        user.email_verification_token = secrets.token_urlsafe(32)
        user.save()
        
        # TODO: Send verification email
        
        return Response({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

# ========================================
# LOGIN
# ========================================

class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    User login
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Create session and generate tokens
        tokens, session = create_user_session(user, request)
        
        # Set active company in session
        if session.company:
            request.session['active_company_id'] = str(session.company.id)
        
        response_data = {
            **tokens,
            'user': UserSerializer(user).data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

# ========================================
# LOGOUT
# ========================================

class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    User logout
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Delete user's active session
        # In production, get token from request header
        UserSession.objects.filter(user=request.user).delete()
        
        # Clear session
        request.session.flush()
        
        logout(request)
        
        return Response({
            'message': 'Successfully logged out.'
        }, status=status.HTTP_200_OK)

# ========================================
# CURRENT USER
# ========================================

class CurrentUserView(APIView):
    """
    GET /api/v1/auth/me/
    Get current user info
    
    PATCH /api/v1/auth/me/
    Update current user info
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# ========================================
# CHANGE PASSWORD
# ========================================

class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/
    Change user password
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Change password
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Invalidate all sessions
        UserSession.objects.filter(user=user).delete()
        
        return Response({
            'message': 'Password changed successfully. Please login again.'
        }, status=status.HTTP_200_OK)

# ========================================
# PASSWORD RESET
# ========================================

class PasswordResetRequestView(APIView):
    """
    POST /api/v1/auth/password-reset/
    Request password reset
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            user.password_reset_token = secrets.token_urlsafe(32)
            user.password_reset_expires = timezone.now() + timedelta(hours=24)
            user.save()
            
            # TODO: Send password reset email with token
            
        except User.DoesNotExist:
            # Don't reveal if email exists
            pass
        
        return Response({
            'message': 'If your email is registered, you will receive password reset instructions.'
        }, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    """
    POST /api/v1/auth/password-reset-confirm/
    Confirm password reset with token
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(
                password_reset_token=token,
                password_reset_expires__gt=timezone.now()
            )
            
            # Reset password
            user.set_password(new_password)
            user.password_reset_token = ''
            user.password_reset_expires = None
            user.save()
            
            # Invalidate all sessions
            UserSession.objects.filter(user=user).delete()
            
            return Response({
                'message': 'Password reset successful. You can now login with your new password.'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid or expired reset token.'
            }, status=status.HTTP_400_BAD_REQUEST)

# ========================================
# EMAIL VERIFICATION
# ========================================

class VerifyEmailView(APIView):
    """
    POST /api/v1/auth/verify-email/
    Verify email address
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email_verification_token=token)
            
            if user.email_verified:
                return Response({
                    'message': 'Email already verified.'
                }, status=status.HTTP_200_OK)
            
            user.email_verified = True
            user.email_verification_token = ''
            user.save()
            
            return Response({
                'message': 'Email verified successfully.'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid verification token.'
            }, status=status.HTTP_400_BAD_REQUEST)

# ========================================
# USER COMPANIES
# ========================================

class UserCompaniesView(APIView):
    """
    GET /api/v1/auth/companies/
    Get all companies user has access to
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get all user's company access
        accesses = UserCompanyAccess.objects.filter(
            user=user,
            is_active=True
        ).select_related('company')
        
        companies = []
        for access in accesses:
            companies.append({
                'id': str(access.company.id),
                'name': access.company.name,
                'code': access.company.code,
                'logo_url': access.company.logo_url,
                'role': access.role,
                'is_primary': access.is_primary,
                'permissions': {
                    'can_create': access.can_create,
                    'can_read': access.can_read,
                    'can_update': access.can_update,
                    'can_delete': access.can_delete,
                    'can_export': access.can_export,
                }
            })
        
        return Response(companies, status=status.HTTP_200_OK)

# ========================================
# SWITCH COMPANY
# ========================================

class SwitchCompanyView(APIView):
    """
    POST /api/v1/auth/switch-company/
    Switch active company
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        company_id = request.data.get('company_id')
        
        if not company_id:
            return Response({
                'error': 'company_id is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            company = Company.objects.get(id=company_id)
            
            # Check if user has access
            if not request.user.has_company_access(company):
                return Response({
                    'error': 'You do not have access to this company.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Set active company in session
            request.session['active_company_id'] = str(company.id)
            
            # Update user's active session
            UserSession.objects.filter(user=request.user).update(
                company=company
            )
            
            return Response({
                'message': 'Company switched successfully.',
                'company': {
                    'id': str(company.id),
                    'name': company.name,
                    'code': company.code,
                }
            }, status=status.HTTP_200_OK)
            
        except Company.DoesNotExist:
            return Response({
                'error': 'Company not found.'
            }, status=status.HTTP_404_NOT_FOUND)

# ========================================
# REFRESH TOKEN
# ========================================

class RefreshTokenView(APIView):
    """
    POST /api/v1/auth/refresh-token/
    Refresh access token using refresh token
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'refresh_token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            
            return Response({
                'access_token': str(refresh.access_token),
                'token_type': 'Bearer',
                'expires_in': 3600
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Invalid or expired refresh token.'
            }, status=status.HTTP_401_UNAUTHORIZED)