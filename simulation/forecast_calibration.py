# simulation/forecast_calibration.py
# Forecast Calibration with Confidence Intervals and Stage Volatility

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
from scipy import stats
from scipy.optimize import minimize
import joblib
import pickle
from celery import shared_task

from .models import (
    SimulationScenario, SimulationResult, ForecastCalibration,
    ConfidenceInterval, StageVolatility, BacktestResult, CalibrationMetrics
)
from core.models import User, Company
from crm.models import Lead, Deal, Account

logger = logging.getLogger(__name__)

class ForecastCalibrationEngine:
    """
    Advanced forecast calibration engine with confidence intervals,
    stage volatility analysis, and backtesting capabilities.
    """
    
    def __init__(self):
        self.calibration_methods = {
            'isotonic': self._isotonic_calibration,
            'platt': self._platt_calibration,
            'temperature': self._temperature_calibration,
            'beta': self._beta_calibration
        }
        
        self.volatility_models = {
            'garch': self._garch_volatility,
            'ewma': self._ewma_volatility,
            'historical': self._historical_volatility,
            'monte_carlo': self._monte_carlo_volatility
        }
        
        self.confidence_levels = [0.68, 0.80, 0.90, 0.95, 0.99]
    
    def calibrate_forecast_model(self, model_id: str, calibration_data: List[Dict[str, Any]], 
                               calibration_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calibrate forecast model with confidence intervals and volatility analysis.
        """
        try:
            # Get model and historical data
            model_record = self._get_model_record(model_id)
            historical_data = self._prepare_historical_data(calibration_data, calibration_config)
            
            if len(historical_data) < 100:
                return {
                    'status': 'error',
                    'error': 'Insufficient historical data for calibration (minimum 100 records required)'
                }
            
            # Split data for calibration
            train_data, test_data = self._split_calibration_data(historical_data, calibration_config)
            
            # Train base model
            base_model = self._train_base_model(train_data, calibration_config)
            
            # Calibrate model
            calibration_method = calibration_config.get('calibration_method', 'isotonic')
            calibrated_model = self._calibrate_model(base_model, train_data, calibration_method)
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                calibrated_model, test_data, calibration_config
            )
            
            # Analyze stage volatility
            stage_volatility = self._analyze_stage_volatility(historical_data, calibration_config)
            
            # Perform backtesting
            backtest_results = self._perform_backtesting(
                calibrated_model, historical_data, calibration_config
            )
            
            # Calculate calibration metrics
            calibration_metrics = self._calculate_calibration_metrics(
                calibrated_model, test_data, confidence_intervals
            )
            
            # Save calibration results
            calibration_record = self._save_calibration_results(
                model_record, calibrated_model, confidence_intervals,
                stage_volatility, backtest_results, calibration_metrics
            )
            
            return {
                'status': 'success',
                'calibration_id': str(calibration_record.id),
                'confidence_intervals': confidence_intervals,
                'stage_volatility': stage_volatility,
                'backtest_results': backtest_results,
                'calibration_metrics': calibration_metrics,
                'calibration_method': calibration_method
            }
            
        except Exception as e:
            logger.error(f"Forecast calibration failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def generate_forecast_with_confidence(self, model_id: str, forecast_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate forecast with confidence intervals and volatility bands.
        """
        try:
            # Get calibrated model
            calibration_record = ForecastCalibration.objects.filter(
                model_id=model_id,
                is_active=True
            ).order_by('-created_at').first()
            
            if not calibration_record:
                return {
                    'status': 'error',
                    'error': 'No calibrated model found'
                }
            
            # Load calibrated model
            calibrated_model = pickle.loads(calibration_record.calibrated_model)
            
            # Generate base forecast
            base_forecast = self._generate_base_forecast(calibrated_model, forecast_config)
            
            # Apply confidence intervals
            confidence_forecast = self._apply_confidence_intervals(
                base_forecast, calibration_record.confidence_intervals, forecast_config
            )
            
            # Apply volatility bands
            volatility_forecast = self._apply_volatility_bands(
                confidence_forecast, calibration_record.stage_volatility, forecast_config
            )
            
            # Generate scenario analysis
            scenario_analysis = self._generate_scenario_analysis(
                volatility_forecast, forecast_config
            )
            
            return {
                'status': 'success',
                'base_forecast': base_forecast,
                'confidence_forecast': confidence_forecast,
                'volatility_forecast': volatility_forecast,
                'scenario_analysis': scenario_analysis,
                'forecast_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Forecast generation failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _isotonic_calibration(self, model, train_data: List[Dict[str, Any]]) -> Any:
        """Isotonic regression calibration"""
        try:
            from sklearn.isotonic import IsotonicRegression
            
            # Get model predictions
            X_train = np.array([record['features'] for record in train_data])
            y_train = np.array([record['target'] for record in train_data])
            
            # Get model predictions
            y_pred = model.predict(X_train)
            
            # Fit isotonic regression
            isotonic_reg = IsotonicRegression(out_of_bounds='clip')
            isotonic_reg.fit(y_pred, y_train)
            
            # Create calibrated model
            class CalibratedModel:
                def __init__(self, base_model, calibrator):
                    self.base_model = base_model
                    self.calibrator = calibrator
                
                def predict(self, X):
                    base_pred = self.base_model.predict(X)
                    return self.calibrator.transform(base_pred)
            
            return CalibratedModel(model, isotonic_reg)
            
        except Exception as e:
            logger.error(f"Isotonic calibration failed: {str(e)}")
            return model
    
    def _platt_calibration(self, model, train_data: List[Dict[str, Any]]) -> Any:
        """Platt scaling calibration"""
        try:
            from sklearn.linear_model import LogisticRegression
            
            # Get model predictions
            X_train = np.array([record['features'] for record in train_data])
            y_train = np.array([record['target'] for record in train_data])
            
            # Get model predictions
            y_pred = model.predict(X_train)
            
            # Fit Platt scaling
            platt_reg = LogisticRegression()
            platt_reg.fit(y_pred.reshape(-1, 1), y_train)
            
            # Create calibrated model
            class CalibratedModel:
                def __init__(self, base_model, calibrator):
                    self.base_model = base_model
                    self.calibrator = calibrator
                
                def predict(self, X):
                    base_pred = self.base_model.predict(X)
                    return self.calibrator.predict_proba(base_pred.reshape(-1, 1))[:, 1]
            
            return CalibratedModel(model, platt_reg)
            
        except Exception as e:
            logger.error(f"Platt calibration failed: {str(e)}")
            return model
    
    def _temperature_calibration(self, model, train_data: List[Dict[str, Any]]) -> Any:
        """Temperature scaling calibration"""
        try:
            # Get model predictions
            X_train = np.array([record['features'] for record in train_data])
            y_train = np.array([record['target'] for record in train_data])
            
            # Get model predictions
            y_pred = model.predict(X_train)
            
            # Optimize temperature parameter
            def temperature_loss(T):
                scaled_pred = y_pred / T
                # Apply softmax and calculate loss
                exp_pred = np.exp(scaled_pred)
                softmax_pred = exp_pred / np.sum(exp_pred, axis=1, keepdims=True)
                loss = -np.mean(y_train * np.log(softmax_pred + 1e-8))
                return loss
            
            result = minimize(temperature_loss, x0=1.0, method='BFGS')
            optimal_temperature = result.x[0]
            
            # Create calibrated model
            class CalibratedModel:
                def __init__(self, base_model, temperature):
                    self.base_model = base_model
                    self.temperature = temperature
                
                def predict(self, X):
                    base_pred = self.base_model.predict(X)
                    return base_pred / self.temperature
            
            return CalibratedModel(model, optimal_temperature)
            
        except Exception as e:
            logger.error(f"Temperature calibration failed: {str(e)}")
            return model
    
    def _beta_calibration(self, model, train_data: List[Dict[str, Any]]) -> Any:
        """Beta calibration"""
        try:
            from scipy.special import betaln
            
            # Get model predictions
            X_train = np.array([record['features'] for record in train_data])
            y_train = np.array([record['target'] for record in train_data])
            
            # Get model predictions
            y_pred = model.predict(X_train)
            
            # Optimize beta parameters
            def beta_loss(params):
                a, b = params
                # Calculate beta distribution parameters
                alpha = a * y_pred + 1
                beta = b * (1 - y_pred) + 1
                
                # Calculate negative log-likelihood
                nll = -np.sum(betaln(alpha, beta) + (alpha - 1) * np.log(y_pred + 1e-8) + 
                             (beta - 1) * np.log(1 - y_pred + 1e-8))
                return nll
            
            result = minimize(beta_loss, x0=[1.0, 1.0], method='BFGS')
            optimal_a, optimal_b = result.x
            
            # Create calibrated model
            class CalibratedModel:
                def __init__(self, base_model, a, b):
                    self.base_model = base_model
                    self.a = a
                    self.b = b
                
                def predict(self, X):
                    base_pred = self.base_model.predict(X)
                    return (self.a * base_pred + 1) / (self.a * base_pred + self.b * (1 - base_pred) + 2)
            
            return CalibratedModel(model, optimal_a, optimal_b)
            
        except Exception as e:
            logger.error(f"Beta calibration failed: {str(e)}")
            return model
    
    def _calculate_confidence_intervals(self, calibrated_model: Any, test_data: List[Dict[str, Any]], 
                                      config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confidence intervals for forecasts"""
        try:
            # Get test predictions
            X_test = np.array([record['features'] for record in test_data])
            y_test = np.array([record['target'] for record in test_data])
            
            # Get calibrated predictions
            y_pred = calibrated_model.predict(X_test)
            
            # Calculate prediction intervals
            confidence_intervals = {}
            
            for confidence_level in self.confidence_levels:
                # Calculate quantiles
                alpha = 1 - confidence_level
                lower_quantile = alpha / 2
                upper_quantile = 1 - alpha / 2
                
                # Calculate prediction intervals
                prediction_std = np.std(y_test - y_pred)
                z_score = stats.norm.ppf(upper_quantile)
                
                lower_bound = y_pred - z_score * prediction_std
                upper_bound = y_pred + z_score * prediction_std
                
                confidence_intervals[f'{confidence_level:.2f}'] = {
                    'lower_bound': lower_bound.tolist(),
                    'upper_bound': upper_bound.tolist(),
                    'width': (upper_bound - lower_bound).tolist()
                }
            
            return confidence_intervals
            
        except Exception as e:
            logger.error(f"Confidence interval calculation failed: {str(e)}")
            return {}
    
    def _analyze_stage_volatility(self, historical_data: List[Dict[str, Any]], 
                                config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze stage volatility in historical data"""
        try:
            # Group data by stages
            stage_data = {}
            for record in historical_data:
                stage = record.get('stage', 'unknown')
                if stage not in stage_data:
                    stage_data[stage] = []
                stage_data[stage].append(record)
            
            # Calculate volatility for each stage
            stage_volatility = {}
            
            for stage, data in stage_data.items():
                if len(data) < 10:  # Need minimum data points
                    continue
                
                # Extract values for volatility calculation
                values = [record['value'] for record in data]
                timestamps = [record['timestamp'] for record in data]
                
                # Calculate different volatility measures
                volatility_measures = {}
                
                # Historical volatility
                volatility_measures['historical'] = np.std(values)
                
                # EWMA volatility
                volatility_measures['ewma'] = self._calculate_ewma_volatility(values)
                
                # GARCH volatility (simplified)
                volatility_measures['garch'] = self._calculate_garch_volatility(values)
                
                # Monte Carlo volatility
                volatility_measures['monte_carlo'] = self._calculate_monte_carlo_volatility(values)
                
                stage_volatility[stage] = {
                    'volatility_measures': volatility_measures,
                    'data_points': len(data),
                    'mean_value': np.mean(values),
                    'std_value': np.std(values),
                    'min_value': np.min(values),
                    'max_value': np.max(values)
                }
            
            return stage_volatility
            
        except Exception as e:
            logger.error(f"Stage volatility analysis failed: {str(e)}")
            return {}
    
    def _calculate_ewma_volatility(self, values: List[float], alpha: float = 0.06) -> float:
        """Calculate EWMA volatility"""
        try:
            if len(values) < 2:
                return 0.0
            
            # Calculate returns
            returns = np.diff(np.log(values + 1e-8))
            
            # Calculate EWMA variance
            ewma_var = np.zeros_like(returns)
            ewma_var[0] = returns[0] ** 2
            
            for i in range(1, len(returns)):
                ewma_var[i] = alpha * returns[i] ** 2 + (1 - alpha) * ewma_var[i-1]
            
            return float(np.sqrt(ewma_var[-1]))
            
        except Exception as e:
            logger.error(f"EWMA volatility calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_garch_volatility(self, values: List[float]) -> float:
        """Calculate GARCH volatility (simplified)"""
        try:
            if len(values) < 10:
                return 0.0
            
            # Calculate returns
            returns = np.diff(np.log(values + 1e-8))
            
            # Simple GARCH(1,1) model
            # This is a simplified implementation
            # In production, use a proper GARCH library
            
            # Calculate variance
            variance = np.var(returns)
            
            # Apply GARCH formula (simplified)
            garch_variance = 0.1 * variance + 0.8 * variance + 0.1 * returns[-1] ** 2
            
            return float(np.sqrt(garch_variance))
            
        except Exception as e:
            logger.error(f"GARCH volatility calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_monte_carlo_volatility(self, values: List[float], n_simulations: int = 1000) -> float:
        """Calculate Monte Carlo volatility"""
        try:
            if len(values) < 10:
                return 0.0
            
            # Calculate returns
            returns = np.diff(np.log(values + 1e-8))
            
            # Monte Carlo simulation
            simulated_returns = []
            for _ in range(n_simulations):
                # Bootstrap sample
                bootstrap_sample = np.random.choice(returns, size=len(returns), replace=True)
                simulated_returns.append(np.std(bootstrap_sample))
            
            return float(np.mean(simulated_returns))
            
        except Exception as e:
            logger.error(f"Monte Carlo volatility calculation failed: {str(e)}")
            return 0.0
    
    def _perform_backtesting(self, calibrated_model: Any, historical_data: List[Dict[str, Any]], 
                           config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform backtesting on historical data"""
        try:
            # Split data into training and testing periods
            split_ratio = config.get('backtest_split_ratio', 0.8)
            split_index = int(len(historical_data) * split_ratio)
            
            train_data = historical_data[:split_index]
            test_data = historical_data[split_index:]
            
            # Train model on training data
            model = self._train_base_model(train_data, config)
            calibrated_model = self._calibrate_model(model, train_data, config.get('calibration_method', 'isotonic'))
            
            # Test on out-of-sample data
            test_predictions = []
            test_actuals = []
            
            for record in test_data:
                try:
                    # Make prediction
                    prediction = calibrated_model.predict([record['features']])
                    test_predictions.append(prediction[0])
                    test_actuals.append(record['target'])
                except Exception as e:
                    logger.error(f"Backtest prediction failed: {str(e)}")
                    continue
            
            if not test_predictions:
                return {
                    'status': 'error',
                    'error': 'No valid predictions for backtesting'
                }
            
            # Calculate backtest metrics
            mae = np.mean(np.abs(np.array(test_actuals) - np.array(test_predictions)))
            rmse = np.sqrt(np.mean((np.array(test_actuals) - np.array(test_predictions)) ** 2))
            mape = np.mean(np.abs((np.array(test_actuals) - np.array(test_predictions)) / (np.array(test_actuals) + 1e-8))) * 100
            
            # Calculate directional accuracy
            actual_direction = np.diff(test_actuals) > 0
            predicted_direction = np.diff(test_predictions) > 0
            directional_accuracy = np.mean(actual_direction == predicted_direction) * 100
            
            return {
                'mae': float(mae),
                'rmse': float(rmse),
                'mape': float(mape),
                'directional_accuracy': float(directional_accuracy),
                'test_periods': len(test_predictions),
                'backtest_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Backtesting failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _calculate_calibration_metrics(self, calibrated_model: Any, test_data: List[Dict[str, Any]], 
                                     confidence_intervals: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate calibration metrics"""
        try:
            # Get test predictions
            X_test = np.array([record['features'] for record in test_data])
            y_test = np.array([record['target'] for record in test_data])
            
            # Get calibrated predictions
            y_pred = calibrated_model.predict(X_test)
            
            # Calculate calibration metrics
            metrics = {}
            
            # Mean Absolute Error
            metrics['mae'] = float(np.mean(np.abs(y_test - y_pred)))
            
            # Root Mean Square Error
            metrics['rmse'] = float(np.sqrt(np.mean((y_test - y_pred) ** 2)))
            
            # Mean Absolute Percentage Error
            metrics['mape'] = float(np.mean(np.abs((y_test - y_pred) / (y_test + 1e-8))) * 100)
            
            # R-squared
            ss_res = np.sum((y_test - y_pred) ** 2)
            ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
            metrics['r_squared'] = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
            
            # Calibration score (reliability)
            # This measures how well-calibrated the predictions are
            n_bins = 10
            bin_boundaries = np.linspace(0, 1, n_bins + 1)
            bin_lowers = bin_boundaries[:-1]
            bin_uppers = bin_boundaries[1:]
            
            ece = 0  # Expected Calibration Error
            for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
                in_bin = (y_pred > bin_lower) & (y_pred <= bin_upper)
                prop_in_bin = in_bin.mean()
                
                if prop_in_bin > 0:
                    accuracy_in_bin = y_test[in_bin].mean()
                    avg_confidence_in_bin = y_pred[in_bin].mean()
                    ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
            
            metrics['expected_calibration_error'] = float(ece)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Calibration metrics calculation failed: {str(e)}")
            return {}
    
    def _save_calibration_results(self, model_record: Any, calibrated_model: Any, 
                                confidence_intervals: Dict[str, Any], stage_volatility: Dict[str, Any],
                                backtest_results: Dict[str, Any], calibration_metrics: Dict[str, Any]) -> ForecastCalibration:
        """Save calibration results to database"""
        return ForecastCalibration.objects.create(
            model=model_record,
            calibrated_model=pickle.dumps(calibrated_model),
            confidence_intervals=confidence_intervals,
            stage_volatility=stage_volatility,
            backtest_results=backtest_results,
            calibration_metrics=calibration_metrics,
            is_active=True,
            created_at=timezone.now()
        )
    
    def _get_model_record(self, model_id: str) -> Any:
        """Get model record"""
        # This would get the actual model record
        # For now, return a placeholder
        return None
    
    def _prepare_historical_data(self, calibration_data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare historical data for calibration"""
        # This would prepare the actual historical data
        # For now, return the input data
        return calibration_data
    
    def _split_calibration_data(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split data for calibration"""
        split_ratio = config.get('calibration_split_ratio', 0.8)
        split_index = int(len(data) * split_ratio)
        return data[:split_index], data[split_index:]
    
    def _train_base_model(self, train_data: List[Dict[str, Any]], config: Dict[str, Any]) -> Any:
        """Train base model"""
        # This would train the actual model
        # For now, return a placeholder
        return None
    
    def _calibrate_model(self, model: Any, train_data: List[Dict[str, Any]], method: str) -> Any:
        """Calibrate model using specified method"""
        calibrator = self.calibration_methods.get(method)
        if calibrator:
            return calibrator(model, train_data)
        return model
    
    def _generate_base_forecast(self, model: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate base forecast"""
        # This would generate the actual forecast
        # For now, return a placeholder
        return {
            'forecast_values': [100, 110, 120, 130, 140],
            'forecast_periods': ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05']
        }
    
    def _apply_confidence_intervals(self, base_forecast: Dict[str, Any], confidence_intervals: Dict[str, Any], 
                                  config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply confidence intervals to forecast"""
        # This would apply the actual confidence intervals
        # For now, return the base forecast with added confidence
        return {
            **base_forecast,
            'confidence_intervals': confidence_intervals
        }
    
    def _apply_volatility_bands(self, confidence_forecast: Dict[str, Any], stage_volatility: Dict[str, Any], 
                              config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply volatility bands to forecast"""
        # This would apply the actual volatility bands
        # For now, return the confidence forecast with added volatility
        return {
            **confidence_forecast,
            'volatility_bands': stage_volatility
        }
    
    def _generate_scenario_analysis(self, volatility_forecast: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scenario analysis"""
        # This would generate the actual scenario analysis
        # For now, return a placeholder
        return {
            'optimistic_scenario': [110, 125, 140, 155, 170],
            'realistic_scenario': [100, 110, 120, 130, 140],
            'pessimistic_scenario': [90, 95, 100, 105, 110]
        }

# Celery tasks
@shared_task
def calibrate_forecast_model_async(model_id: str, calibration_data: List[Dict[str, Any]], calibration_config: Dict[str, Any]):
    """Async task to calibrate forecast model"""
    engine = ForecastCalibrationEngine()
    return engine.calibrate_forecast_model(model_id, calibration_data, calibration_config)

@shared_task
def generate_forecast_with_confidence_async(model_id: str, forecast_config: Dict[str, Any]):
    """Async task to generate forecast with confidence"""
    engine = ForecastCalibrationEngine()
    return engine.generate_forecast_with_confidence(model_id, forecast_config)

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calibrate_forecast_model(request):
    """API endpoint to calibrate forecast model"""
    engine = ForecastCalibrationEngine()
    result = engine.calibrate_forecast_model(
        request.data.get('model_id'),
        request.data.get('calibration_data', []),
        request.data.get('calibration_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_forecast_with_confidence(request):
    """API endpoint to generate forecast with confidence"""
    engine = ForecastCalibrationEngine()
    result = engine.generate_forecast_with_confidence(
        request.data.get('model_id'),
        request.data.get('forecast_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)
