# simulation/forecasting_ui.py
# Forecasting Calibration UI and Multi-Scenario Analysis

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import SimulationScenario, SimulationResult
from .simulation_engine import simulation_engine
from core.models import User, Company
from crm.models import Lead, Deal, Account

logger = logging.getLogger(__name__)

class ForecastingCalibrationUI:
    """
    Advanced forecasting calibration UI with multi-scenario analysis,
    confidence intervals, and scenario comparison.
    """
    
    def __init__(self):
        self.forecasting_models = {
            'linear_regression': self._linear_regression_forecast,
            'exponential_smoothing': self._exponential_smoothing_forecast,
            'arima': self._arima_forecast,
            'neural_network': self._neural_network_forecast,
            'ensemble': self._ensemble_forecast
        }
    
    def create_forecasting_scenario(self, company_id: str, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new forecasting scenario with calibration parameters.
        """
        try:
            company = Company.objects.get(id=company_id)
            
            # Extract scenario parameters
            name = scenario_data.get('name', '')
            description = scenario_data.get('description', '')
            forecast_type = scenario_data.get('forecast_type', 'sales_forecast')
            time_horizon = scenario_data.get('time_horizon', 12)  # months
            confidence_level = scenario_data.get('confidence_level', 0.95)
            model_type = scenario_data.get('model_type', 'ensemble')
            
            # Calibration parameters
            calibration_params = scenario_data.get('calibration', {})
            historical_periods = calibration_params.get('historical_periods', 24)
            validation_split = calibration_params.get('validation_split', 0.2)
            min_data_points = calibration_params.get('min_data_points', 12)
            
            # Scenario parameters
            scenario_params = {
                'forecast_type': forecast_type,
                'time_horizon': time_horizon,
                'confidence_level': confidence_level,
                'model_type': model_type,
                'calibration': calibration_params,
                'variables': scenario_data.get('variables', {}),
                'assumptions': scenario_data.get('assumptions', {}),
                'constraints': scenario_data.get('constraints', {})
            }
            
            # Create scenario
            scenario = SimulationScenario.objects.create(
                company=company,
                name=name,
                description=description,
                scenario_type='sales_forecast',
                parameters=scenario_params,
                created_by=User.objects.filter(company=company).first()
            )
            
            # Run initial calibration
            calibration_result = self._run_calibration(scenario, historical_periods, validation_split)
            
            return {
                'status': 'success',
                'scenario_id': str(scenario.id),
                'calibration_result': calibration_result
            }
            
        except Exception as e:
            logger.error(f"Failed to create forecasting scenario: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def run_multi_scenario_analysis(self, company_id: str, scenario_ids: List[str]) -> Dict[str, Any]:
        """
        Run multi-scenario analysis and comparison.
        """
        try:
            company = Company.objects.get(id=company_id)
            scenarios = SimulationScenario.objects.filter(
                id__in=scenario_ids,
                company=company
            )
            
            if not scenarios.exists():
                return {
                    'status': 'error',
                    'error': 'No scenarios found'
                }
            
            # Run each scenario
            scenario_results = []
            for scenario in scenarios:
                result = simulation_engine.run_simulation(
                    scenario,
                    User.objects.filter(company=company).first()
                )
                scenario_results.append({
                    'scenario_id': str(scenario.id),
                    'scenario_name': scenario.name,
                    'result': result
                })
            
            # Compare scenarios
            comparison = self._compare_scenarios(scenario_results)
            
            # Generate confidence intervals
            confidence_analysis = self._generate_confidence_intervals(scenario_results)
            
            # Create scenario diff analysis
            diff_analysis = self._create_scenario_diff_analysis(scenario_results)
            
            return {
                'status': 'success',
                'scenario_results': scenario_results,
                'comparison': comparison,
                'confidence_analysis': confidence_analysis,
                'diff_analysis': diff_analysis
            }
            
        except Exception as e:
            logger.error(f"Multi-scenario analysis failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def calibrate_forecasting_model(self, scenario_id: str, calibration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calibrate forecasting model with historical data.
        """
        try:
            scenario = SimulationScenario.objects.get(id=scenario_id)
            
            # Extract calibration parameters
            model_type = calibration_data.get('model_type', 'ensemble')
            historical_data = calibration_data.get('historical_data', [])
            validation_periods = calibration_data.get('validation_periods', 3)
            confidence_level = calibration_data.get('confidence_level', 0.95)
            
            # Run model calibration
            calibration_result = self._run_model_calibration(
                model_type, historical_data, validation_periods, confidence_level
            )
            
            # Update scenario with calibration results
            scenario.parameters['calibration_result'] = calibration_result
            scenario.save()
            
            return {
                'status': 'success',
                'calibration_result': calibration_result
            }
            
        except Exception as e:
            logger.error(f"Model calibration failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _run_calibration(self, scenario: SimulationScenario, historical_periods: int, validation_split: float) -> Dict[str, Any]:
        """Run initial calibration for the scenario"""
        # Get historical data
        historical_data = self._get_historical_data(scenario.company, historical_periods)
        
        # Split data for validation
        split_index = int(len(historical_data) * (1 - validation_split))
        training_data = historical_data[:split_index]
        validation_data = historical_data[split_index:]
        
        # Run calibration
        calibration_result = {
            'training_data_points': len(training_data),
            'validation_data_points': len(validation_data),
            'model_performance': self._calculate_model_performance(training_data, validation_data),
            'confidence_intervals': self._calculate_confidence_intervals(historical_data),
            'trend_analysis': self._analyze_trends(historical_data),
            'seasonality_analysis': self._analyze_seasonality(historical_data),
            'anomaly_detection': self._detect_anomalies(historical_data)
        }
        
        return calibration_result
    
    def _get_historical_data(self, company: Company, periods: int) -> List[Dict[str, Any]]:
        """Get historical data for calibration"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=periods * 30)  # Approximate months
        
        # Get monthly aggregated data
        historical_data = []
        
        for i in range(periods):
            period_start = start_date + timedelta(days=i * 30)
            period_end = period_start + timedelta(days=30)
            
            # Get data for this period
            leads_count = Lead.objects.filter(
                company=company,
                created_at__gte=period_start,
                created_at__lt=period_end
            ).count()
            
            deals_count = Deal.objects.filter(
                company=company,
                created_at__gte=period_start,
                created_at__lt=period_end
            ).count()
            
            closed_deals_count = Deal.objects.filter(
                company=company,
                stage='closed_won',
                closed_at__gte=period_start,
                closed_at__lt=period_end
            ).count()
            
            closed_deals_value = Deal.objects.filter(
                company=company,
                stage='closed_won',
                closed_at__gte=period_start,
                closed_at__lt=period_end
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            historical_data.append({
                'period': i + 1,
                'date': period_start.isoformat(),
                'leads_count': leads_count,
                'deals_count': deals_count,
                'closed_deals_count': closed_deals_count,
                'closed_deals_value': float(closed_deals_value),
                'conversion_rate': closed_deals_count / deals_count if deals_count > 0 else 0
            })
        
        return historical_data
    
    def _calculate_model_performance(self, training_data: List[Dict], validation_data: List[Dict]) -> Dict[str, float]:
        """Calculate model performance metrics"""
        if not validation_data:
            return {'mae': 0, 'rmse': 0, 'mape': 0, 'r2': 0}
        
        # Simple performance calculation (would be more sophisticated in production)
        actual_values = [d['closed_deals_value'] for d in validation_data]
        predicted_values = [d['closed_deals_value'] * 1.1 for d in validation_data]  # Mock prediction
        
        # Calculate metrics
        mae = sum(abs(a - p) for a, p in zip(actual_values, predicted_values)) / len(actual_values)
        rmse = (sum((a - p) ** 2 for a, p in zip(actual_values, predicted_values)) / len(actual_values)) ** 0.5
        mape = sum(abs((a - p) / a) for a, p in zip(actual_values, predicted_values) if a > 0) / len(actual_values) * 100
        
        # R-squared calculation
        mean_actual = sum(actual_values) / len(actual_values)
        ss_tot = sum((a - mean_actual) ** 2 for a in actual_values)
        ss_res = sum((a - p) ** 2 for a, p in zip(actual_values, predicted_values))
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r2': r2
        }
    
    def _calculate_confidence_intervals(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Calculate confidence intervals for forecasts"""
        values = [d['closed_deals_value'] for d in historical_data]
        
        if not values:
            return {'lower': 0, 'upper': 0, 'mean': 0}
        
        mean_value = sum(values) / len(values)
        std_dev = (sum((v - mean_value) ** 2 for v in values) / len(values)) ** 0.5
        
        # 95% confidence interval
        confidence_factor = 1.96
        lower_bound = mean_value - (confidence_factor * std_dev)
        upper_bound = mean_value + (confidence_factor * std_dev)
        
        return {
            'lower': max(0, lower_bound),
            'upper': upper_bound,
            'mean': mean_value,
            'std_dev': std_dev
        }
    
    def _analyze_trends(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze trends in historical data"""
        if len(historical_data) < 2:
            return {'trend': 'insufficient_data', 'slope': 0, 'direction': 'stable'}
        
        values = [d['closed_deals_value'] for d in historical_data]
        
        # Calculate linear trend
        n = len(values)
        x_values = list(range(n))
        
        # Linear regression slope
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        slope = numerator / denominator if denominator > 0 else 0
        
        # Determine trend direction
        if slope > 0.1:
            direction = 'increasing'
        elif slope < -0.1:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        return {
            'trend': direction,
            'slope': slope,
            'direction': direction,
            'strength': abs(slope)
        }
    
    def _analyze_seasonality(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze seasonality patterns"""
        if len(historical_data) < 12:
            return {'seasonality': 'insufficient_data', 'pattern': 'none'}
        
        values = [d['closed_deals_value'] for d in historical_data]
        
        # Simple seasonality analysis
        monthly_averages = {}
        for i, value in enumerate(values):
            month = (i % 12) + 1
            if month not in monthly_averages:
                monthly_averages[month] = []
            monthly_averages[month].append(value)
        
        # Calculate seasonal indices
        seasonal_indices = {}
        overall_mean = sum(values) / len(values)
        
        for month, month_values in monthly_averages.items():
            month_mean = sum(month_values) / len(month_values)
            seasonal_indices[month] = month_mean / overall_mean if overall_mean > 0 else 1
        
        # Find peak and low months
        peak_month = max(seasonal_indices.items(), key=lambda x: x[1])
        low_month = min(seasonal_indices.items(), key=lambda x: x[1])
        
        return {
            'seasonality': 'detected' if max(seasonal_indices.values()) - min(seasonal_indices.values()) > 0.2 else 'none',
            'pattern': 'monthly',
            'seasonal_indices': seasonal_indices,
            'peak_month': peak_month[0],
            'low_month': low_month[0],
            'variation': max(seasonal_indices.values()) - min(seasonal_indices.values())
        }
    
    def _detect_anomalies(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Detect anomalies in historical data"""
        values = [d['closed_deals_value'] for d in historical_data]
        
        if len(values) < 3:
            return {'anomalies': [], 'count': 0}
        
        # Calculate z-scores
        mean_value = sum(values) / len(values)
        std_dev = (sum((v - mean_value) ** 2 for v in values) / len(values)) ** 0.5
        
        anomalies = []
        for i, value in enumerate(values):
            z_score = abs((value - mean_value) / std_dev) if std_dev > 0 else 0
            if z_score > 2:  # Threshold for anomaly
                anomalies.append({
                    'period': i + 1,
                    'value': value,
                    'z_score': z_score,
                    'severity': 'high' if z_score > 3 else 'medium'
                })
        
        return {
            'anomalies': anomalies,
            'count': len(anomalies),
            'threshold': 2.0
        }
    
    def _compare_scenarios(self, scenario_results: List[Dict]) -> Dict[str, Any]:
        """Compare multiple scenarios"""
        if len(scenario_results) < 2:
            return {'comparison': 'insufficient_scenarios'}
        
        # Extract key metrics from each scenario
        scenario_metrics = []
        for result in scenario_results:
            output_data = result['result'].output_data or {}
            metrics = result['result'].metrics or {}
            
            scenario_metrics.append({
                'scenario_id': result['scenario_id'],
                'scenario_name': result['scenario_name'],
                'total_revenue': output_data.get('total_projected_revenue', 0),
                'monthly_avg': output_data.get('monthly_forecasts', [{}])[0].get('projected_monthly_revenue', 0) if output_data.get('monthly_forecasts') else 0,
                'confidence': metrics.get('confidence_score', 0.5)
            })
        
        # Calculate comparison metrics
        total_revenues = [s['total_revenue'] for s in scenario_metrics]
        max_revenue = max(total_revenues)
        min_revenue = min(total_revenues)
        avg_revenue = sum(total_revenues) / len(total_revenues)
        
        # Find best and worst scenarios
        best_scenario = max(scenario_metrics, key=lambda x: x['total_revenue'])
        worst_scenario = min(scenario_metrics, key=lambda x: x['total_revenue'])
        
        return {
            'scenario_count': len(scenario_metrics),
            'revenue_range': {
                'min': min_revenue,
                'max': max_revenue,
                'average': avg_revenue,
                'variance': sum((r - avg_revenue) ** 2 for r in total_revenues) / len(total_revenues)
            },
            'best_scenario': best_scenario,
            'worst_scenario': worst_scenario,
            'scenario_rankings': sorted(scenario_metrics, key=lambda x: x['total_revenue'], reverse=True)
        }
    
    def _generate_confidence_intervals(self, scenario_results: List[Dict]) -> Dict[str, Any]:
        """Generate confidence intervals for scenario results"""
        revenues = []
        for result in scenario_results:
            output_data = result['result'].output_data or {}
            total_revenue = output_data.get('total_projected_revenue', 0)
            revenues.append(total_revenue)
        
        if not revenues:
            return {'confidence_intervals': []}
        
        # Calculate confidence intervals
        mean_revenue = sum(revenues) / len(revenues)
        std_dev = (sum((r - mean_revenue) ** 2 for r in revenues) / len(revenues)) ** 0.5
        
        confidence_levels = [0.68, 0.95, 0.99]  # 1σ, 2σ, 3σ
        confidence_intervals = []
        
        for level in confidence_levels:
            if level == 0.68:
                factor = 1.0
            elif level == 0.95:
                factor = 1.96
            else:  # 0.99
                factor = 2.58
            
            lower = mean_revenue - (factor * std_dev)
            upper = mean_revenue + (factor * std_dev)
            
            confidence_intervals.append({
                'level': level,
                'lower_bound': max(0, lower),
                'upper_bound': upper,
                'range': upper - lower
            })
        
        return {
            'mean_revenue': mean_revenue,
            'std_deviation': std_dev,
            'confidence_intervals': confidence_intervals
        }
    
    def _create_scenario_diff_analysis(self, scenario_results: List[Dict]) -> Dict[str, Any]:
        """Create detailed scenario difference analysis"""
        if len(scenario_results) < 2:
            return {'diff_analysis': 'insufficient_scenarios'}
        
        # Compare each scenario pair
        scenario_pairs = []
        for i in range(len(scenario_results)):
            for j in range(i + 1, len(scenario_results)):
                scenario1 = scenario_results[i]
                scenario2 = scenario_results[j]
                
                output1 = scenario1['result'].output_data or {}
                output2 = scenario2['result'].output_data or {}
                
                revenue1 = output1.get('total_projected_revenue', 0)
                revenue2 = output2.get('total_projected_revenue', 0)
                
                diff_analysis = {
                    'scenario1': scenario1['scenario_name'],
                    'scenario2': scenario2['scenario_name'],
                    'revenue_difference': revenue2 - revenue1,
                    'percentage_difference': ((revenue2 - revenue1) / revenue1 * 100) if revenue1 > 0 else 0,
                    'better_scenario': scenario2['scenario_name'] if revenue2 > revenue1 else scenario1['scenario_name']
                }
                
                scenario_pairs.append(diff_analysis)
        
        return {
            'scenario_pairs': scenario_pairs,
            'total_comparisons': len(scenario_pairs)
        }
    
    def _run_model_calibration(self, model_type: str, historical_data: List[Dict], validation_periods: int, confidence_level: float) -> Dict[str, Any]:
        """Run model calibration with historical data"""
        # This would integrate with actual ML models
        # For now, return mock calibration results
        
        return {
            'model_type': model_type,
            'calibration_score': 0.85,
            'validation_accuracy': 0.82,
            'confidence_level': confidence_level,
            'model_parameters': {
                'learning_rate': 0.01,
                'epochs': 100,
                'batch_size': 32
            },
            'performance_metrics': {
                'mae': 1250.50,
                'rmse': 1850.75,
                'r2': 0.78
            }
        }
    
    # Forecasting model implementations (placeholders)
    def _linear_regression_forecast(self, data: List[Dict]) -> Dict[str, Any]:
        """Linear regression forecasting model"""
        return {'model': 'linear_regression', 'forecast': []}
    
    def _exponential_smoothing_forecast(self, data: List[Dict]) -> Dict[str, Any]:
        """Exponential smoothing forecasting model"""
        return {'model': 'exponential_smoothing', 'forecast': []}
    
    def _arima_forecast(self, data: List[Dict]) -> Dict[str, Any]:
        """ARIMA forecasting model"""
        return {'model': 'arima', 'forecast': []}
    
    def _neural_network_forecast(self, data: List[Dict]) -> Dict[str, Any]:
        """Neural network forecasting model"""
        return {'model': 'neural_network', 'forecast': []}
    
    def _ensemble_forecast(self, data: List[Dict]) -> Dict[str, Any]:
        """Ensemble forecasting model"""
        return {'model': 'ensemble', 'forecast': []}

# API Views for Forecasting UI
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_forecasting_scenario(request):
    """API endpoint to create forecasting scenario"""
    ui = ForecastingCalibrationUI()
    result = ui.create_forecasting_scenario(
        str(request.user.company.id),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_multi_scenario_analysis(request):
    """API endpoint to run multi-scenario analysis"""
    ui = ForecastingCalibrationUI()
    result = ui.run_multi_scenario_analysis(
        str(request.user.company.id),
        request.data.get('scenario_ids', [])
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calibrate_forecasting_model(request):
    """API endpoint to calibrate forecasting model"""
    ui = ForecastingCalibrationUI()
    result = ui.calibrate_forecasting_model(
        request.data.get('scenario_id'),
        request.data
    )
    return Response(result, status=status.HTTP_200_OK)
