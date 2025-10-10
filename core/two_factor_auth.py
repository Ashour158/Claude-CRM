# core/two_factor_auth.py
# Two-Factor Authentication implementation for Phase 9

import pyotp
import qrcode
from io import BytesIO
import base64
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.api_responses import APIResponse
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class TwoFactorAuthService:
    """Two-Factor Authentication service"""
    
    @staticmethod
    def generate_secret():
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp_uri(user, secret):
        """Get TOTP provisioning URI for QR code"""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'CRM System'
        )
    
    @staticmethod
    def generate_qr_code(uri):
        """Generate QR code image as base64"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify_token(secret, token):
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def setup_2fa(user):
        """Setup 2FA for a user"""
        if not hasattr(user, 'two_factor_secret') or not user.two_factor_secret:
            secret = TwoFactorAuthService.generate_secret()
            user.two_factor_secret = secret
            user.save(update_fields=['two_factor_secret'])
        else:
            secret = user.two_factor_secret
        
        uri = TwoFactorAuthService.get_totp_uri(user, secret)
        qr_code = TwoFactorAuthService.generate_qr_code(uri)
        
        return {
            'secret': secret,
            'qr_code': qr_code,
            'uri': uri
        }
    
    @staticmethod
    def enable_2fa(user, token):
        """Enable 2FA for a user after verifying token"""
        if not hasattr(user, 'two_factor_secret') or not user.two_factor_secret:
            return False, "2FA not set up. Please setup first."
        
        if not TwoFactorAuthService.verify_token(user.two_factor_secret, token):
            return False, "Invalid verification code."
        
        user.two_factor_enabled = True
        user.save(update_fields=['two_factor_enabled'])
        
        logger.info(f"2FA enabled for user {user.email}")
        return True, "2FA enabled successfully."
    
    @staticmethod
    def disable_2fa(user, token):
        """Disable 2FA for a user after verifying token"""
        if not user.two_factor_enabled:
            return False, "2FA is not enabled."
        
        if not TwoFactorAuthService.verify_token(user.two_factor_secret, token):
            return False, "Invalid verification code."
        
        user.two_factor_enabled = False
        user.two_factor_secret = ''
        user.save(update_fields=['two_factor_enabled', 'two_factor_secret'])
        
        logger.info(f"2FA disabled for user {user.email}")
        return True, "2FA disabled successfully."
    
    @staticmethod
    def generate_backup_codes(user, count=10):
        """Generate backup codes for 2FA"""
        import secrets
        codes = [secrets.token_hex(4) for _ in range(count)]
        return codes


class TwoFactorAuthSerializer(serializers.Serializer):
    """Serializer for 2FA operations"""
    token = serializers.CharField(max_length=6, min_length=6)


class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for 2FA setup response"""
    secret = serializers.CharField()
    qr_code = serializers.CharField()
    uri = serializers.CharField()


class TwoFactorAuthMixin:
    """Mixin to add 2FA endpoints to user viewsets"""
    
    @action(detail=False, methods=['post'], url_path='2fa/setup')
    def setup_2fa(self, request):
        """Setup 2FA for current user"""
        user = request.user
        
        try:
            setup_data = TwoFactorAuthService.setup_2fa(user)
            serializer = TwoFactorSetupSerializer(setup_data)
            return APIResponse.success(
                data=serializer.data,
                message="2FA setup initiated. Scan QR code with your authenticator app."
            )
        except Exception as e:
            logger.error(f"2FA setup failed for user {user.email}: {str(e)}")
            return APIResponse.server_error(
                message="Failed to setup 2FA. Please try again."
            )
    
    @action(detail=False, methods=['post'], url_path='2fa/enable')
    def enable_2fa(self, request):
        """Enable 2FA after verification"""
        user = request.user
        serializer = TwoFactorAuthSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.validation_error(serializer.errors)
        
        success, message = TwoFactorAuthService.enable_2fa(
            user, serializer.validated_data['token']
        )
        
        if success:
            return APIResponse.success(message=message)
        else:
            return APIResponse.error(message=message)
    
    @action(detail=False, methods=['post'], url_path='2fa/disable')
    def disable_2fa(self, request):
        """Disable 2FA after verification"""
        user = request.user
        serializer = TwoFactorAuthSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.validation_error(serializer.errors)
        
        success, message = TwoFactorAuthService.disable_2fa(
            user, serializer.validated_data['token']
        )
        
        if success:
            return APIResponse.success(message=message)
        else:
            return APIResponse.error(message=message)
    
    @action(detail=False, methods=['post'], url_path='2fa/verify')
    def verify_2fa(self, request):
        """Verify 2FA token"""
        user = request.user
        serializer = TwoFactorAuthSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.validation_error(serializer.errors)
        
        if not user.two_factor_enabled:
            return APIResponse.error(message="2FA is not enabled.")
        
        is_valid = TwoFactorAuthService.verify_token(
            user.two_factor_secret,
            serializer.validated_data['token']
        )
        
        if is_valid:
            return APIResponse.success(message="Token verified successfully.")
        else:
            return APIResponse.error(message="Invalid verification code.")
    
    @action(detail=False, methods=['post'], url_path='2fa/backup-codes')
    def generate_backup_codes(self, request):
        """Generate backup codes"""
        user = request.user
        
        if not user.two_factor_enabled:
            return APIResponse.error(message="2FA must be enabled to generate backup codes.")
        
        codes = TwoFactorAuthService.generate_backup_codes(user)
        return APIResponse.success(
            data={'backup_codes': codes},
            message="Backup codes generated. Store them securely."
        )
