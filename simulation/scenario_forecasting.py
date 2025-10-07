# simulation/scenario_forecasting.py
# Scenario Forecasting with What-If Deltas and Path Sensitivity

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from scipy.optimize import minimize
from scipy.stats import norm
import joblib
import pickle
from celery import shared_task

from .models import (
    ScenarioForecast, WhatIfScenario, PathSensitivity, 
    ScenarioDelta, ForecastPath, ScenarioMetrics
)
from core.models import User, Company

logger = logging.getLogger(__name__)

class ScenarioForecastingEngine:
    """
    Advanced scenario forecasting engine with what-if deltas,
    path sensitivity analysis, and Monte Carlo simulations.
    """
    
    def __init__(self):
        self.scenario_types = {
            'sales_forecast': self._sales_forecast_scenario,
            'territory_optimization': self._territory_optimization_scenario,
            'lead_scoring_impact': self._lead_scoring_impact_scenario,
            'resource_allocation': self._resource_allocation_scenario,
            'market_conditions': self._market_conditions_scenario,
            'competitive_analysis': self._competitive_analysis_scenario
        }
        
        self.sensitivity_methods = {
            'monte_carlo': self._monte_carlo_sensitivity,
            'tornado': self._tornado_sensitivity,
            'scenario_analysis': self._scenario_analysis_sensitivity,
            'stress_testing': self._stress_testing_sensitivity
        }
        
        self.delta_calculators = {
            'linear': self._linear_delta,
            'exponential': self._exponential_delta,
            'logistic': self._logistic_delta,
            'polynomial': self._polynomial_delta
        }
    
    def create_what_if_scenario(self, scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a what-if scenario with deltas and sensitivity analysis.
        """
        try:
            # Validate scenario configuration
            validation_result = self._validate_scenario_config(scenario_config)
            if not validation_result['valid']:
                return {
                    'status': 'error',
                    'error': validation_result['error']
                }
            
            # Create scenario record
            scenario_record = self._create_scenario_record(scenario_config)
            
            # Generate base forecast
            base_forecast = self._generate_base_forecast(scenario_config)
            
            # Apply scenario deltas
            scenario_forecast = self._apply_scenario_deltas(base_forecast, scenario_config)
            
            # Calculate path sensitivity
            sensitivity_analysis = self._calculate_path_sensitivity(scenario_forecast, scenario_config)
            
            # Generate scenario metrics
            scenario_metrics = self._calculate_scenario_metrics(scenario_forecast, base_forecast, scenario_config)
            
            # Save scenario results
            self._save_scenario_results(scenario_record, scenario_forecast, sensitivity_analysis, scenario_metrics)
            
            return {
                'status': 'success',
                'scenario_id': str(scenario_record.id),
                'base_forecast': base_forecast,
                'scenario_forecast': scenario_forecast,
                'sensitivity_analysis': sensitivity_analysis,
                'scenario_metrics': scenario_metrics,
                'created_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"What-if scenario creation failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def run_scenario_comparison(self, scenario_ids: List[str], comparison_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare multiple scenarios and analyze differences.
        """
        try:
            # Get scenario records
            scenarios = WhatIfScenario.objects.filter(id__in=scenario_ids)
            
            if not scenarios.exists():
                return {
                    'status': 'error',
                    'error': 'No scenarios found for comparison'
                }
            
            # Load scenario forecasts
            scenario_forecasts = {}
            for scenario in scenarios:
                forecast = self._load_scenario_forecast(scenario)
                scenario_forecasts[str(scenario.id)] = forecast
            
            # Compare scenarios
            comparison_results = self._compare_scenarios(scenario_forecasts, comparison_config)
            
            # Calculate scenario rankings
            scenario_rankings = self._rank_scenarios(scenario_forecasts, comparison_config)
            
            # Generate comparison insights
            insights = self._generate_comparison_insights(comparison_results, scenario_rankings)
            
            return {
                'status': 'success',
                'scenarios_compared': len(scenarios),
                'comparison_results': comparison_results,
                'scenario_rankings': scenario_rankings,
                'insights': insights,
                'comparison_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Scenario comparison failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def analyze_path_sensitivity(self, scenario_id: str, sensitivity_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze path sensitivity for a specific scenario.
        """
        try:
            # Get scenario record
            scenario = WhatIfScenario.objects.get(id=scenario_id)
            
            # Load scenario forecast
            scenario_forecast = self._load_scenario_forecast(scenario)
            
            # Run sensitivity analysis
            sensitivity_method = sensitivity_config.get('method', 'monte_carlo')
            sensitivity_func = self.sensitivity_methods.get(sensitivity_method)
            
            if not sensitivity_func:
                return {
                    'status': 'error',
                    'error': f'Unknown sensitivity method: {sensitivity_method}'
                }
            
            sensitivity_results = sensitivity_func(scenario_forecast, sensitivity_config)
            
            # Calculate sensitivity metrics
            sensitivity_metrics = self._calculate_sensitivity_metrics(sensitivity_results, sensitivity_config)
            
            # Save sensitivity analysis
            sensitivity_record = self._save_sensitivity_analysis(scenario, sensitivity_results, sensitivity_metrics)
            
            return {
                'status': 'success',
                'sensitivity_id': str(sensitivity_record.id),
                'sensitivity_results': sensitivity_results,
                'sensitivity_metrics': sensitivity_metrics,
                'method': sensitivity_method,
                'analysis_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Path sensitivity analysis failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _sales_forecast_scenario(self, base_data: Dict[str, Any], scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sales forecast scenario"""
        try:
            # Extract scenario parameters
            growth_rate = scenario_config.get('growth_rate', 0.05)
            market_conditions = scenario_config.get('market_conditions', 'stable')
            competitive_pressure = scenario_config.get('competitive_pressure', 0.0)
            
            # Apply scenario deltas
            scenario_forecast = {}
            
            for period in base_data.get('periods', []):
                # Calculate base forecast
                base_value = period['value']
                
                # Apply growth rate
                growth_factor = (1 + growth_rate) ** period['period']
                
                # Apply market conditions
                market_factor = self._get_market_factor(market_conditions)
                
                # Apply competitive pressure
                competitive_factor = 1 - competitive_pressure
                
                # Calculate scenario value
                scenario_value = base_value * growth_factor * market_factor * competitive_factor
                
                scenario_forecast[period['period']] = {
                    'base_value': base_value,
                    'scenario_value': scenario_value,
                    'delta': scenario_value - base_value,
                    'delta_percentage': (scenario_value - base_value) / base_value * 100
                }
            
            return scenario_forecast
            
        except Exception as e:
            logger.error(f"Sales forecast scenario failed: {str(e)}")
            return {}
    
    def _territory_optimization_scenario(self, base_data: Dict[str, Any], scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate territory optimization scenario"""
        try:
            # Extract scenario parameters
            territory_changes = scenario_config.get('territory_changes', {})
            reallocation_factor = scenario_config.get('reallocation_factor', 1.0)
            
            # Apply territory changes
            scenario_forecast = {}
            
            for territory in base_data.get('territories', []):
                territory_id = territory['id']
                
                if territory_id in territory_changes:
                    change = territory_changes[territory_id]
                    
                    # Apply reallocation
                    new_value = territory['value'] * change['allocation_factor'] * reallocation_factor
                    
                    scenario_forecast[territory_id] = {
                        'base_value': territory['value'],
                        'scenario_value': new_value,
                        'delta': new_value - territory['value'],
                        'allocation_change': change['allocation_factor']
                    }
                else:
                    scenario_forecast[territory_id] = {
                        'base_value': territory['value'],
                        'scenario_value': territory['value'],
                        'delta': 0,
                        'allocation_change': 1.0
                    }
            
            return scenario_forecast
            
        except Exception as e:
            logger.error(f"Territory optimization scenario failed: {str(e)}")
            return {}
    
    def _lead_scoring_impact_scenario(self, base_data: Dict[str, Any], scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate lead scoring impact scenario"""
        try:
            # Extract scenario parameters
            scoring_threshold = scenario_config.get('scoring_threshold', 0.5)
            conversion_improvement = scenario_config.get('conversion_improvement', 0.0)
            
            # Apply lead scoring changes
            scenario_forecast = {}
            
            for lead in base_data.get('leads', []):
                lead_id = lead['id']
                current_score = lead['score']
                
                # Apply new scoring threshold
                if current_score >= scoring_threshold:
                    # Lead qualifies with new threshold
                    conversion_rate = lead['conversion_rate'] * (1 + conversion_improvement)
                    scenario_value = lead['value'] * conversion_rate
                else:
                    # Lead doesn't qualify
                    scenario_value = 0
                
                scenario_forecast[lead_id] = {
                    'base_value': lead['value'],
                    'scenario_value': scenario_value,
                    'delta': scenario_value - lead['value'],
                    'qualifies': current_score >= scoring_threshold,
                    'conversion_rate': conversion_rate if current_score >= scoring_threshold else 0
                }
            
            return scenario_forecast
            
        except Exception as e:
            logger.error(f"Lead scoring impact scenario failed: {str(e)}")
            return {}
    
    def _resource_allocation_scenario(self, base_data: Dict[str, Any], scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate resource allocation scenario"""
        try:
            # Extract scenario parameters
            resource_changes = scenario_config.get('resource_changes', {})
            efficiency_improvement = scenario_config.get('efficiency_improvement', 0.0)
            
            # Apply resource allocation changes
            scenario_forecast = {}
            
            for resource in base_data.get('resources', []):
                resource_id = resource['id']
                
                if resource_id in resource_changes:
                    change = resource_changes[resource_id]
                    
                    # Apply resource change
                    new_allocation = resource['allocation'] * change['allocation_factor']
                    
                    # Apply efficiency improvement
                    efficiency_factor = 1 + efficiency_improvement
                    
                    # Calculate scenario value
                    scenario_value = new_allocation * efficiency_factor
                    
                    scenario_forecast[resource_id] = {
                        'base_value': resource['value'],
                        'scenario_value': scenario_value,
                        'delta': scenario_value - resource['value'],
                        'allocation_change': change['allocation_factor'],
                        'efficiency_factor': efficiency_factor
                    }
                else:
                    scenario_forecast[resource_id] = {
                        'base_value': resource['value'],
                        'scenario_value': resource['value'],
                        'delta': 0,
                        'allocation_change': 1.0,
                        'efficiency_factor': 1.0
                    }
            
            return scenario_forecast
            
        except Exception as e:
            logger.error(f"Resource allocation scenario failed: {str(e)}")
            return {}
    
    def _market_conditions_scenario(self, base_data: Dict[str, Any], scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market conditions scenario"""
        try:
            # Extract scenario parameters
            market_growth = scenario_config.get('market_growth', 0.0)
            market_volatility = scenario_config.get('market_volatility', 0.0)
            economic_conditions = scenario_config.get('economic_conditions', 'stable')
            
            # Apply market conditions
            scenario_forecast = {}
            
            for period in base_data.get('periods', []):
                base_value = period['value']
                
                # Apply market growth
                growth_factor = 1 + market_growth
                
                # Apply market volatility
                volatility_factor = 1 + np.random.normal(0, market_volatility)
                
                # Apply economic conditions
                economic_factor = self._get_economic_factor(economic_conditions)
                
                # Calculate scenario value
                scenario_value = base_value * growth_factor * volatility_factor * economic_factor
                
                scenario_forecast[period['period']] = {
                    'base_value': base_value,
                    'scenario_value': scenario_value,
                    'delta': scenario_value - base_value,
                    'growth_factor': growth_factor,
                    'volatility_factor': volatility_factor,
                    'economic_factor': economic_factor
                }
            
            return scenario_forecast
            
        except Exception as e:
            logger.error(f"Market conditions scenario failed: {str(e)}")
            return {}
    
    def _competitive_analysis_scenario(self, base_data: Dict[str, Any], scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate competitive analysis scenario"""
        try:
            # Extract scenario parameters
            competitive_pressure = scenario_config.get('competitive_pressure', 0.0)
            market_share_changes = scenario_config.get('market_share_changes', {})
            
            # Apply competitive changes
            scenario_forecast = {}
            
            for product in base_data.get('products', []):
                product_id = product['id']
                
                # Apply competitive pressure
                pressure_factor = 1 - competitive_pressure
                
                # Apply market share changes
                if product_id in market_share_changes:
                    share_change = market_share_changes[product_id]
                    share_factor = 1 + share_change
                else:
                    share_factor = 1.0
                
                # Calculate scenario value
                scenario_value = product['value'] * pressure_factor * share_factor
                
                scenario_forecast[product_id] = {
                    'base_value': product['value'],
                    'scenario_value': scenario_value,
                    'delta': scenario_value - product['value'],
                    'pressure_factor': pressure_factor,
                    'share_factor': share_factor
                }
            
            return scenario_forecast
            
        except Exception as e:
            logger.error(f"Competitive analysis scenario failed: {str(e)}")
            return {}
    
    def _monte_carlo_sensitivity(self, scenario_forecast: Dict[str, Any], sensitivity_config: Dict[str, Any]) -> Dict[str, Any]:
        """Monte Carlo sensitivity analysis"""
        try:
            n_simulations = sensitivity_config.get('n_simulations', 1000)
            uncertainty_factors = sensitivity_config.get('uncertainty_factors', {})
            
            # Run Monte Carlo simulations
            simulation_results = []
            
            for i in range(n_simulations):
                # Generate random scenario
                random_scenario = self._generate_random_scenario(uncertainty_factors)
                
                # Calculate scenario outcome
                outcome = self._calculate_scenario_outcome(scenario_forecast, random_scenario)
                
                simulation_results.append(outcome)
            
            # Analyze results
            outcomes = np.array(simulation_results)
            
            sensitivity_results = {
                'mean_outcome': float(np.mean(outcomes)),
                'std_outcome': float(np.std(outcomes)),
                'percentile_5': float(np.percentile(outcomes, 5)),
                'percentile_95': float(np.percentile(outcomes, 95)),
                'confidence_interval': {
                    'lower': float(np.percentile(outcomes, 2.5)),
                    'upper': float(np.percentile(outcomes, 97.5))
                },
                'simulation_results': simulation_results
            }
            
            return sensitivity_results
            
        except Exception as e:
            logger.error(f"Monte Carlo sensitivity analysis failed: {str(e)}")
            return {}
    
    def _tornado_sensitivity(self, scenario_forecast: Dict[str, Any], sensitivity_config: Dict[str, Any]) -> Dict[str, Any]:
        """Tornado sensitivity analysis"""
        try:
            # Get sensitivity parameters
            sensitivity_params = sensitivity_config.get('sensitivity_params', {})
            
            # Run tornado analysis
            tornado_results = {}
            
            for param_name, param_range in sensitivity_params.items():
                # Test parameter at low and high values
                low_value = param_range['low']
                high_value = param_range['high']
                
                # Calculate outcomes
                low_outcome = self._calculate_parameter_outcome(scenario_forecast, param_name, low_value)
                high_outcome = self._calculate_parameter_outcome(scenario_forecast, param_name, high_value)
                
                # Calculate sensitivity
                sensitivity = abs(high_outcome - low_outcome)
                
                tornado_results[param_name] = {
                    'low_value': low_value,
                    'high_value': high_value,
                    'low_outcome': low_outcome,
                    'high_outcome': high_outcome,
                    'sensitivity': sensitivity
                }
            
            # Sort by sensitivity
            sorted_results = sorted(tornado_results.items(), key=lambda x: x[1]['sensitivity'], reverse=True)
            
            return {
                'tornado_results': dict(sorted_results),
                'most_sensitive': sorted_results[0][0] if sorted_results else None
            }
            
        except Exception as e:
            logger.error(f"Tornado sensitivity analysis failed: {str(e)}")
            return {}
    
    def _scenario_analysis_sensitivity(self, scenario_forecast: Dict[str, Any], sensitivity_config: Dict[str, Any]) -> Dict[str, Any]:
        """Scenario analysis sensitivity"""
        try:
            # Get scenario variations
            scenario_variations = sensitivity_config.get('scenario_variations', {})
            
            # Run scenario analysis
            scenario_results = {}
            
            for scenario_name, scenario_params in scenario_variations.items():
                # Calculate scenario outcome
                outcome = self._calculate_scenario_outcome(scenario_forecast, scenario_params)
                
                scenario_results[scenario_name] = {
                    'parameters': scenario_params,
                    'outcome': outcome
                }
            
            return {
                'scenario_results': scenario_results,
                'best_scenario': max(scenario_results.items(), key=lambda x: x[1]['outcome'])[0],
                'worst_scenario': min(scenario_results.items(), key=lambda x: x[1]['outcome'])[0]
            }
            
        except Exception as e:
            logger.error(f"Scenario analysis sensitivity failed: {str(e)}")
            return {}
    
    def _stress_testing_sensitivity(self, scenario_forecast: Dict[str, Any], sensitivity_config: Dict[str, Any]) -> Dict[str, Any]:
        """Stress testing sensitivity analysis"""
        try:
            # Get stress test scenarios
            stress_scenarios = sensitivity_config.get('stress_scenarios', {})
            
            # Run stress tests
            stress_results = {}
            
            for stress_name, stress_params in stress_scenarios.items():
                # Apply stress conditions
                stressed_forecast = self._apply_stress_conditions(scenario_forecast, stress_params)
                
                # Calculate stressed outcome
                outcome = self._calculate_stressed_outcome(stressed_forecast)
                
                stress_results[stress_name] = {
                    'stress_parameters': stress_params,
                    'outcome': outcome,
                    'impact': outcome - self._calculate_base_outcome(scenario_forecast)
                }
            
            return {
                'stress_results': stress_results,
                'most_stressful': max(stress_results.items(), key=lambda x: abs(x[1]['impact']))[0]
            }
            
        except Exception as e:
            logger.error(f"Stress testing sensitivity failed: {str(e)}")
            return {}
    
    def _validate_scenario_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate scenario configuration"""
        try:
            # Check required fields
            required_fields = ['scenario_type', 'base_data']
            for field in required_fields:
                if field not in config:
                    return {
                        'valid': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Check scenario type
            if config['scenario_type'] not in self.scenario_types:
                return {
                    'valid': False,
                    'error': f'Unknown scenario type: {config["scenario_type"]}'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Scenario config validation failed: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _create_scenario_record(self, config: Dict[str, Any]) -> WhatIfScenario:
        """Create scenario record"""
        return WhatIfScenario.objects.create(
            scenario_type=config['scenario_type'],
            scenario_name=config.get('scenario_name', 'Unnamed Scenario'),
            scenario_config=config,
            created_at=timezone.now()
        )
    
    def _generate_base_forecast(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate base forecast"""
        try:
            # This would generate actual base forecast
            # For now, return placeholder data
            return {
                'periods': [
                    {'period': 1, 'value': 100000},
                    {'period': 2, 'value': 110000},
                    {'period': 3, 'value': 120000}
                ]
            }
            
        except Exception as e:
            logger.error(f"Base forecast generation failed: {str(e)}")
            return {}
    
    def _apply_scenario_deltas(self, base_forecast: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply scenario deltas to base forecast"""
        try:
            scenario_type = config['scenario_type']
            scenario_func = self.scenario_types.get(scenario_type)
            
            if scenario_func:
                return scenario_func(base_forecast, config)
            else:
                return base_forecast
                
        except Exception as e:
            logger.error(f"Scenario deltas application failed: {str(e)}")
            return base_forecast
    
    def _calculate_path_sensitivity(self, scenario_forecast: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate path sensitivity"""
        try:
            # This would implement actual path sensitivity calculation
            # For now, return placeholder results
            return {
                'sensitivity_score': 0.75,
                'critical_paths': ['growth_rate', 'market_conditions'],
                'sensitivity_factors': {
                    'growth_rate': 0.8,
                    'market_conditions': 0.6,
                    'competitive_pressure': 0.4
                }
            }
            
        except Exception as e:
            logger.error(f"Path sensitivity calculation failed: {str(e)}")
            return {}
    
    def _calculate_scenario_metrics(self, scenario_forecast: Dict[str, Any], base_forecast: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate scenario metrics"""
        try:
            # Calculate total scenario value
            scenario_total = sum(period.get('scenario_value', 0) for period in scenario_forecast.values() if isinstance(period, dict))
            base_total = sum(period.get('value', 0) for period in base_forecast.get('periods', []))
            
            # Calculate metrics
            total_delta = scenario_total - base_total
            delta_percentage = (total_delta / base_total * 100) if base_total > 0 else 0
            
            return {
                'scenario_total': scenario_total,
                'base_total': base_total,
                'total_delta': total_delta,
                'delta_percentage': delta_percentage,
                'roi': total_delta / base_total if base_total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Scenario metrics calculation failed: {str(e)}")
            return {}
    
    def _save_scenario_results(self, scenario_record: WhatIfScenario, scenario_forecast: Dict[str, Any], 
                            sensitivity_analysis: Dict[str, Any], scenario_metrics: Dict[str, Any]):
        """Save scenario results"""
        scenario_record.scenario_forecast = scenario_forecast
        scenario_record.sensitivity_analysis = sensitivity_analysis
        scenario_record.scenario_metrics = scenario_metrics
        scenario_record.save()
    
    def _load_scenario_forecast(self, scenario: WhatIfScenario) -> Dict[str, Any]:
        """Load scenario forecast"""
        return scenario.scenario_forecast or {}
    
    def _compare_scenarios(self, scenario_forecasts: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Compare multiple scenarios"""
        try:
            # This would implement actual scenario comparison
            # For now, return placeholder results
            return {
                'comparison_metrics': {
                    'total_value': {scenario_id: 100000 for scenario_id in scenario_forecasts.keys()},
                    'roi': {scenario_id: 0.15 for scenario_id in scenario_forecasts.keys()}
                }
            }
            
        except Exception as e:
            logger.error(f"Scenario comparison failed: {str(e)}")
            return {}
    
    def _rank_scenarios(self, scenario_forecasts: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank scenarios by performance"""
        try:
            # This would implement actual scenario ranking
            # For now, return placeholder rankings
            return [
                {'scenario_id': scenario_id, 'rank': i+1, 'score': 100-i*10}
                for i, scenario_id in enumerate(scenario_forecasts.keys())
            ]
            
        except Exception as e:
            logger.error(f"Scenario ranking failed: {str(e)}")
            return []
    
    def _generate_comparison_insights(self, comparison_results: Dict[str, Any], scenario_rankings: List[Dict[str, Any]]) -> List[str]:
        """Generate comparison insights"""
        try:
            insights = []
            
            # Add ranking insights
            if scenario_rankings:
                best_scenario = scenario_rankings[0]
                insights.append(f"Best performing scenario: {best_scenario['scenario_id']} with score {best_scenario['score']}")
            
            # Add comparison insights
            if 'comparison_metrics' in comparison_results:
                insights.append("Scenario comparison completed successfully")
            
            return insights
            
        except Exception as e:
            logger.error(f"Comparison insights generation failed: {str(e)}")
            return []
    
    def _calculate_sensitivity_metrics(self, sensitivity_results: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate sensitivity metrics"""
        try:
            # This would calculate actual sensitivity metrics
            # For now, return placeholder metrics
            return {
                'sensitivity_score': 0.75,
                'confidence_level': 0.95,
                'risk_level': 'medium'
            }
            
        except Exception as e:
            logger.error(f"Sensitivity metrics calculation failed: {str(e)}")
            return {}
    
    def _save_sensitivity_analysis(self, scenario: WhatIfScenario, sensitivity_results: Dict[str, Any], 
                                sensitivity_metrics: Dict[str, Any]) -> PathSensitivity:
        """Save sensitivity analysis"""
        return PathSensitivity.objects.create(
            scenario=scenario,
            sensitivity_results=sensitivity_results,
            sensitivity_metrics=sensitivity_metrics,
            analyzed_at=timezone.now()
        )
    
    def _get_market_factor(self, market_conditions: str) -> float:
        """Get market factor based on conditions"""
        factors = {
            'recession': 0.7,
            'slow_growth': 0.9,
            'stable': 1.0,
            'growth': 1.1,
            'boom': 1.3
        }
        return factors.get(market_conditions, 1.0)
    
    def _get_economic_factor(self, economic_conditions: str) -> float:
        """Get economic factor based on conditions"""
        factors = {
            'recession': 0.8,
            'slow_growth': 0.9,
            'stable': 1.0,
            'growth': 1.1,
            'boom': 1.2
        }
        return factors.get(economic_conditions, 1.0)
    
    def _generate_random_scenario(self, uncertainty_factors: Dict[str, Any]) -> Dict[str, Any]:
        """Generate random scenario for Monte Carlo"""
        try:
            random_scenario = {}
            
            for factor_name, factor_range in uncertainty_factors.items():
                if isinstance(factor_range, dict) and 'min' in factor_range and 'max' in factor_range:
                    random_value = np.random.uniform(factor_range['min'], factor_range['max'])
                    random_scenario[factor_name] = random_value
                else:
                    random_scenario[factor_name] = factor_range
            
            return random_scenario
            
        except Exception as e:
            logger.error(f"Random scenario generation failed: {str(e)}")
            return {}
    
    def _calculate_scenario_outcome(self, scenario_forecast: Dict[str, Any], scenario_params: Dict[str, Any]) -> float:
        """Calculate scenario outcome"""
        try:
            # This would implement actual scenario outcome calculation
            # For now, return placeholder outcome
            return 100000.0
            
        except Exception as e:
            logger.error(f"Scenario outcome calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_parameter_outcome(self, scenario_forecast: Dict[str, Any], param_name: str, param_value: float) -> float:
        """Calculate outcome for specific parameter value"""
        try:
            # This would implement actual parameter outcome calculation
            # For now, return placeholder outcome
            return 100000.0 * param_value
            
        except Exception as e:
            logger.error(f"Parameter outcome calculation failed: {str(e)}")
            return 0.0
    
    def _apply_stress_conditions(self, scenario_forecast: Dict[str, Any], stress_params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply stress conditions to scenario forecast"""
        try:
            # This would implement actual stress condition application
            # For now, return modified scenario forecast
            return scenario_forecast
            
        except Exception as e:
            logger.error(f"Stress conditions application failed: {str(e)}")
            return scenario_forecast
    
    def _calculate_stressed_outcome(self, stressed_forecast: Dict[str, Any]) -> float:
        """Calculate stressed outcome"""
        try:
            # This would implement actual stressed outcome calculation
            # For now, return placeholder outcome
            return 80000.0
            
        except Exception as e:
            logger.error(f"Stressed outcome calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_base_outcome(self, scenario_forecast: Dict[str, Any]) -> float:
        """Calculate base outcome"""
        try:
            # This would implement actual base outcome calculation
            # For now, return placeholder outcome
            return 100000.0
            
        except Exception as e:
            logger.error(f"Base outcome calculation failed: {str(e)}")
            return 0.0

# Celery tasks
@shared_task
def create_what_if_scenario_async(scenario_config: Dict[str, Any]):
    """Async task to create what-if scenario"""
    engine = ScenarioForecastingEngine()
    return engine.create_what_if_scenario(scenario_config)

@shared_task
def run_scenario_comparison_async(scenario_ids: List[str], comparison_config: Dict[str, Any]):
    """Async task to run scenario comparison"""
    engine = ScenarioForecastingEngine()
    return engine.run_scenario_comparison(scenario_ids, comparison_config)

@shared_task
def analyze_path_sensitivity_async(scenario_id: str, sensitivity_config: Dict[str, Any]):
    """Async task to analyze path sensitivity"""
    engine = ScenarioForecastingEngine()
    return engine.analyze_path_sensitivity(scenario_id, sensitivity_config)

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_what_if_scenario(request):
    """API endpoint to create what-if scenario"""
    engine = ScenarioForecastingEngine()
    result = engine.create_what_if_scenario(request.data)
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_scenario_comparison(request):
    """API endpoint to run scenario comparison"""
    engine = ScenarioForecastingEngine()
    result = engine.run_scenario_comparison(
        request.data.get('scenario_ids', []),
        request.data.get('comparison_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_path_sensitivity(request):
    """API endpoint to analyze path sensitivity"""
    engine = ScenarioForecastingEngine()
    result = engine.analyze_path_sensitivity(
        request.data.get('scenario_id'),
        request.data.get('sensitivity_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)
