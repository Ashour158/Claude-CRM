# ai_assistant/views.py
# AI Assistant and Predictive Analytics Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Avg, Count
from django.utils import timezone
import openai
import json
import logging

from .models import AIAssistant, AIInteraction, PredictiveModel, Prediction, AnomalyDetection
from .serializers import (
    AIAssistantSerializer, AIInteractionSerializer, 
    PredictiveModelSerializer, PredictionSerializer, 
    AnomalyDetectionSerializer, ChatRequestSerializer,
    PredictionRequestSerializer
)
from core.permissions import CompanyIsolationPermission

logger = logging.getLogger(__name__)

class AIAssistantViewSet(viewsets.ModelViewSet):
    """AI Assistant management"""
    
    queryset = AIAssistant.objects.all()
    serializer_class = AIAssistantSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['assistant_type', 'is_active', 'is_public']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'total_interactions']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        """Chat with AI assistant"""
        assistant = self.get_object()
        serializer = ChatRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get user input and context
            user_input = serializer.validated_data['user_input']
            context = serializer.validated_data.get('context', {})
            related_entity = serializer.validated_data.get('related_entity')
            
            # Prepare context data
            context_data = {
                'user_id': request.user.id,
                'company_id': request.user.active_company.id,
                'assistant_type': assistant.assistant_type,
                'context': context,
                'related_entity': related_entity
            }
            
            # Call AI service
            start_time = timezone.now()
            ai_response = self._call_ai_service(assistant, user_input, context_data)
            response_time = (timezone.now() - start_time).total_seconds() * 1000
            
            # Create interaction record
            interaction = AIInteraction.objects.create(
                assistant=assistant,
                user=request.user,
                interaction_type='chat',
                user_input=user_input,
                ai_response=ai_response['response'],
                context=context_data,
                response_time_ms=int(response_time),
                tokens_used=ai_response.get('tokens_used', 0),
                content_type=related_entity.get('content_type') if related_entity else None,
                object_id=related_entity.get('object_id') if related_entity else None
            )
            
            # Update assistant statistics
            assistant.total_interactions += 1
            assistant.save()
            
            return Response({
                'response': ai_response['response'],
                'interaction_id': interaction.id,
                'response_time_ms': int(response_time),
                'tokens_used': ai_response.get('tokens_used', 0)
            })
            
        except Exception as e:
            logger.error(f"AI Chat error: {str(e)}")
            return Response(
                {'error': 'Failed to process chat request'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Analyze data with AI assistant"""
        assistant = self.get_object()
        
        try:
            analysis_type = request.data.get('analysis_type')
            data = request.data.get('data', {})
            
            # Prepare analysis prompt
            prompt = self._prepare_analysis_prompt(analysis_type, data)
            
            # Call AI service
            ai_response = self._call_ai_service(assistant, prompt, {
                'analysis_type': analysis_type,
                'data': data
            })
            
            # Create interaction record
            interaction = AIInteraction.objects.create(
                assistant=assistant,
                user=request.user,
                interaction_type='analysis',
                user_input=prompt,
                ai_response=ai_response['response'],
                context={'analysis_type': analysis_type, 'data': data}
            )
            
            return Response({
                'analysis': ai_response['response'],
                'interaction_id': interaction.id
            })
            
        except Exception as e:
            logger.error(f"AI Analysis error: {str(e)}")
            return Response(
                {'error': 'Failed to process analysis request'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _call_ai_service(self, assistant, user_input, context_data):
        """Call external AI service (OpenAI, etc.)"""
        try:
            # Configure OpenAI client
            client = openai.OpenAI(api_key="your-openai-api-key")
            
            # Prepare messages
            messages = [
                {"role": "system", "content": f"You are a {assistant.assistant_type} assistant for a CRM system."},
                {"role": "user", "content": user_input}
            ]
            
            # Add context if available
            if context_data.get('context'):
                messages.insert(-1, {
                    "role": "system", 
                    "content": f"Context: {json.dumps(context_data['context'])}"
                })
            
            # Make API call
            response = client.chat.completions.create(
                model=assistant.model_name,
                messages=messages,
                temperature=assistant.temperature,
                max_tokens=assistant.max_tokens
            )
            
            return {
                'response': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"AI Service call failed: {str(e)}")
            return {
                'response': "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
                'tokens_used': 0
            }
    
    def _prepare_analysis_prompt(self, analysis_type, data):
        """Prepare analysis prompt based on type"""
        prompts = {
            'sales_trends': f"Analyze these sales trends: {json.dumps(data)}",
            'lead_quality': f"Analyze lead quality metrics: {json.dumps(data)}",
            'customer_behavior': f"Analyze customer behavior patterns: {json.dumps(data)}",
            'revenue_forecast': f"Analyze revenue forecasting data: {json.dumps(data)}"
        }
        
        return prompts.get(analysis_type, f"Analyze this data: {json.dumps(data)}")

class AIInteractionViewSet(viewsets.ModelViewSet):
    """AI Interaction management"""
    
    queryset = AIInteraction.objects.all()
    serializer_class = AIInteractionSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['assistant', 'interaction_type', 'user']
    search_fields = ['user_input', 'ai_response']
    ordering_fields = ['created_at', 'user_rating', 'response_time_ms']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate an AI interaction"""
        interaction = self.get_object()
        
        rating = request.data.get('rating')
        is_helpful = request.data.get('is_helpful')
        feedback = request.data.get('feedback', '')
        
        if rating is not None:
            interaction.user_rating = rating
        if is_helpful is not None:
            interaction.is_helpful = is_helpful
        if feedback:
            interaction.feedback = feedback
        
        interaction.save()
        
        # Update assistant statistics
        if interaction.user_rating and interaction.user_rating >= 4:
            interaction.assistant.successful_interactions += 1
            interaction.assistant.save()
        
        return Response({'status': 'Rating updated successfully'})
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get AI interaction analytics"""
        queryset = self.get_queryset()
        
        # Calculate metrics
        total_interactions = queryset.count()
        avg_rating = queryset.filter(user_rating__isnull=False).aggregate(
            avg_rating=Avg('user_rating')
        )['avg_rating'] or 0
        
        helpful_count = queryset.filter(is_helpful=True).count()
        helpful_rate = (helpful_count / total_interactions * 100) if total_interactions > 0 else 0
        
        avg_response_time = queryset.filter(response_time_ms__isnull=False).aggregate(
            avg_time=Avg('response_time_ms')
        )['avg_time'] or 0
        
        # Interaction types breakdown
        type_breakdown = queryset.values('interaction_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_interactions': total_interactions,
            'average_rating': round(avg_rating, 2),
            'helpful_rate': round(helpful_rate, 2),
            'average_response_time_ms': round(avg_response_time, 2),
            'interaction_types': list(type_breakdown)
        })

class PredictiveModelViewSet(viewsets.ModelViewSet):
    """Predictive Model management"""
    
    queryset = PredictiveModel.objects.all()
    serializer_class = PredictiveModelSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['model_type', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'accuracy']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def train(self, request, pk=None):
        """Train a predictive model"""
        model = self.get_object()
        
        try:
            # Get training data
            training_data = request.data.get('training_data', {})
            
            # Simulate model training
            model.status = 'training'
            model.save()
            
            # TODO: Implement actual model training
            # This would involve:
            # 1. Data preprocessing
            # 2. Feature engineering
            # 3. Model training
            # 4. Validation
            # 5. Performance metrics calculation
            
            # Simulate training completion
            model.status = 'active'
            model.accuracy = 0.85
            model.precision = 0.82
            model.recall = 0.88
            model.f1_score = 0.85
            model.last_trained = timezone.now()
            model.training_duration = 300  # 5 minutes
            model.training_samples = 1000
            model.save()
            
            return Response({
                'status': 'Model training completed',
                'accuracy': model.accuracy,
                'precision': model.precision,
                'recall': model.recall,
                'f1_score': model.f1_score
            })
            
        except Exception as e:
            model.status = 'error'
            model.save()
            logger.error(f"Model training error: {str(e)}")
            return Response(
                {'error': 'Model training failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def predict(self, request, pk=None):
        """Make predictions with a model"""
        model = self.get_object()
        
        if model.status != 'active':
            return Response(
                {'error': 'Model is not active'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PredictionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get prediction data
            entity_type = serializer.validated_data['entity_type']
            entity_id = serializer.validated_data['entity_id']
            input_features = serializer.validated_data['input_features']
            
            # TODO: Implement actual prediction
            # This would involve:
            # 1. Feature preprocessing
            # 2. Model inference
            # 3. Confidence calculation
            
            # Simulate prediction
            prediction_value = 0.75  # Simulated prediction
            confidence_score = 0.85  # Simulated confidence
            
            # Create prediction record
            content_type = ContentType.objects.get(model=entity_type)
            prediction = Prediction.objects.create(
                model=model,
                content_type=content_type,
                object_id=entity_id,
                prediction_value=prediction_value,
                confidence_score=confidence_score,
                input_features=input_features,
                model_version='1.0'
            )
            
            return Response({
                'prediction_id': prediction.id,
                'prediction_value': prediction_value,
                'confidence_score': confidence_score,
                'model_accuracy': model.accuracy
            })
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return Response(
                {'error': 'Prediction failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PredictionViewSet(viewsets.ModelViewSet):
    """Prediction management"""
    
    queryset = Prediction.objects.all()
    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['model', 'content_type']
    ordering_fields = ['created_at', 'prediction_value', 'confidence_score']
    ordering = ['-created_at']

class AnomalyDetectionViewSet(viewsets.ModelViewSet):
    """Anomaly Detection management"""
    
    queryset = AnomalyDetection.objects.all()
    serializer_class = AnomalyDetectionSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['anomaly_type', 'severity', 'is_resolved']
    search_fields = ['title', 'description']
    ordering_fields = ['detected_at', 'severity', 'anomaly_score']
    ordering = ['-detected_at']
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an anomaly"""
        anomaly = self.get_object()
        
        resolution_notes = request.data.get('resolution_notes', '')
        
        anomaly.is_resolved = True
        anomaly.resolved_at = timezone.now()
        anomaly.resolved_by = request.user
        anomaly.resolution_notes = resolution_notes
        anomaly.save()
        
        return Response({'status': 'Anomaly resolved successfully'})
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get anomaly detection summary"""
        queryset = self.get_queryset()
        
        # Calculate metrics
        total_anomalies = queryset.count()
        resolved_anomalies = queryset.filter(is_resolved=True).count()
        unresolved_anomalies = total_anomalies - resolved_anomalies
        
        # Severity breakdown
        severity_breakdown = queryset.values('severity').annotate(
            count=Count('id')
        ).order_by('severity')
        
        # Type breakdown
        type_breakdown = queryset.values('anomaly_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_anomalies': total_anomalies,
            'resolved_anomalies': resolved_anomalies,
            'unresolved_anomalies': unresolved_anomalies,
            'resolution_rate': (resolved_anomalies / total_anomalies * 100) if total_anomalies > 0 else 0,
            'severity_breakdown': list(severity_breakdown),
            'type_breakdown': list(type_breakdown)
        })
