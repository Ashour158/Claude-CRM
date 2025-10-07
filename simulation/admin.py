# simulation/admin.py
# What-If Analysis and Simulation Admin Configuration

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    SimulationScenario, SimulationRun, SimulationModel,
    SimulationResult, OptimizationTarget, SensitivityAnalysis,
    MonteCarloSimulation
)

@admin.register(SimulationScenario)
class SimulationScenarioAdmin(admin.ModelAdmin):
    """Simulation scenario admin interface"""
    list_display = [
        'name', 'scenario_type', 'status', 'is_active',
        'owner', 'started_at', 'created_at'
    ]
    list_filter = [
        'scenario_type', 'status', 'is_active', 'owner',
        'created_at', 'started_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'started_at', 'completed_at', 'execution_duration',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['owner']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'scenario_type')
        }),
        ('Configuration', {
            'fields': ('parameters', 'constraints', 'baseline_data')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Execution', {
            'fields': ('started_at', 'completed_at', 'execution_duration'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('results', 'insights', 'recommendations'),
            'classes': ('collapse',)
        }),
        ('Owner', {
            'fields': ('owner',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SimulationRun)
class SimulationRunAdmin(admin.ModelAdmin):
    """Simulation run admin interface"""
    list_display = [
        'run_name', 'scenario', 'status', 'started_at',
        'completed_at', 'created_at'
    ]
    list_filter = [
        'status', 'scenario', 'started_at', 'completed_at', 'created_at'
    ]
    search_fields = ['run_name', 'description', 'scenario__name']
    readonly_fields = [
        'started_at', 'completed_at', 'execution_duration',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['scenario']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('scenario', 'run_name', 'description')
        }),
        ('Configuration', {
            'fields': ('parameters', 'input_data')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Execution', {
            'fields': ('started_at', 'completed_at', 'execution_duration'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('results', 'metrics', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SimulationModel)
class SimulationModelAdmin(admin.ModelAdmin):
    """Simulation model admin interface"""
    list_display = [
        'name', 'model_type', 'algorithm', 'is_active',
        'is_trained', 'accuracy', 'owner', 'created_at'
    ]
    list_filter = [
        'model_type', 'algorithm', 'is_active', 'is_trained',
        'owner', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'last_trained', 'training_duration', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['owner']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'model_type', 'algorithm')
        }),
        ('Configuration', {
            'fields': ('configuration', 'features', 'target_variable')
        }),
        ('Performance Metrics', {
            'fields': ('accuracy', 'precision', 'recall', 'f1_score', 'auc_score')
        }),
        ('Status', {
            'fields': ('status', 'is_active', 'is_trained')
        }),
        ('Training', {
            'fields': ('last_trained', 'training_duration'),
            'classes': ('collapse',)
        }),
        ('Owner', {
            'fields': ('owner',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    """Simulation result admin interface"""
    list_display = [
        'name', 'simulation_run', 'result_type', 'confidence_score',
        'created_at'
    ]
    list_filter = [
        'result_type', 'simulation_run__scenario', 'created_at'
    ]
    search_fields = ['name', 'description', 'simulation_run__run_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['simulation_run']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('simulation_run', 'result_type', 'name', 'description')
        }),
        ('Result Data', {
            'fields': ('data', 'metrics', 'visualizations')
        }),
        ('Analysis', {
            'fields': ('insights', 'recommendations', 'confidence_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(OptimizationTarget)
class OptimizationTargetAdmin(admin.ModelAdmin):
    """Optimization target admin interface"""
    list_display = [
        'name', 'target_type', 'metric', 'target_value',
        'weight', 'is_active', 'created_at'
    ]
    list_filter = [
        'target_type', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description', 'metric']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'target_type')
        }),
        ('Target Configuration', {
            'fields': ('metric', 'target_value', 'weight')
        }),
        ('Constraints', {
            'fields': ('constraints',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SensitivityAnalysis)
class SensitivityAnalysisAdmin(admin.ModelAdmin):
    """Sensitivity analysis admin interface"""
    list_display = [
        'parameter_name', 'simulation_run', 'sensitivity_score',
        'created_at'
    ]
    list_filter = [
        'simulation_run__scenario', 'created_at'
    ]
    search_fields = ['parameter_name', 'simulation_run__run_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['simulation_run']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('simulation_run', 'parameter_name')
        }),
        ('Analysis Configuration', {
            'fields': ('parameter_range', 'step_size')
        }),
        ('Results', {
            'fields': ('results', 'sensitivity_score', 'chart_data')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(MonteCarloSimulation)
class MonteCarloSimulationAdmin(admin.ModelAdmin):
    """Monte Carlo simulation admin interface"""
    list_display = [
        'simulation_run', 'iterations', 'random_seed', 'created_at'
    ]
    list_filter = [
        'simulation_run__scenario', 'created_at'
    ]
    search_fields = ['simulation_run__run_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['simulation_run']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('simulation_run',)
        }),
        ('Simulation Configuration', {
            'fields': ('iterations', 'random_seed', 'variable_distributions')
        }),
        ('Results', {
            'fields': ('results', 'statistics')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
