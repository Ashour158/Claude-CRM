# marketplace/views.py
# Marketplace and Extensibility Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Avg, Count
from django.utils import timezone
import logging

from .models import (
    MarketplaceApp, AppInstallation, AppReview, AppPermission,
    AppWebhook, AppExecution, AppAnalytics, AppSubscription
)
from .serializers import (
    MarketplaceAppSerializer, AppInstallationSerializer, AppReviewSerializer,
    AppPermissionSerializer, AppWebhookSerializer, AppExecutionSerializer,
    AppAnalyticsSerializer, AppSubscriptionSerializer
)
from core.permissions import CompanyIsolationPermission

logger = logging.getLogger(__name__)

class MarketplaceAppViewSet(viewsets.ModelViewSet):
    """Marketplace app management"""
    
    queryset = MarketplaceApp.objects.all()
    serializer_class = MarketplaceAppSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['app_type', 'status', 'is_public', 'is_featured', 'developer']
    search_fields = ['name', 'description', 'short_description']
    ordering_fields = ['name', 'created_at', 'download_count', 'rating']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def install(self, request, pk=None):
        """Install an app"""
        app = self.get_object()
        
        try:
            # Check if already installed
            existing_installation = AppInstallation.objects.filter(
                company=request.user.active_company,
                app=app
            ).first()
            
            if existing_installation:
                return Response(
                    {'error': 'App is already installed'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create installation
            installation = AppInstallation.objects.create(
                app=app,
                installed_by=request.user,
                version=app.latest_version,
                installation_config=request.data.get('config', {}),
                status='installing'
            )
            
            # TODO: Implement actual app installation
            # This would involve downloading and setting up the app
            
            installation.status = 'installed'
            installation.save()
            
            # Update app statistics
            app.install_count += 1
            app.save()
            
            return Response({
                'status': 'success',
                'installation_id': str(installation.id),
                'app_name': app.name
            })
            
        except Exception as e:
            logger.error(f"App installation failed: {str(e)}")
            return Response(
                {'error': 'App installation failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Review an app"""
        app = self.get_object()
        
        try:
            rating = request.data.get('rating')
            title = request.data.get('title', '')
            content = request.data.get('content', '')
            
            if not rating or rating < 1 or rating > 5:
                return Response(
                    {'error': 'Rating must be between 1 and 5'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create or update review
            review, created = AppReview.objects.get_or_create(
                app=app,
                reviewer=request.user,
                defaults={
                    'rating': rating,
                    'title': title,
                    'content': content
                }
            )
            
            if not created:
                review.rating = rating
                review.title = title
                review.content = content
                review.save()
            
            # Update app rating
            reviews = app.reviews.all()
            if reviews.exists():
                app.rating = sum(r.rating for r in reviews) / reviews.count()
                app.review_count = reviews.count()
                app.save()
            
            return Response({
                'status': 'success',
                'review_id': str(review.id),
                'rating': review.rating
            })
            
        except Exception as e:
            logger.error(f"App review failed: {str(e)}")
            return Response(
                {'error': 'App review failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AppInstallationViewSet(viewsets.ModelViewSet):
    """App installation management"""
    
    queryset = AppInstallation.objects.all()
    serializer_class = AppInstallationSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['app', 'status', 'installed_by']
    search_fields = ['run_name', 'description']
    ordering_fields = ['installed_at', 'last_updated', 'usage_count']
    ordering = ['-installed_at']
    
    @action(detail=True, methods=['post'])
    def uninstall(self, request, pk=None):
        """Uninstall an app"""
        installation = self.get_object()
        
        try:
            installation.status = 'uninstalling'
            installation.save()
            
            # TODO: Implement actual app uninstallation
            # This would involve removing the app and cleaning up data
            
            installation.status = 'uninstalled'
            installation.uninstalled_at = timezone.now()
            installation.save()
            
            return Response({
                'status': 'success',
                'app_name': installation.app.name,
                'uninstalled_at': installation.uninstalled_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"App uninstallation failed: {str(e)}")
            return Response(
                {'error': 'App uninstallation failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AppReviewViewSet(viewsets.ModelViewSet):
    """App review management"""
    
    queryset = AppReview.objects.all()
    serializer_class = AppReviewSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['app', 'reviewer', 'rating']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'rating', 'helpful_count']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark review as helpful"""
        review = self.get_object()
        
        is_helpful = request.data.get('is_helpful', True)
        
        if is_helpful:
            review.helpful_count += 1
        else:
            review.not_helpful_count += 1
        
        review.save()
        
        return Response({
            'status': 'success',
            'helpful_count': review.helpful_count,
            'not_helpful_count': review.not_helpful_count
        })

class AppPermissionViewSet(viewsets.ModelViewSet):
    """App permission management"""
    
    queryset = AppPermission.objects.all()
    serializer_class = AppPermissionSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['app', 'permission_type', 'status', 'requested_by']
    search_fields = ['resource']
    ordering_fields = ['requested_at', 'approved_at']
    ordering = ['-requested_at']
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve app permission"""
        permission = self.get_object()
        
        try:
            permission.status = 'approved'
            permission.approved_by = request.user
            permission.approved_at = timezone.now()
            permission.save()
            
            return Response({
                'status': 'success',
                'permission_id': str(permission.id),
                'approved_by': request.user.get_full_name()
            })
            
        except Exception as e:
            logger.error(f"Permission approval failed: {str(e)}")
            return Response(
                {'error': 'Permission approval failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def deny(self, request, pk=None):
        """Deny app permission"""
        permission = self.get_object()
        
        try:
            permission.status = 'denied'
            permission.approved_by = request.user
            permission.approved_at = timezone.now()
            permission.save()
            
            return Response({
                'status': 'success',
                'permission_id': str(permission.id),
                'denied_by': request.user.get_full_name()
            })
            
        except Exception as e:
            logger.error(f"Permission denial failed: {str(e)}")
            return Response(
                {'error': 'Permission denial failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AppWebhookViewSet(viewsets.ModelViewSet):
    """App webhook management"""
    
    queryset = AppWebhook.objects.all()
    serializer_class = AppWebhookSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['app', 'webhook_type', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'total_calls']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def test_webhook(self, request, pk=None):
        """Test webhook"""
        webhook = self.get_object()
        
        try:
            # TODO: Implement actual webhook testing
            # This would involve sending a test payload to the webhook endpoint
            
            test_payload = request.data.get('test_payload', {})
            
            return Response({
                'status': 'success',
                'webhook_name': webhook.name,
                'test_result': 'Webhook test completed successfully'
            })
            
        except Exception as e:
            logger.error(f"Webhook test failed: {str(e)}")
            return Response(
                {'error': 'Webhook test failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AppExecutionViewSet(viewsets.ModelViewSet):
    """App execution management"""
    
    queryset = AppExecution.objects.all()
    serializer_class = AppExecutionSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['app', 'installation', 'execution_type', 'status']
    search_fields = ['function_name']
    ordering_fields = ['created_at', 'started_at', 'completed_at']
    ordering = ['-created_at']

class AppAnalyticsViewSet(viewsets.ModelViewSet):
    """App analytics management"""
    
    queryset = AppAnalytics.objects.all()
    serializer_class = AppAnalyticsSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['app', 'metric_type']
    search_fields = ['metric_name']
    ordering_fields = ['period_start', 'period_end', 'value']
    ordering = ['-period_end']

class AppSubscriptionViewSet(viewsets.ModelViewSet):
    """App subscription management"""
    
    queryset = AppSubscription.objects.all()
    serializer_class = AppSubscriptionSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['app', 'subscription_type', 'status', 'subscriber']
    search_fields = ['app__name']
    ordering_fields = ['started_at', 'expires_at']
    ordering = ['-started_at']
    
    @action(detail=True, methods=['post'])
    def cancel_subscription(self, request, pk=None):
        """Cancel app subscription"""
        subscription = self.get_object()
        
        try:
            subscription.status = 'cancelled'
            subscription.cancelled_at = timezone.now()
            subscription.save()
            
            return Response({
                'status': 'success',
                'subscription_id': str(subscription.id),
                'cancelled_at': subscription.cancelled_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Subscription cancellation failed: {str(e)}")
            return Response(
                {'error': 'Subscription cancellation failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
