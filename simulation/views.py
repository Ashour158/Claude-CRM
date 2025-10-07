# simulation/views.py
# What-If Analysis and Simulation Views

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
    SimulationScenario, SimulationRun, SimulationModel,
    SimulationResult, OptimizationTarget, SensitivityAnalysis,
    MonteCarloSimulation
)
from .serializers import (
    SimulationScenarioSerializer, SimulationRunSerializer, SimulationModelSerializer,
    SimulationResultSerializer, OptimizationTargetSerializer, SensitivityAnalysisSerializer,
    MonteCarloSimulationSerializer
)
from core.permissions import CompanyIsolationPermission

logger = logging.getLogger(__name__)

class SimulationScenarioViewSet(viewsets.ModelViewSet):
    """Simulation scenario management"""
    
    queryset = SimulationScenario.objects.all()
    serializer_class = SimulationScenarioSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['scenario_type', 'status', 'is_active', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'started_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def run_simulation(self, request, pk=None):
        """Run a simulation scenario"""
        scenario = self.get_object()
        
        try:
            from .simulation_engine import simulation_engine
            
            parameters = request.data.get('parameters', {})
            
            results = simulation_engine.run_simulation(
                scenario_id=str(scenario.id),
                parameters=parameters
            )
            
            return Response(results)
            
        except Exception as e:
            logger.error(f"Simulation failed: {str(e)}")
            return Response(
                {'error': 'Simulation failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get simulation results"""
        scenario = self.get_object()
        runs = scenario.runs.all().order_by('-created_at')
        
        serializer = SimulationRunSerializer(runs, many=True)
        return Response(serializer.data)

class SimulationRunViewSet(viewsets.ModelViewSet):
    """Simulation run management"""
    
    queryset = SimulationRun.objects.all()
    serializer_class = SimulationRunSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['scenario', 'status']
    search_fields = ['run_name', 'description']
    ordering_fields = ['created_at', 'started_at', 'completed_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get run results"""
        run = self.get_object()
        results = run.results.all().order_by('-created_at')
        
        serializer = SimulationResultSerializer(results, many=True)
        return Response(serializer.data)

class SimulationModelViewSet(viewsets.ModelViewSet):
    """Simulation model management"""
    
    queryset = SimulationModel.objects.all()
    serializer_class = SimulationModelSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['model_type', 'algorithm', 'is_active', 'is_trained', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'accuracy']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def train_model(self, request, pk=None):
        """Train a simulation model"""
        model = self.get_object()
        
        try:
            # TODO: Implement actual model training
            # This would involve training the ML model with provided data
            
            training_data = request.data.get('training_data', {})
            
            # Simulate model training
            model.is_trained = True
            model.last_trained = timezone.now()
            model.accuracy = 0.85  # Simulated accuracy
            model.save()
            
            return Response({
                'status': 'success',
                'model_id': str(model.id),
                'accuracy': model.accuracy
            })
            
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return Response(
                {'error': 'Model training failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SimulationResultViewSet(viewsets.ModelViewSet):
    """Simulation result management"""
    
    queryset = SimulationResult.objects.all()
    serializer_class = SimulationResultSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['simulation_run', 'result_type']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'confidence_score']
    ordering = ['-created_at']

class OptimizationTargetViewSet(viewsets.ModelViewSet):
    """Optimization target management"""
    
    queryset = OptimizationTarget.objects.all()
    serializer_class = OptimizationTargetSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['target_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'weight']
    ordering = ['name']

class SensitivityAnalysisViewSet(viewsets.ModelViewSet):
    """Sensitivity analysis management"""
    
    queryset = SensitivityAnalysis.objects.all()
    serializer_class = SensitivityAnalysisSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['simulation_run', 'parameter_name']
    search_fields = ['parameter_name']
    ordering_fields = ['created_at', 'sensitivity_score']
    ordering = ['-created_at']

class MonteCarloSimulationViewSet(viewsets.ModelViewSet):
    """Monte Carlo simulation management"""
    
    queryset = MonteCarloSimulation.objects.all()
    serializer_class = MonteCarloSimulationSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['simulation_run']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def run_simulation(self, request, pk=None):
        """Run Monte Carlo simulation"""
        monte_carlo = self.get_object()
        
        try:
            # TODO: Implement actual Monte Carlo simulation
            # This would involve running the simulation with specified parameters
            
            iterations = request.data.get('iterations', monte_carlo.iterations)
            
            # Simulate Monte Carlo results
            results = {
                'iterations': iterations,
                'mean': 0.75,
                'std_dev': 0.15,
                'confidence_95': [0.45, 1.05],
                'percentiles': {
                    '5th': 0.45,
                    '25th': 0.65,
                    '50th': 0.75,
                    '75th': 0.85,
                    '95th': 1.05
                }
            }
            
            monte_carlo.results = results
            monte_carlo.save()
            
            return Response({
                'status': 'success',
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Monte Carlo simulation failed: {str(e)}")
            return Response(
                {'error': 'Monte Carlo simulation failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
