# simulation/models.py
# What-If Analysis and Simulation Models

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import CompanyIsolatedModel, User
import uuid
import json

class SimulationScenario(CompanyIsolatedModel):
    """Simulation scenarios for what-if analysis"""
    
    SCENARIO_TYPES = [
        ('sales_forecast', 'Sales Forecast'),
        ('lead_scoring', 'Lead Scoring'),
        ('territory_optimization', 'Territory Optimization'),
        ('pipeline_analysis', 'Pipeline Analysis'),
        ('revenue_projection', 'Revenue Projection'),
        ('customer_lifetime_value', 'Customer Lifetime Value'),
        ('churn_prediction', 'Churn Prediction'),
        ('resource_allocation', 'Resource Allocation'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    scenario_type = models.CharField(
        max_length=30,
        choices=SCENARIO_TYPES
    )
    
    # Scenario Configuration
    parameters = models.JSONField(
        default=dict,
        help_text="Simulation parameters"
    )
    constraints = models.JSONField(
        default=dict,
        help_text="Simulation constraints"
    )
    baseline_data = models.JSONField(
        default=dict,
        help_text="Baseline data for comparison"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_active = models.BooleanField(default=True)
    
    # Execution Information
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Execution duration in seconds"
    )
    
    # Results
    results = models.JSONField(
        default=dict,
        help_text="Simulation results"
    )
    insights = models.TextField(blank=True, help_text="Key insights from simulation")
    recommendations = models.TextField(blank=True, help_text="Recommendations based on results")
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_scenarios'
    )
    
    class Meta:
        db_table = 'simulation_scenario'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class SimulationRun(CompanyIsolatedModel):
    """Individual simulation runs"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Basic Information
    scenario = models.ForeignKey(
        SimulationScenario,
        on_delete=models.CASCADE,
        related_name='runs'
    )
    run_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Run Configuration
    parameters = models.JSONField(
        default=dict,
        help_text="Run-specific parameters"
    )
    input_data = models.JSONField(
        default=dict,
        help_text="Input data for simulation"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Execution Information
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="Execution duration in seconds"
    )
    
    # Results
    results = models.JSONField(
        default=dict,
        help_text="Simulation run results"
    )
    metrics = models.JSONField(
        default=dict,
        help_text="Performance metrics"
    )
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'simulation_run'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.scenario.name} - {self.run_name}"

class SimulationModel(CompanyIsolatedModel):
    """Simulation models for different scenarios"""
    
    MODEL_TYPES = [
        ('monte_carlo', 'Monte Carlo'),
        ('linear_regression', 'Linear Regression'),
        ('decision_tree', 'Decision Tree'),
        ('neural_network', 'Neural Network'),
        ('time_series', 'Time Series'),
        ('optimization', 'Optimization'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    model_type = models.CharField(
        max_length=30,
        choices=MODEL_TYPES
    )
    
    # Model Configuration
    algorithm = models.CharField(
        max_length=100,
        help_text="Algorithm used for simulation"
    )
    parameters = models.JSONField(
        default=dict,
        help_text="Model parameters"
    )
    training_data = models.JSONField(
        default=dict,
        help_text="Training data configuration"
    )
    
    # Performance Metrics
    accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="Model accuracy"
    )
    precision = models.FloatField(
        null=True,
        blank=True,
        help_text="Model precision"
    )
    recall = models.FloatField(
        null=True,
        blank=True,
        help_text="Model recall"
    )
    f1_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Model F1 score"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_trained = models.BooleanField(default=False)
    last_trained = models.DateTimeField(null=True, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_models'
    )
    
    class Meta:
        db_table = 'simulation_model'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class SimulationResult(CompanyIsolatedModel):
    """Simulation results and outputs"""
    
    RESULT_TYPES = [
        ('forecast', 'Forecast'),
        ('optimization', 'Optimization'),
        ('sensitivity', 'Sensitivity Analysis'),
        ('scenario', 'Scenario Analysis'),
        ('risk', 'Risk Analysis'),
    ]
    
    # Basic Information
    simulation_run = models.ForeignKey(
        SimulationRun,
        on_delete=models.CASCADE,
        related_name='results'
    )
    result_type = models.CharField(
        max_length=20,
        choices=RESULT_TYPES
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Result Data
    data = models.JSONField(
        default=dict,
        help_text="Result data"
    )
    metrics = models.JSONField(
        default=dict,
        help_text="Result metrics"
    )
    visualizations = models.JSONField(
        default=list,
        help_text="Visualization configurations"
    )
    
    # Analysis
    insights = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence in results (0.0-1.0)"
    )
    
    class Meta:
        db_table = 'simulation_result'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.simulation_run.run_name} - {self.name}"

class OptimizationTarget(CompanyIsolatedModel):
    """Optimization targets for simulations"""
    
    TARGET_TYPES = [
        ('maximize', 'Maximize'),
        ('minimize', 'Minimize'),
        ('target', 'Target Value'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_type = models.CharField(
        max_length=20,
        choices=TARGET_TYPES
    )
    
    # Target Configuration
    metric = models.CharField(
        max_length=100,
        help_text="Metric to optimize"
    )
    target_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Target value (for target type)"
    )
    weight = models.FloatField(
        default=1.0,
        help_text="Weight for multi-objective optimization"
    )
    
    # Constraints
    constraints = models.JSONField(
        default=dict,
        help_text="Optimization constraints"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'optimization_target'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class SensitivityAnalysis(CompanyIsolatedModel):
    """Sensitivity analysis for simulations"""
    
    # Basic Information
    simulation_run = models.ForeignKey(
        SimulationRun,
        on_delete=models.CASCADE,
        related_name='sensitivity_analyses'
    )
    parameter_name = models.CharField(
        max_length=100,
        help_text="Parameter being analyzed"
    )
    
    # Analysis Configuration
    parameter_range = models.JSONField(
        default=dict,
        help_text="Parameter range for analysis"
    )
    step_size = models.FloatField(
        help_text="Step size for parameter variation"
    )
    
    # Results
    results = models.JSONField(
        default=dict,
        help_text="Sensitivity analysis results"
    )
    sensitivity_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Overall sensitivity score"
    )
    
    # Visualization
    chart_data = models.JSONField(
        default=dict,
        help_text="Chart data for visualization"
    )
    
    class Meta:
        db_table = 'sensitivity_analysis'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.simulation_run.run_name} - {self.parameter_name}"

class MonteCarloSimulation(CompanyIsolatedModel):
    """Monte Carlo simulation configuration"""
    
    # Basic Information
    simulation_run = models.ForeignKey(
        SimulationRun,
        on_delete=models.CASCADE,
        related_name='monte_carlo_simulations'
    )
    
    # Simulation Configuration
    iterations = models.IntegerField(
        default=1000,
        help_text="Number of Monte Carlo iterations"
    )
    random_seed = models.IntegerField(
        null=True,
        blank=True,
        help_text="Random seed for reproducibility"
    )
    
    # Variable Distributions
    variable_distributions = models.JSONField(
        default=dict,
        help_text="Variable probability distributions"
    )
    
    # Results
    results = models.JSONField(
        default=dict,
        help_text="Monte Carlo simulation results"
    )
    statistics = models.JSONField(
        default=dict,
        help_text="Statistical results"
    )
    
    class Meta:
        db_table = 'monte_carlo_simulation'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Monte Carlo - {self.simulation_run.run_name}"
