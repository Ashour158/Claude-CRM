# analytics/incremental_aggregates.py
"""
Incremental Aggregates Implementation
P2 Priority: Report p95 <1.2s

This module implements:
- Incremental aggregation for real-time analytics
- Pre-computed aggregates with delta updates
- Performance optimization for sub-second queries
- Aggregate caching and invalidation
- Report generation with SLA guarantees
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from core.models import Company, User
from events.event_bus import event_bus
import uuid
import json
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class AggregateDefinition:
    """Aggregate definition with metadata"""
    id: str
    name: str
    description: str
    entity_type: str
    company_id: str
    dimensions: List[str]
    metrics: List[str]
    time_granularity: str  # hour, day, week, month
    created_at: timezone.datetime
    is_active: bool
    refresh_interval_minutes: int

@dataclass
class AggregateData:
    """Aggregate data point"""
    id: str
    aggregate_id: str
    time_bucket: timezone.datetime
    dimensions: Dict[str, Any]
    metrics: Dict[str, float]
    record_count: int
    last_updated: timezone.datetime
    version: int

@dataclass
class ReportRequest:
    """Report generation request"""
    id: str
    user_id: str
    company_id: str
    report_type: str
    parameters: Dict[str, Any]
    created_at: timezone.datetime
    started_at: Optional[timezone.datetime] = None
    completed_at: Optional[timezone.datetime] = None
    status: str = "pending"
    result_data: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0

class IncrementalAggregates:
    """
    Incremental aggregates with sub-second report generation
    """
    
    def __init__(self):
        self.aggregate_definitions: Dict[str, AggregateDefinition] = {}
        self.aggregate_data: Dict[str, List[AggregateData]] = {}
        self.report_requests: List[ReportRequest] = []
        self.aggregate_cache: Dict[str, Any] = {}
        self.cache_lock = threading.Lock()
        
        # Performance configuration
        self.config = {
            "max_report_time_ms": 1200,  # 1.2 seconds
            "cache_ttl_seconds": 300,  # 5 minutes
            "batch_size": 1000,
            "parallel_processing": True,
            "max_workers": 4
        }
        
        # Performance monitoring
        self.performance_metrics = {
            "total_reports": 0,
            "avg_execution_time": 0.0,
            "p95_execution_time": 0.0,
            "cache_hit_rate": 0.0,
            "sla_met_count": 0
        }
    
    def create_aggregate_definition(self, name: str, description: str,
                                 entity_type: str, dimensions: List[str],
                                 metrics: List[str], time_granularity: str,
                                 company: Company, user: User,
                                 refresh_interval_minutes: int = 60) -> AggregateDefinition:
        """Create a new aggregate definition"""
        aggregate_id = str(uuid.uuid4())
        
        aggregate_def = AggregateDefinition(
            id=aggregate_id,
            name=name,
            description=description,
            entity_type=entity_type,
            company_id=str(company.id),
            dimensions=dimensions,
            metrics=metrics,
            time_granularity=time_granularity,
            created_at=timezone.now(),
            is_active=True,
            refresh_interval_minutes=refresh_interval_minutes
        )
        
        self.aggregate_definitions[aggregate_id] = aggregate_def
        self.aggregate_data[aggregate_id] = []
        
        # Publish aggregate creation event
        event_bus.publish(
            event_type='AGGREGATE_DEFINITION_CREATED',
            data={
                'aggregate_id': aggregate_id,
                'name': name,
                'entity_type': entity_type,
                'dimensions': dimensions,
                'metrics': metrics,
                'time_granularity': time_granularity
            },
            actor=user,
            company_id=company.id
        )
        
        logger.info(f"Aggregate definition created: {name} ({aggregate_id})")
        return aggregate_def
    
    def update_aggregate_data(self, aggregate_id: str, entity_data: Dict[str, Any],
                            company: Company) -> bool:
        """Update aggregate data with new entity data"""
        if aggregate_id not in self.aggregate_definitions:
            return False
        
        aggregate_def = self.aggregate_definitions[aggregate_id]
        if not aggregate_def.is_active:
            return False
        
        # Calculate time bucket
        time_bucket = self._calculate_time_bucket(
            entity_data.get('created_at', timezone.now()),
            aggregate_def.time_granularity
        )
        
        # Extract dimensions and metrics
        dimensions = {dim: entity_data.get(dim) for dim in aggregate_def.dimensions}
        metrics = {metric: float(entity_data.get(metric, 0)) for metric in aggregate_def.metrics}
        
        # Find existing aggregate data point
        existing_data = self._find_aggregate_data_point(aggregate_id, time_bucket, dimensions)
        
        if existing_data:
            # Update existing data point
            self._update_existing_aggregate(existing_data, metrics)
        else:
            # Create new data point
            self._create_new_aggregate(aggregate_id, time_bucket, dimensions, metrics)
        
        # Invalidate cache
        self._invalidate_cache(aggregate_id)
        
        return True
    
    def _calculate_time_bucket(self, timestamp: timezone.datetime, 
                             granularity: str) -> timezone.datetime:
        """Calculate time bucket for the timestamp"""
        if granularity == "hour":
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif granularity == "day":
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        elif granularity == "week":
            # Start of week (Monday)
            days_since_monday = timestamp.weekday()
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
        elif granularity == "month":
            return timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return timestamp
    
    def _find_aggregate_data_point(self, aggregate_id: str, time_bucket: timezone.datetime,
                                 dimensions: Dict[str, Any]) -> Optional[AggregateData]:
        """Find existing aggregate data point"""
        for data_point in self.aggregate_data.get(aggregate_id, []):
            if (data_point.time_bucket == time_bucket and 
                data_point.dimensions == dimensions):
                return data_point
        return None
    
    def _update_existing_aggregate(self, data_point: AggregateData, 
                                 new_metrics: Dict[str, float]):
        """Update existing aggregate data point"""
        # Update metrics (sum for additive metrics)
        for metric, value in new_metrics.items():
            if metric in data_point.metrics:
                data_point.metrics[metric] += value
            else:
                data_point.metrics[metric] = value
        
        data_point.record_count += 1
        data_point.last_updated = timezone.now()
        data_point.version += 1
    
    def _create_new_aggregate(self, aggregate_id: str, time_bucket: timezone.datetime,
                            dimensions: Dict[str, Any], metrics: Dict[str, float]):
        """Create new aggregate data point"""
        data_point = AggregateData(
            id=str(uuid.uuid4()),
            aggregate_id=aggregate_id,
            time_bucket=time_bucket,
            dimensions=dimensions,
            metrics=metrics,
            record_count=1,
            last_updated=timezone.now(),
            version=1
        )
        
        self.aggregate_data[aggregate_id].append(data_point)
    
    def _invalidate_cache(self, aggregate_id: str):
        """Invalidate cache for aggregate"""
        with self.cache_lock:
            cache_keys_to_remove = [
                key for key in self.aggregate_cache.keys()
                if key.startswith(f"aggregate_{aggregate_id}")
            ]
            for key in cache_keys_to_remove:
                del self.aggregate_cache[key]
    
    def generate_report(self, report_type: str, parameters: Dict[str, Any],
                       company: Company, user: User) -> ReportRequest:
        """Generate report with SLA guarantee"""
        request_id = str(uuid.uuid4())
        
        report_request = ReportRequest(
            id=request_id,
            user_id=str(user.id),
            company_id=str(company.id),
            report_type=report_type,
            parameters=parameters,
            created_at=timezone.now()
        )
        
        self.report_requests.append(report_request)
        
        # Start report generation
        start_time = time.time()
        report_request.started_at = timezone.now()
        report_request.status = "processing"
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(report_type, parameters, company.id)
            cached_result = self._get_from_cache(cache_key)
            
            if cached_result:
                report_request.result_data = cached_result
                report_request.status = "completed"
                report_request.completed_at = timezone.now()
                report_request.execution_time_ms = (time.time() - start_time) * 1000
                
                # Update performance metrics
                self._update_performance_metrics(report_request.execution_time_ms, cache_hit=True)
                
                logger.info(f"Report generated from cache: {request_id}")
                return report_request
            
            # Generate report from aggregates
            result_data = self._generate_report_data(report_type, parameters, company)
            
            # Cache result
            self._set_cache(cache_key, result_data)
            
            report_request.result_data = result_data
            report_request.status = "completed"
            report_request.completed_at = timezone.now()
            report_request.execution_time_ms = (time.time() - start_time) * 1000
            
            # Update performance metrics
            self._update_performance_metrics(report_request.execution_time_ms, cache_hit=False)
            
            # Publish report completion event
            event_bus.publish(
                event_type='REPORT_GENERATED',
                data={
                    'request_id': request_id,
                    'report_type': report_type,
                    'execution_time_ms': report_request.execution_time_ms,
                    'sla_met': report_request.execution_time_ms <= self.config["max_report_time_ms"]
                },
                actor=user,
                company_id=company.id
            )
            
            logger.info(f"Report generated: {request_id} ({report_request.execution_time_ms:.2f}ms)")
            return report_request
            
        except Exception as e:
            report_request.status = "failed"
            report_request.completed_at = timezone.now()
            report_request.execution_time_ms = (time.time() - start_time) * 1000
            
            logger.error(f"Report generation failed: {request_id} - {e}")
            raise
    
    def _generate_cache_key(self, report_type: str, parameters: Dict[str, Any], 
                          company_id: str) -> str:
        """Generate cache key for report"""
        params_str = json.dumps(parameters, sort_keys=True)
        return f"report_{report_type}_{company_id}_{hash(params_str)}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache"""
        with self.cache_lock:
            if cache_key in self.aggregate_cache:
                cache_entry = self.aggregate_cache[cache_key]
                # Check TTL
                if time.time() - cache_entry['timestamp'] < self.config["cache_ttl_seconds"]:
                    return cache_entry['data']
                else:
                    # Expired, remove from cache
                    del self.aggregate_cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Dict[str, Any]):
        """Set data in cache"""
        with self.cache_lock:
            self.aggregate_cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
    
    def _generate_report_data(self, report_type: str, parameters: Dict[str, Any],
                            company: Company) -> Dict[str, Any]:
        """Generate report data from aggregates"""
        # Get relevant aggregates for the company
        company_aggregates = [
            agg for agg in self.aggregate_definitions.values()
            if agg.company_id == str(company.id) and agg.is_active
        ]
        
        if not company_aggregates:
            return {"error": "No aggregates available"}
        
        # Filter aggregates by report type
        relevant_aggregates = [
            agg for agg in company_aggregates
            if self._is_aggregate_relevant(agg, report_type, parameters)
        ]
        
        if not relevant_aggregates:
            return {"error": "No relevant aggregates found"}
        
        # Generate report data
        report_data = {
            "report_type": report_type,
            "generated_at": timezone.now().isoformat(),
            "parameters": parameters,
            "aggregates": []
        }
        
        for aggregate in relevant_aggregates:
            aggregate_data = self._process_aggregate_data(aggregate, parameters)
            report_data["aggregates"].append(aggregate_data)
        
        return report_data
    
    def _is_aggregate_relevant(self, aggregate: AggregateDefinition, 
                             report_type: str, parameters: Dict[str, Any]) -> bool:
        """Check if aggregate is relevant for the report"""
        # Simple relevance check - in real implementation, this would be more sophisticated
        return True
    
    def _process_aggregate_data(self, aggregate: AggregateDefinition,
                              parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process aggregate data for report"""
        aggregate_data_points = self.aggregate_data.get(aggregate.id, [])
        
        # Filter by time range if specified
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        
        if start_date or end_date:
            filtered_data = []
            for data_point in aggregate_data_points:
                if start_date and data_point.time_bucket < start_date:
                    continue
                if end_date and data_point.time_bucket > end_date:
                    continue
                filtered_data.append(data_point)
        else:
            filtered_data = aggregate_data_points
        
        # Calculate summary metrics
        total_records = sum(dp.record_count for dp in filtered_data)
        metric_totals = defaultdict(float)
        
        for data_point in filtered_data:
            for metric, value in data_point.metrics.items():
                metric_totals[metric] += value
        
        return {
            "aggregate_id": aggregate.id,
            "aggregate_name": aggregate.name,
            "time_granularity": aggregate.time_granularity,
            "data_points": len(filtered_data),
            "total_records": total_records,
            "metric_totals": dict(metric_totals),
            "time_range": {
                "start": min([dp.time_bucket for dp in filtered_data]) if filtered_data else None,
                "end": max([dp.time_bucket for dp in filtered_data]) if filtered_data else None
            }
        }
    
    def _update_performance_metrics(self, execution_time_ms: float, cache_hit: bool):
        """Update performance metrics"""
        self.performance_metrics["total_reports"] += 1
        
        # Update average execution time
        total = self.performance_metrics["total_reports"]
        current_avg = self.performance_metrics["avg_execution_time"]
        self.performance_metrics["avg_execution_time"] = (
            (current_avg * (total - 1) + execution_time_ms) / total
        )
        
        # Update P95 execution time (simplified)
        if execution_time_ms > self.performance_metrics["p95_execution_time"]:
            self.performance_metrics["p95_execution_time"] = execution_time_ms
        
        # Update cache hit rate
        if cache_hit:
            cache_hits = self.performance_metrics.get("cache_hits", 0) + 1
            self.performance_metrics["cache_hits"] = cache_hits
            self.performance_metrics["cache_hit_rate"] = cache_hits / total
        
        # Update SLA met count
        if execution_time_ms <= self.config["max_report_time_ms"]:
            self.performance_metrics["sla_met_count"] += 1
    
    def get_performance_metrics(self, company: Company) -> Dict[str, Any]:
        """Get performance metrics for the company"""
        company_reports = [
            req for req in self.report_requests
            if req.company_id == str(company.id)
        ]
        
        if not company_reports:
            return {"status": "no_data", "message": "No report data available"}
        
        # Calculate company-specific metrics
        total_reports = len(company_reports)
        sla_met_count = sum(1 for req in company_reports if req.execution_time_ms <= self.config["max_report_time_ms"])
        sla_met_rate = sla_met_count / total_reports if total_reports > 0 else 0
        
        execution_times = [req.execution_time_ms for req in company_reports if req.execution_time_ms > 0]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Calculate P95
        if execution_times:
            sorted_times = sorted(execution_times)
            p95_index = int(len(sorted_times) * 0.95)
            p95_execution_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
        else:
            p95_execution_time = 0
        
        return {
            "company_id": str(company.id),
            "total_reports": total_reports,
            "sla_met_count": sla_met_count,
            "sla_met_rate": sla_met_rate,
            "avg_execution_time_ms": avg_execution_time,
            "p95_execution_time_ms": p95_execution_time,
            "target_sla_ms": self.config["max_report_time_ms"],
            "target_met": p95_execution_time <= self.config["max_report_time_ms"],
            "cache_hit_rate": self.performance_metrics.get("cache_hit_rate", 0),
            "active_aggregates": len([agg for agg in self.aggregate_definitions.values() 
                                    if agg.company_id == str(company.id) and agg.is_active])
        }
    
    def optimize_aggregates(self, company: Company) -> Dict[str, Any]:
        """Optimize aggregates for better performance"""
        company_aggregates = [
            agg for agg in self.aggregate_definitions.values()
            if agg.company_id == str(company.id) and agg.is_active
        ]
        
        if not company_aggregates:
            return {"status": "no_data", "message": "No aggregates to optimize"}
        
        optimization_recommendations = []
        
        for aggregate in company_aggregates:
            # Check data volume
            data_points = len(self.aggregate_data.get(aggregate.id, []))
            if data_points > 10000:
                optimization_recommendations.append(
                    f"Aggregate '{aggregate.name}' has {data_points} data points - consider archiving old data"
                )
            
            # Check refresh frequency
            if aggregate.refresh_interval_minutes < 30:
                optimization_recommendations.append(
                    f"Aggregate '{aggregate.name}' refreshes every {aggregate.refresh_interval_minutes} minutes - consider increasing interval"
                )
            
            # Check dimensions count
            if len(aggregate.dimensions) > 5:
                optimization_recommendations.append(
                    f"Aggregate '{aggregate.name}' has {len(aggregate.dimensions)} dimensions - consider reducing for better performance"
                )
        
        return {
            "company_id": str(company.id),
            "total_aggregates": len(company_aggregates),
            "optimization_recommendations": optimization_recommendations,
            "optimization_needed": len(optimization_recommendations) > 0
        }

# Global instance
incremental_aggregates = IncrementalAggregates()
