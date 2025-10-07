# simulation/serializers.py
# What-If Analysis and Simulation Serializers

from rest_framework import serializers
from .models import (
    SimulationScenario, SimulationRun, SimulationModel,
    SimulationResult, OptimizationTarget, SensitivityAnalysis,
    MonteCarloSimulation
)

class SimulationScenarioSerializer(serializers.ModelSerializer):
    """Simulation scenario serializer"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = SimulationScenario
        fields = [
            'id', 'name', 'description', 'scenario_type', 'parameters',
            'constraints', 'baseline_data', 'status', 'is_active',
            'started_at', 'completed_at', 'execution_duration', 'results',
            'insights', 'recommendations', 'owner', 'owner_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SimulationRunSerializer(serializers.ModelSerializer):
    """Simulation run serializer"""
    
    scenario_name = serializers.CharField(source='scenario.name', read_only=True)
    
    class Meta:
        model = SimulationRun
        fields = [
            'id', 'scenario', 'scenario_name', 'run_name', 'description',
            'parameters', 'input_data', 'status', 'started_at', 'completed_at',
            'execution_duration', 'results', 'metrics', 'error_message',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SimulationModelSerializer(serializers.ModelSerializer):
    """Simulation model serializer"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = SimulationModel
        fields = [
            'id', 'name', 'description', 'model_type', 'algorithm',
            'configuration', 'features', 'target_variable', 'accuracy',
            'precision', 'recall', 'f1_score', 'auc_score', 'status',
            'is_active', 'is_trained', 'last_trained', 'training_duration',
            'owner', 'owner_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SimulationResultSerializer(serializers.ModelSerializer):
    """Simulation result serializer"""
    
    simulation_run_name = serializers.CharField(source='simulation_run.run_name', read_only=True)
    
    class Meta:
        model = SimulationResult
        fields = [
            'id', 'simulation_run', 'simulation_run_name', 'result_type',
            'name', 'description', 'data', 'metrics', 'visualizations',
            'insights', 'recommendations', 'confidence_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class OptimizationTargetSerializer(serializers.ModelSerializer):
    """Optimization target serializer"""
    
    class Meta:
        model = OptimizationTarget
        fields = [
            'id', 'name', 'description', 'target_type', 'metric',
            'target_value', 'weight', 'constraints', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SensitivityAnalysisSerializer(serializers.ModelSerializer):
    """Sensitivity analysis serializer"""
    
    simulation_run_name = serializers.CharField(source='simulation_run.run_name', read_only=True)
    
    class Meta:
        model = SensitivityAnalysis
        fields = [
            'id', 'simulation_run', 'simulation_run_name', 'parameter_name',
            'parameter_range', 'step_size', 'results', 'sensitivity_score',
            'chart_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class MonteCarloSimulationSerializer(serializers.ModelSerializer):
    """Monte Carlo simulation serializer"""
    
    simulation_run_name = serializers.CharField(source='simulation_run.run_name', read_only=True)
    
    class Meta:
        model = MonteCarloSimulation
        fields = [
            'id', 'simulation_run', 'simulation_run_name', 'iterations',
            'random_seed', 'variable_distributions', 'results', 'statistics',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
