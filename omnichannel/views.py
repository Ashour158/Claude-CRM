# omnichannel/views.py
# Omnichannel Communication Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Avg, Count, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .models import (
    CommunicationChannel, Conversation, Message, ConversationTemplate,
    ConversationRule, ConversationMetric, ConversationAnalytics
)
from .serializers import (
    CommunicationChannelSerializer, ConversationSerializer, MessageSerializer,
    ConversationTemplateSerializer, ConversationRuleSerializer,
    ConversationMetricSerializer, ConversationAnalyticsSerializer,
    ConversationCreateSerializer, MessageCreateSerializer
)
from core.permissions import CompanyIsolationPermission

logger = logging.getLogger(__name__)

class CommunicationChannelViewSet(viewsets.ModelViewSet):
    """Communication channel management"""
    
    queryset = CommunicationChannel.objects.all()
    serializer_class = CommunicationChannelSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['channel_type', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'total_conversations']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test channel connection"""
        channel = self.get_object()
        
        try:
            # TODO: Implement actual connection testing
            # This would involve testing the channel's credentials and configuration
            
            # Simulate connection test
            is_connected = True  # Replace with actual test
            response_time = 150  # Replace with actual response time
            
            return Response({
                'status': 'success' if is_connected else 'failed',
                'response_time_ms': response_time,
                'message': 'Connection test successful' if is_connected else 'Connection test failed'
            })
            
        except Exception as e:
            logger.error(f"Channel connection test failed: {str(e)}")
            return Response(
                {'error': 'Connection test failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get channel statistics"""
        channel = self.get_object()
        
        # Calculate statistics
        total_conversations = channel.conversations.count()
        active_conversations = channel.conversations.filter(status__in=['new', 'open', 'pending']).count()
        
        # Average response time
        avg_response_time = channel.conversations.filter(
            first_response_time__isnull=False
        ).aggregate(avg_time=Avg('first_response_time'))['avg_time'] or 0
        
        # Customer satisfaction
        satisfaction = channel.customer_satisfaction
        
        # Recent activity
        recent_conversations = channel.conversations.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return Response({
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'average_response_time': round(avg_response_time, 2),
            'customer_satisfaction': satisfaction,
            'recent_conversations': recent_conversations
        })

class ConversationViewSet(viewsets.ModelViewSet):
    """Conversation management"""
    
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['channel', 'status', 'priority', 'assigned_agent']
    search_fields = ['subject', 'description']
    ordering_fields = ['created_at', 'last_activity', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign conversation to agent"""
        conversation = self.get_object()
        agent_id = request.data.get('agent_id')
        
        if not agent_id:
            return Response(
                {'error': 'Agent ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from core.models import User
            agent = User.objects.get(id=agent_id, company=conversation.company)
            
            conversation.assigned_agent = agent
            conversation.status = 'open'
            conversation.save()
            
            return Response({
                'status': 'success',
                'assigned_agent': agent.get_full_name(),
                'conversation_id': str(conversation.id)
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Agent not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close conversation"""
        conversation = self.get_object()
        
        resolution_notes = request.data.get('resolution_notes', '')
        
        conversation.status = 'resolved'
        conversation.resolved_at = timezone.now()
        conversation.metadata['resolution_notes'] = resolution_notes
        conversation.save()
        
        return Response({
            'status': 'success',
            'resolved_at': conversation.resolved_at.isoformat()
        })
    
    @action(detail=True, methods=['post'])
    def escalate(self, request, pk=None):
        """Escalate conversation"""
        conversation = self.get_object()
        
        escalation_reason = request.data.get('escalation_reason', '')
        escalation_level = request.data.get('escalation_level', 'supervisor')
        
        conversation.status = 'escalated'
        conversation.priority = 'high'
        conversation.metadata['escalation_reason'] = escalation_reason
        conversation.metadata['escalation_level'] = escalation_level
        conversation.save()
        
        return Response({
            'status': 'success',
            'escalated_at': timezone.now().isoformat(),
            'escalation_level': escalation_level
        })
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get conversation messages"""
        conversation = self.get_object()
        messages = conversation.messages.all().order_by('created_at')
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send message in conversation"""
        conversation = self.get_object()
        
        serializer = MessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create message
            message = Message.objects.create(
                conversation=conversation,
                content=serializer.validated_data['content'],
                content_type=serializer.validated_data.get('content_type', 'text/plain'),
                sender=request.user,
                recipient=conversation.customer,
                direction='outgoing',
                message_type='outbound'
            )
            
            # Update conversation
            conversation.last_activity = timezone.now()
            conversation.save()
            
            # TODO: Send message through channel
            # This would involve calling the appropriate channel service
            
            return Response({
                'status': 'success',
                'message_id': str(message.id),
                'sent_at': message.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return Response(
                {'error': 'Failed to send message'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get conversation dashboard data"""
        queryset = self.get_queryset()
        
        # Calculate metrics
        total_conversations = queryset.count()
        active_conversations = queryset.filter(
            status__in=['new', 'open', 'pending']
        ).count()
        
        # Status breakdown
        status_breakdown = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Channel breakdown
        channel_breakdown = queryset.values('channel__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Priority breakdown
        priority_breakdown = queryset.values('priority').annotate(
            count=Count('id')
        ).order_by('priority')
        
        # Recent activity
        recent_conversations = queryset.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # SLA metrics
        sla_breaches = queryset.filter(
            sla_deadline__lt=timezone.now(),
            status__in=['new', 'open', 'pending']
        ).count()
        
        return Response({
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'recent_conversations': recent_conversations,
            'sla_breaches': sla_breaches,
            'status_breakdown': list(status_breakdown),
            'channel_breakdown': list(channel_breakdown),
            'priority_breakdown': list(priority_breakdown)
        })

class MessageViewSet(viewsets.ModelViewSet):
    """Message management"""
    
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['conversation', 'message_type', 'direction', 'sender', 'recipient']
    search_fields = ['content']
    ordering_fields = ['created_at', 'is_read', 'is_delivered']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        
        message.is_read = True
        message.save()
        
        return Response({'status': 'success'})
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """Mark message as delivered"""
        message = self.get_object()
        
        message.is_delivered = True
        message.save()
        
        return Response({'status': 'success'})

class ConversationTemplateViewSet(viewsets.ModelViewSet):
    """Conversation template management"""
    
    queryset = ConversationTemplate.objects.all()
    serializer_class = ConversationTemplateSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template_type', 'is_active', 'is_public', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'usage_count', 'last_used']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Use template in a conversation"""
        template = self.get_object()
        conversation_id = request.data.get('conversation_id')
        variables = request.data.get('variables', {})
        
        if not conversation_id:
            return Response(
                {'error': 'Conversation ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Process template with variables
            subject = self._process_template(template.subject_template, variables)
            content = self._process_template(template.content_template, variables)
            
            # Update usage statistics
            template.usage_count += 1
            template.last_used = timezone.now()
            template.save()
            
            return Response({
                'subject': subject,
                'content': content,
                'template_name': template.name
            })
            
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _process_template(self, template: str, variables: dict) -> str:
        """Process template with variables"""
        # Simple template processing - in practice, use a proper templating engine
        result = template
        for key, value in variables.items():
            result = result.replace(f'{{{key}}}', str(value))
        return result

class ConversationRuleViewSet(viewsets.ModelViewSet):
    """Conversation rule management"""
    
    queryset = ConversationRule.objects.all()
    serializer_class = ConversationRuleSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rule_type', 'trigger_condition', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'priority', 'execution_count']
    ordering = ['-priority', 'name']
    
    @action(detail=True, methods=['post'])
    def test_rule(self, request, pk=None):
        """Test rule execution"""
        rule = self.get_object()
        test_data = request.data.get('test_data', {})
        
        try:
            # TODO: Implement actual rule testing
            # This would involve evaluating the rule conditions against test data
            
            # Simulate rule execution
            would_trigger = True  # Replace with actual rule evaluation
            actions = rule.actions
            
            return Response({
                'would_trigger': would_trigger,
                'actions': actions,
                'rule_name': rule.name
            })
            
        except Exception as e:
            logger.error(f"Rule test failed: {str(e)}")
            return Response(
                {'error': 'Rule test failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def execute_rule(self, request, pk=None):
        """Manually execute rule"""
        rule = self.get_object()
        conversation_id = request.data.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {'error': 'Conversation ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            
            # TODO: Implement actual rule execution
            # This would involve executing the rule actions on the conversation
            
            # Update execution statistics
            rule.execution_count += 1
            rule.success_count += 1
            rule.last_executed = timezone.now()
            rule.save()
            
            return Response({
                'status': 'success',
                'rule_name': rule.name,
                'executed_at': timezone.now().isoformat()
            })
            
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ConversationMetricViewSet(viewsets.ModelViewSet):
    """Conversation metric management"""
    
    queryset = ConversationMetric.objects.all()
    serializer_class = ConversationMetricSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['metric_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'target_value']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def calculate_metric(self, request, pk=None):
        """Calculate metric value"""
        metric = self.get_object()
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        
        if not period_start or not period_end:
            return Response(
                {'error': 'Period start and end are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # TODO: Implement actual metric calculation
            # This would involve calculating the metric based on the specified period
            
            # Simulate metric calculation
            current_value = 85.5  # Replace with actual calculation
            previous_value = 82.3  # Replace with actual calculation
            
            # Calculate trend
            if previous_value > 0:
                trend_percentage = ((current_value - previous_value) / previous_value) * 100
                trend_direction = 'up' if trend_percentage > 0 else 'down' if trend_percentage < 0 else 'stable'
            else:
                trend_percentage = 0
                trend_direction = 'stable'
            
            # Determine status
            if metric.target_value:
                if current_value >= metric.target_value:
                    status = 'good'
                elif metric.warning_threshold and current_value < metric.warning_threshold:
                    status = 'warning'
                else:
                    status = 'critical'
            else:
                status = 'good'
            
            return Response({
                'current_value': current_value,
                'previous_value': previous_value,
                'target_value': metric.target_value,
                'trend_direction': trend_direction,
                'trend_percentage': round(trend_percentage, 2),
                'status': status
            })
            
        except Exception as e:
            logger.error(f"Metric calculation failed: {str(e)}")
            return Response(
                {'error': 'Metric calculation failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ConversationAnalyticsViewSet(viewsets.ModelViewSet):
    """Conversation analytics management"""
    
    queryset = ConversationAnalytics.objects.all()
    serializer_class = ConversationAnalyticsSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['metric', 'status']
    ordering_fields = ['period_start', 'period_end', 'current_value']
    ordering = ['-period_end']
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get analytics dashboard"""
        queryset = self.get_queryset()
        
        # Get recent analytics
        recent_analytics = queryset.filter(
            period_end__gte=timezone.now() - timedelta(days=30)
        ).order_by('-period_end')
        
        # Calculate summary metrics
        total_metrics = queryset.count()
        good_status = queryset.filter(status='good').count()
        warning_status = queryset.filter(status='warning').count()
        critical_status = queryset.filter(status='critical').count()
        
        # Trend analysis
        trending_up = queryset.filter(trend_direction='up').count()
        trending_down = queryset.filter(trend_direction='down').count()
        trending_stable = queryset.filter(trend_direction='stable').count()
        
        return Response({
            'total_metrics': total_metrics,
            'status_breakdown': {
                'good': good_status,
                'warning': warning_status,
                'critical': critical_status
            },
            'trend_breakdown': {
                'up': trending_up,
                'down': trending_down,
                'stable': trending_stable
            },
            'recent_analytics': ConversationAnalyticsSerializer(recent_analytics[:10], many=True).data
        })
