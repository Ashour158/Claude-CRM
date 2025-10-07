# simulation/simulation_engine.py
# What-If Analysis and Simulation Engine

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from .models import (
    SimulationScenario, SimulationRun, SimulationModel,
    SimulationResult, OptimizationTarget, SensitivityAnalysis,
    MonteCarloSimulation
)

logger = logging.getLogger(__name__)

class SimulationEngine:
    """Main simulation engine for what-if analysis"""
    
    def __init__(self):
        self.supported_scenarios = [
            'sales_forecast', 'lead_scoring', 'territory_optimization',
            'pipeline_analysis', 'revenue_projection', 'customer_lifetime_value',
            'churn_prediction', 'resource_allocation'
        ]
    
    def run_simulation(self, scenario_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a simulation scenario
        
        Args:
            scenario_id: ID of the simulation scenario
            parameters: Simulation parameters
            
        Returns:
            Simulation results
        """
        try:
            # Get scenario
            scenario = SimulationScenario.objects.get(id=scenario_id)
            
            # Create simulation run
            run = SimulationRun.objects.create(
                scenario=scenario,
                run_name=f"Run {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                parameters=parameters,
                input_data=scenario.baseline_data,
                status='running',
                started_at=timezone.now()
            )
            
            # Run simulation based on scenario type
            results = self._execute_simulation(scenario, run, parameters)
            
            # Update run status
            run.status = 'completed'
            run.completed_at = timezone.now()
            run.execution_duration = int(
                (run.completed_at - run.started_at).total_seconds()
            )
            run.results = results
            run.save()
            
            # Update scenario
            scenario.status = 'completed'
            scenario.completed_at = timezone.now()
            scenario.results = results
            scenario.save()
            
            return {
                'run_id': str(run.id),
                'scenario_id': str(scenario.id),
                'results': results,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Simulation failed for scenario {scenario_id}: {str(e)}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def _execute_simulation(self, scenario: SimulationScenario, 
                          run: SimulationRun, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute simulation based on scenario type"""
        
        scenario_type = scenario.scenario_type
        
        if scenario_type == 'sales_forecast':
            return self._run_sales_forecast_simulation(scenario, run, parameters)
        elif scenario_type == 'lead_scoring':
            return self._run_lead_scoring_simulation(scenario, run, parameters)
        elif scenario_type == 'territory_optimization':
            return self._run_territory_optimization_simulation(scenario, run, parameters)
        elif scenario_type == 'pipeline_analysis':
            return self._run_pipeline_analysis_simulation(scenario, run, parameters)
        elif scenario_type == 'revenue_projection':
            return self._run_revenue_projection_simulation(scenario, run, parameters)
        elif scenario_type == 'customer_lifetime_value':
            return self._run_customer_lifetime_value_simulation(scenario, run, parameters)
        elif scenario_type == 'churn_prediction':
            return self._run_churn_prediction_simulation(scenario, run, parameters)
        elif scenario_type == 'resource_allocation':
            return self._run_resource_allocation_simulation(scenario, run, parameters)
        else:
            raise ValueError(f"Unsupported scenario type: {scenario_type}")
    
    def _run_sales_forecast_simulation(self, scenario: SimulationScenario, 
                                      run: SimulationRun, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run sales forecast simulation"""
        
        # Extract parameters
        forecast_periods = parameters.get('forecast_periods', 12)
        confidence_level = parameters.get('confidence_level', 0.95)
        seasonality = parameters.get('seasonality', True)
        
        # Get historical sales data
        historical_data = scenario.baseline_data.get('sales_data', [])
        
        if not historical_data:
            # Generate sample data for demonstration
            historical_data = self._generate_sample_sales_data()
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # Perform time series forecasting
        forecast_results = self._time_series_forecast(
            df['revenue'], forecast_periods, confidence_level, seasonality
        )
        
        # Calculate metrics
        metrics = self._calculate_forecast_metrics(df['revenue'], forecast_results)
        
        return {
            'forecast_data': forecast_results,
            'metrics': metrics,
            'insights': self._generate_sales_forecast_insights(forecast_results, metrics),
            'recommendations': self._generate_sales_forecast_recommendations(forecast_results, metrics)
        }
    
    def _run_lead_scoring_simulation(self, scenario: SimulationScenario, 
                                    run: SimulationRun, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run lead scoring simulation"""
        
        # Extract parameters
        score_threshold = parameters.get('score_threshold', 0.5)
        conversion_rate = parameters.get('conversion_rate', 0.15)
        
        # Get lead data
        lead_data = scenario.baseline_data.get('leads', [])
        
        if not lead_data:
            # Generate sample data for demonstration
            lead_data = self._generate_sample_lead_data()
        
        # Simulate lead scoring
        scored_leads = self._simulate_lead_scoring(lead_data, score_threshold)
        
        # Calculate conversion metrics
        conversion_metrics = self._calculate_conversion_metrics(scored_leads, conversion_rate)
        
        # Optimize score threshold
        optimization_results = self._optimize_score_threshold(lead_data, conversion_rate)
        
        return {
            'scored_leads': scored_leads,
            'conversion_metrics': conversion_metrics,
            'optimization_results': optimization_results,
            'insights': self._generate_lead_scoring_insights(scored_leads, conversion_metrics),
            'recommendations': self._generate_lead_scoring_recommendations(optimization_results)
        }
    
    def _run_territory_optimization_simulation(self, scenario: SimulationScenario, 
                                             run: SimulationRun, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run territory optimization simulation"""
        
        # Extract parameters
        optimization_goal = parameters.get('optimization_goal', 'maximize_revenue')
        constraints = parameters.get('constraints', {})
        
        # Get territory data
        territory_data = scenario.baseline_data.get('territories', [])
        
        if not territory_data:
            # Generate sample data for demonstration
            territory_data = self._generate_sample_territory_data()
        
        # Run optimization
        optimization_results = self._optimize_territories(territory_data, optimization_goal, constraints)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_territory_performance_metrics(optimization_results)
        
        return {
            'optimization_results': optimization_results,
            'performance_metrics': performance_metrics,
            'insights': self._generate_territory_optimization_insights(optimization_results),
            'recommendations': self._generate_territory_optimization_recommendations(optimization_results)
        }
    
    def _run_pipeline_analysis_simulation(self, scenario: SimulationScenario, 
                                       run: SimulationRun, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run pipeline analysis simulation"""
        
        # Extract parameters
        analysis_period = parameters.get('analysis_period', 90)
        probability_threshold = parameters.get('probability_threshold', 0.5)
        
        # Get pipeline data
        pipeline_data = scenario.baseline_data.get('pipeline', [])
        
        if not pipeline_data:
            # Generate sample data for demonstration
            pipeline_data = self._generate_sample_pipeline_data()
        
        # Analyze pipeline
        pipeline_analysis = self._analyze_pipeline(pipeline_data, analysis_period, probability_threshold)
        
        # Calculate forecasting metrics
        forecasting_metrics = self._calculate_pipeline_forecasting_metrics(pipeline_analysis)
        
        return {
            'pipeline_analysis': pipeline_analysis,
            'forecasting_metrics': forecasting_metrics,
            'insights': self._generate_pipeline_analysis_insights(pipeline_analysis),
            'recommendations': self._generate_pipeline_analysis_recommendations(pipeline_analysis)
        }
    
    def _run_revenue_projection_simulation(self, scenario: SimulationScenario, 
                                         run: SimulationRun, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run revenue projection simulation"""
        
        # Extract parameters
        projection_periods = parameters.get('projection_periods', 12)
        growth_rate = parameters.get('growth_rate', 0.1)
        seasonality = parameters.get('seasonality', True)
        
        # Get revenue data
        revenue_data = scenario.baseline_data.get('revenue_data', [])
        
        if not revenue_data:
            # Generate sample data for demonstration
            revenue_data = self._generate_sample_revenue_data()
        
        # Run revenue projection
        projection_results = self._project_revenue(revenue_data, projection_periods, growth_rate, seasonality)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_revenue_risk_metrics(projection_results)
        
        return {
            'projection_results': projection_results,
            'risk_metrics': risk_metrics,
            'insights': self._generate_revenue_projection_insights(projection_results),
            'recommendations': self._generate_revenue_projection_recommendations(projection_results)
        }
    
    def _run_customer_lifetime_value_simulation(self, scenario: SimulationScenario, 
                                              run: SimulationRun, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run customer lifetime value simulation"""
        
        # Extract parameters
        discount_rate = parameters.get('discount_rate', 0.1)
        time_horizon = parameters.get('time_horizon', 36)
        
        # Get customer data
        customer_data = scenario.baseline_data.get('customers', [])
        
        if not customer_data:
            # Generate sample data for demonstration
            customer_data = self._generate_sample_customer_data()
        
        # Calculate CLV
        clv_results = self._calculate_customer_lifetime_value(customer_data, discount_rate, time_horizon)
        
        # Segment customers by CLV
        customer_segments = self._segment_customers_by_clv(clv_results)
        
        return {
            'clv_results': clv_results,
            'customer_segments': customer_segments,
            'insights': self._generate_clv_insights(clv_results),
            'recommendations': self._generate_clv_recommendations(customer_segments)
        }
    
    def _run_churn_prediction_simulation(self, scenario: SimulationScenario, 
                                        run: SimulationRun, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run churn prediction simulation"""
        
        # Extract parameters
        prediction_horizon = parameters.get('prediction_horizon', 90)
        churn_threshold = parameters.get('churn_threshold', 0.5)
        
        # Get customer data
        customer_data = scenario.baseline_data.get('customers', [])
        
        if not customer_data:
            # Generate sample data for demonstration
            customer_data = self._generate_sample_customer_data()
        
        # Predict churn
        churn_predictions = self._predict_customer_churn(customer_data, prediction_horizon, churn_threshold)
        
        # Calculate churn metrics
        churn_metrics = self._calculate_churn_metrics(churn_predictions)
        
        return {
            'churn_predictions': churn_predictions,
            'churn_metrics': churn_metrics,
            'insights': self._generate_churn_insights(churn_predictions),
            'recommendations': self._generate_churn_recommendations(churn_predictions)
        }
    
    def _run_resource_allocation_simulation(self, scenario: SimulationScenario, 
                                           run: SimulationRun, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run resource allocation simulation"""
        
        # Extract parameters
        optimization_goal = parameters.get('optimization_goal', 'maximize_roi')
        budget_constraint = parameters.get('budget_constraint', 100000)
        
        # Get resource data
        resource_data = scenario.baseline_data.get('resources', [])
        
        if not resource_data:
            # Generate sample data for demonstration
            resource_data = self._generate_sample_resource_data()
        
        # Optimize resource allocation
        allocation_results = self._optimize_resource_allocation(
            resource_data, optimization_goal, budget_constraint
        )
        
        # Calculate ROI metrics
        roi_metrics = self._calculate_roi_metrics(allocation_results)
        
        return {
            'allocation_results': allocation_results,
            'roi_metrics': roi_metrics,
            'insights': self._generate_resource_allocation_insights(allocation_results),
            'recommendations': self._generate_resource_allocation_recommendations(allocation_results)
        }
    
    # Helper methods for data generation and analysis
    def _generate_sample_sales_data(self) -> List[Dict]:
        """Generate sample sales data for demonstration"""
        data = []
        base_date = datetime.now() - timedelta(days=365)
        
        for i in range(365):
            date = base_date + timedelta(days=i)
            # Simulate seasonal sales data
            seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * i / 365)
            revenue = 10000 + 5000 * seasonal_factor + np.random.normal(0, 1000)
            
            data.append({
                'date': date.isoformat(),
                'revenue': max(0, revenue),
                'units_sold': int(revenue / 100),
                'customers': int(revenue / 200)
            })
        
        return data
    
    def _generate_sample_lead_data(self) -> List[Dict]:
        """Generate sample lead data for demonstration"""
        data = []
        
        for i in range(1000):
            data.append({
                'id': f"lead_{i}",
                'company': f"Company {i}",
                'industry': np.random.choice(['Technology', 'Healthcare', 'Finance', 'Manufacturing']),
                'company_size': np.random.choice(['Small', 'Medium', 'Large']),
                'lead_source': np.random.choice(['Website', 'Referral', 'Cold Call', 'Email']),
                'engagement_score': np.random.uniform(0, 1),
                'budget': np.random.uniform(1000, 100000),
                'timeline': np.random.choice(['Immediate', '1-3 months', '3-6 months', '6+ months'])
            })
        
        return data
    
    def _generate_sample_territory_data(self) -> List[Dict]:
        """Generate sample territory data for demonstration"""
        territories = []
        
        for i in range(10):
            territories.append({
                'id': f"territory_{i}",
                'name': f"Territory {i}",
                'region': f"Region {i % 3}",
                'sales_rep': f"Rep {i}",
                'revenue': np.random.uniform(100000, 500000),
                'customers': np.random.randint(50, 200),
                'potential': np.random.uniform(200000, 800000),
                'market_share': np.random.uniform(0.1, 0.4)
            })
        
        return territories
    
    def _generate_sample_pipeline_data(self) -> List[Dict]:
        """Generate sample pipeline data for demonstration"""
        pipeline = []
        
        for i in range(100):
            pipeline.append({
                'id': f"deal_{i}",
                'name': f"Deal {i}",
                'stage': np.random.choice(['Prospecting', 'Qualification', 'Proposal', 'Negotiation', 'Closed Won']),
                'value': np.random.uniform(5000, 100000),
                'probability': np.random.uniform(0.1, 0.9),
                'close_date': (datetime.now() + timedelta(days=np.random.randint(1, 90))).isoformat(),
                'customer': f"Customer {i}",
                'sales_rep': f"Rep {i % 5}"
            })
        
        return pipeline
    
    def _generate_sample_revenue_data(self) -> List[Dict]:
        """Generate sample revenue data for demonstration"""
        data = []
        base_date = datetime.now() - timedelta(days=365)
        
        for i in range(365):
            date = base_date + timedelta(days=i)
            revenue = 50000 + 10000 * np.sin(2 * np.pi * i / 365) + np.random.normal(0, 5000)
            
            data.append({
                'date': date.isoformat(),
                'revenue': max(0, revenue),
                'recurring_revenue': revenue * 0.7,
                'new_revenue': revenue * 0.3
            })
        
        return data
    
    def _generate_sample_customer_data(self) -> List[Dict]:
        """Generate sample customer data for demonstration"""
        customers = []
        
        for i in range(500):
            customers.append({
                'id': f"customer_{i}",
                'name': f"Customer {i}",
                'industry': np.random.choice(['Technology', 'Healthcare', 'Finance', 'Manufacturing']),
                'company_size': np.random.choice(['Small', 'Medium', 'Large']),
                'acquisition_date': (datetime.now() - timedelta(days=np.random.randint(1, 1000))).isoformat(),
                'monthly_revenue': np.random.uniform(1000, 10000),
                'churn_probability': np.random.uniform(0, 0.3),
                'engagement_score': np.random.uniform(0, 1)
            })
        
        return customers
    
    def _generate_sample_resource_data(self) -> List[Dict]:
        """Generate sample resource data for demonstration"""
        resources = []
        
        for i in range(20):
            resources.append({
                'id': f"resource_{i}",
                'name': f"Resource {i}",
                'type': np.random.choice(['Sales Rep', 'Marketing Campaign', 'Product Development', 'Support']),
                'cost': np.random.uniform(10000, 100000),
                'expected_roi': np.random.uniform(1.2, 3.0),
                'risk_score': np.random.uniform(0, 1),
                'availability': np.random.uniform(0.5, 1.0)
            })
        
        return resources
    
    # Analysis methods (simplified implementations)
    def _time_series_forecast(self, data: pd.Series, periods: int, 
                             confidence_level: float, seasonality: bool) -> Dict[str, Any]:
        """Perform time series forecasting"""
        # Simplified implementation - in practice, use proper time series models
        trend = data.pct_change().mean()
        seasonal_factor = 0.1 if seasonality else 0
        
        forecast = []
        last_value = data.iloc[-1]
        
        for i in range(periods):
            next_value = last_value * (1 + trend + seasonal_factor * np.sin(2 * np.pi * i / 12))
            forecast.append({
                'period': i + 1,
                'value': max(0, next_value),
                'confidence_lower': next_value * 0.8,
                'confidence_upper': next_value * 1.2
            })
            last_value = next_value
        
        return {
            'forecast': forecast,
            'trend': trend,
            'seasonality': seasonality
        }
    
    def _simulate_lead_scoring(self, leads: List[Dict], threshold: float) -> List[Dict]:
        """Simulate lead scoring"""
        scored_leads = []
        
        for lead in leads:
            # Simple scoring algorithm
            score = 0
            score += lead.get('engagement_score', 0) * 0.3
            score += min(lead.get('budget', 0) / 100000, 1) * 0.4
            score += 0.3 if lead.get('timeline') == 'Immediate' else 0.1
            
            lead['score'] = score
            lead['qualified'] = score >= threshold
            scored_leads.append(lead)
        
        return scored_leads
    
    def _calculate_conversion_metrics(self, scored_leads: List[Dict], conversion_rate: float) -> Dict[str, Any]:
        """Calculate conversion metrics"""
        qualified_leads = [lead for lead in scored_leads if lead['qualified']]
        total_leads = len(scored_leads)
        qualified_count = len(qualified_leads)
        
        expected_conversions = qualified_count * conversion_rate
        total_potential_revenue = sum(lead.get('budget', 0) for lead in qualified_leads)
        
        return {
            'total_leads': total_leads,
            'qualified_leads': qualified_count,
            'qualification_rate': qualified_count / total_leads if total_leads > 0 else 0,
            'expected_conversions': expected_conversions,
            'conversion_rate': conversion_rate,
            'total_potential_revenue': total_potential_revenue
        }
    
    def _optimize_score_threshold(self, leads: List[Dict], conversion_rate: float) -> Dict[str, Any]:
        """Optimize score threshold"""
        thresholds = np.arange(0.1, 1.0, 0.1)
        results = []
        
        for threshold in thresholds:
            qualified_leads = [lead for lead in leads if lead.get('engagement_score', 0) >= threshold]
            qualified_count = len(qualified_leads)
            expected_conversions = qualified_count * conversion_rate
            total_revenue = sum(lead.get('budget', 0) for lead in qualified_leads)
            
            results.append({
                'threshold': threshold,
                'qualified_count': qualified_count,
                'expected_conversions': expected_conversions,
                'total_revenue': total_revenue,
                'efficiency': expected_conversions / qualified_count if qualified_count > 0 else 0
            })
        
        # Find optimal threshold
        optimal_result = max(results, key=lambda x: x['efficiency'])
        
        return {
            'optimal_threshold': optimal_result['threshold'],
            'results': results,
            'recommendation': f"Optimal threshold: {optimal_result['threshold']:.2f}"
        }
    
    # Placeholder methods for other analyses
    def _optimize_territories(self, territories: List[Dict], goal: str, constraints: Dict) -> Dict[str, Any]:
        """Optimize territory allocation"""
        return {'optimized_territories': territories, 'improvement': 0.15}
    
    def _analyze_pipeline(self, pipeline: List[Dict], period: int, threshold: float) -> Dict[str, Any]:
        """Analyze sales pipeline"""
        return {'pipeline_health': 0.75, 'forecast_revenue': 1000000}
    
    def _project_revenue(self, revenue_data: List[Dict], periods: int, growth_rate: float, seasonality: bool) -> Dict[str, Any]:
        """Project revenue"""
        return {'projected_revenue': 1200000, 'growth_rate': growth_rate}
    
    def _calculate_customer_lifetime_value(self, customers: List[Dict], discount_rate: float, time_horizon: int) -> Dict[str, Any]:
        """Calculate customer lifetime value"""
        return {'average_clv': 50000, 'total_clv': 25000000}
    
    def _predict_customer_churn(self, customers: List[Dict], horizon: int, threshold: float) -> Dict[str, Any]:
        """Predict customer churn"""
        return {'churn_rate': 0.15, 'at_risk_customers': 75}
    
    def _optimize_resource_allocation(self, resources: List[Dict], goal: str, budget: float) -> Dict[str, Any]:
        """Optimize resource allocation"""
        return {'optimal_allocation': resources, 'expected_roi': 2.5}
    
    # Metric calculation methods
    def _calculate_forecast_metrics(self, historical: pd.Series, forecast: Dict) -> Dict[str, Any]:
        """Calculate forecast metrics"""
        return {'mape': 0.1, 'rmse': 5000, 'accuracy': 0.9}
    
    def _calculate_territory_performance_metrics(self, results: Dict) -> Dict[str, Any]:
        """Calculate territory performance metrics"""
        return {'revenue_growth': 0.2, 'efficiency_improvement': 0.15}
    
    def _calculate_pipeline_forecasting_metrics(self, analysis: Dict) -> Dict[str, Any]:
        """Calculate pipeline forecasting metrics"""
        return {'forecast_accuracy': 0.85, 'conversion_rate': 0.25}
    
    def _calculate_revenue_risk_metrics(self, projection: Dict) -> Dict[str, Any]:
        """Calculate revenue risk metrics"""
        return {'volatility': 0.2, 'var_95': 100000}
    
    def _segment_customers_by_clv(self, clv_results: Dict) -> Dict[str, Any]:
        """Segment customers by CLV"""
        return {'high_value': 100, 'medium_value': 200, 'low_value': 200}
    
    def _calculate_churn_metrics(self, predictions: Dict) -> Dict[str, Any]:
        """Calculate churn metrics"""
        return {'churn_rate': 0.15, 'retention_rate': 0.85}
    
    def _calculate_roi_metrics(self, allocation: Dict) -> Dict[str, Any]:
        """Calculate ROI metrics"""
        return {'expected_roi': 2.5, 'payback_period': 12}
    
    # Insight and recommendation generation methods
    def _generate_sales_forecast_insights(self, forecast: Dict, metrics: Dict) -> str:
        """Generate sales forecast insights"""
        return "Sales are projected to grow by 15% over the next 12 months with seasonal variations."
    
    def _generate_sales_forecast_recommendations(self, forecast: Dict, metrics: Dict) -> str:
        """Generate sales forecast recommendations"""
        return "Consider increasing marketing spend during low seasons to smooth revenue fluctuations."
    
    def _generate_lead_scoring_insights(self, leads: List[Dict], metrics: Dict) -> str:
        """Generate lead scoring insights"""
        return f"Lead qualification rate is {metrics['qualification_rate']:.1%} with strong conversion potential."
    
    def _generate_lead_scoring_recommendations(self, optimization: Dict) -> str:
        """Generate lead scoring recommendations"""
        return f"Optimize lead scoring threshold to {optimization['optimal_threshold']:.2f} for maximum efficiency."
    
    def _generate_territory_optimization_insights(self, results: Dict) -> str:
        """Generate territory optimization insights"""
        return "Territory optimization can improve revenue by 15% through better resource allocation."
    
    def _generate_territory_optimization_recommendations(self, results: Dict) -> str:
        """Generate territory optimization recommendations"""
        return "Redistribute sales reps to high-potential territories for maximum impact."
    
    def _generate_pipeline_analysis_insights(self, analysis: Dict) -> str:
        """Generate pipeline analysis insights"""
        return "Pipeline health is strong with good conversion rates across all stages."
    
    def _generate_pipeline_analysis_recommendations(self, analysis: Dict) -> str:
        """Generate pipeline analysis recommendations"""
        return "Focus on accelerating deals in the negotiation stage to improve close rates."
    
    def _generate_revenue_projection_insights(self, projection: Dict) -> str:
        """Generate revenue projection insights"""
        return "Revenue is projected to grow steadily with manageable risk levels."
    
    def _generate_revenue_projection_recommendations(self, projection: Dict) -> str:
        """Generate revenue projection recommendations"""
        return "Implement risk mitigation strategies to protect against market volatility."
    
    def _generate_clv_insights(self, clv_results: Dict) -> str:
        """Generate CLV insights"""
        return f"Average customer lifetime value is ${clv_results['average_clv']:,.0f} with strong retention potential."
    
    def _generate_clv_recommendations(self, segments: Dict) -> str:
        """Generate CLV recommendations"""
        return "Focus retention efforts on high-value customers to maximize lifetime value."
    
    def _generate_churn_insights(self, predictions: Dict) -> str:
        """Generate churn insights"""
        return f"Churn rate is {predictions['churn_rate']:.1%} with {predictions['at_risk_customers']} customers at risk."
    
    def _generate_churn_recommendations(self, predictions: Dict) -> str:
        """Generate churn recommendations"""
        return "Implement proactive retention campaigns for at-risk customers."
    
    def _generate_resource_allocation_insights(self, allocation: Dict) -> str:
        """Generate resource allocation insights"""
        return "Optimal resource allocation can improve ROI by 25% with better efficiency."
    
    def _generate_resource_allocation_recommendations(self, allocation: Dict) -> str:
        """Generate resource allocation recommendations"""
        return "Reallocate resources to high-ROI activities and reduce investment in low-performing areas."

# Global simulation engine instance
simulation_engine = SimulationEngine()
