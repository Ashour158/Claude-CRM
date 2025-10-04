# core/urls.py
# URL configuration for authentication endpoints

from django.urls import path
from core.views.auth import (
    RegisterView, LoginView, LogoutView,
    CurrentUserView, ChangePasswordView,
    PasswordResetRequestView, PasswordResetConfirmView,
    VerifyEmailView, UserCompaniesView, SwitchCompanyView,
    RefreshTokenView
)

app_name = 'auth'

urlpatterns = [
    # Registration & Login
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Current User
    path('me/', CurrentUserView.as_view(), name='current-user'),
    
    # Password Management
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Email Verification
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    
    # Company Management
    path('companies/', UserCompaniesView.as_view(), name='user-companies'),
    path('switch-company/', SwitchCompanyView.as_view(), name='switch-company'),
    
    # Token Management
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
]