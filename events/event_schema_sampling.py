# events/event_schema_sampling.py
"""
Event Schema Sampling Ramp Implementation
P1 Priority: Invalid block false positives <0.5%

This module implements:
- Event schema validation and sampling
- Block validation with minimal false positives
- Schema evolution tracking
- Performance monitoring
- Compliance reporting
"""

import logging
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from core.models import Company, User
from events.event_bus import event_bus
import uuid
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class EventSchema:
    """Event schema definition"""
    id: str
    schema_name: str
    version: str
    schema_definition: Dict[str, Any]
    created_at: timezone.datetime
    is_active: bool
    validation_rules: Dict[str, Any]
    sample_rate: float
    false_positive_threshold: float

@dataclass
class SchemaValidationResult:
    """Schema validation result"""
    id: str
    event_id: str
    schema_id: str
    is_valid: bool
    validation_errors: List[str]
    validation_time_ms: float
    timestamp: timezone.datetime
    false_positive: bool
    confidence_score: float

@dataclass
class SchemaBlock:
    """Schema validation block"""
    id: str
    block_name: str
    schema_ids: List[str]
    validation_rules: Dict[str, Any]
    is_active: bool
    created_at: timezone.datetime
    false_positive_count: int
    total_validations: int

class EventSchemaSampling:
    """
    Event schema sampling with minimal false positives
    """
    
    def __init__(self):
        self.event_schemas: Dict[str, EventSchema] = {}
        self.schema_blocks: Dict[str, SchemaBlock] = {}
        self.validation_results: List[SchemaValidationResult] = []
        self.sampling_config = {
            "default_sample_rate": 0.1,  # 10% sampling
            "false_positive_threshold": 0.005,  # 0.5% false positive threshold
            "validation_timeout_ms": 100,
            "confidence_threshold": 0.95
        }
    
    def create_event_schema(self, schema_name: str, schema_definition: Dict[str, Any],
                          version: str = "1.0", sample_rate: float = 0.1,
                          false_positive_threshold: float = 0.005) -> EventSchema:
        """Create a new event schema"""
        schema_id = str(uuid.uuid4())
        
        # Validate schema definition
        try:
            jsonschema.Draft7Validator.check_schema(schema_definition)
        except jsonschema.SchemaError as e:
            raise ValueError(f"Invalid schema definition: {e}")
        
        event_schema = EventSchema(
            id=schema_id,
            schema_name=schema_name,
            version=version,
            schema_definition=schema_definition,
            created_at=timezone.now(),
            is_active=True,
            validation_rules=self._extract_validation_rules(schema_definition),
            sample_rate=sample_rate,
            false_positive_threshold=false_positive_threshold
        )
        
        self.event_schemas[schema_id] = event_schema
        
        # Publish schema creation event
        event_bus.publish(
            event_type='EVENT_SCHEMA_CREATED',
            data={
                'schema_id': schema_id,
                'schema_name': schema_name,
                'version': version,
                'sample_rate': sample_rate
            }
        )
        
        logger.info(f"Event schema created: {schema_name} v{version}")
        return event_schema
    
    def _extract_validation_rules(self, schema_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Extract validation rules from schema definition"""
        rules = {
            "required_fields": schema_definition.get("required", []),
            "field_types": {},
            "constraints": {},
            "patterns": {}
        }
        
        properties = schema_definition.get("properties", {})
        for field, definition in properties.items():
            if "type" in definition:
                rules["field_types"][field] = definition["type"]
            
            if "pattern" in definition:
                rules["patterns"][field] = definition["pattern"]
            
            if "minimum" in definition or "maximum" in definition:
                rules["constraints"][field] = {
                    "min": definition.get("minimum"),
                    "max": definition.get("maximum")
                }
        
        return rules
    
    def create_schema_block(self, block_name: str, schema_ids: List[str],
                          validation_rules: Dict[str, Any] = None) -> SchemaBlock:
        """Create a schema validation block"""
        block_id = str(uuid.uuid4())
        
        # Validate schema IDs
        for schema_id in schema_ids:
            if schema_id not in self.event_schemas:
                raise ValueError(f"Schema not found: {schema_id}")
        
        schema_block = SchemaBlock(
            id=block_id,
            block_name=block_name,
            schema_ids=schema_ids,
            validation_rules=validation_rules or {},
            is_active=True,
            created_at=timezone.now(),
            false_positive_count=0,
            total_validations=0
        )
        
        self.schema_blocks[block_id] = schema_block
        
        logger.info(f"Schema block created: {block_name} with {len(schema_ids)} schemas")
        return schema_block
    
    def validate_event(self, event_data: Dict[str, Any], schema_id: str,
                      company: Company) -> SchemaValidationResult:
        """Validate an event against a schema"""
        start_time = timezone.now()
        
        if schema_id not in self.event_schemas:
            raise ValueError(f"Schema not found: {schema_id}")
        
        schema = self.event_schemas[schema_id]
        
        # Check if event should be sampled
        if not self._should_sample_event(event_data, schema):
            return SchemaValidationResult(
                id=str(uuid.uuid4()),
                event_id=event_data.get("id", "unknown"),
                schema_id=schema_id,
                is_valid=True,
                validation_errors=[],
                validation_time_ms=0,
                timestamp=timezone.now(),
                false_positive=False,
                confidence_score=1.0
            )
        
        # Perform validation
        validation_errors = []
        is_valid = True
        
        try:
            validate(instance=event_data, schema=schema.schema_definition)
        except ValidationError as e:
            is_valid = False
            validation_errors.append(str(e))
        except Exception as e:
            is_valid = False
            validation_errors.append(f"Validation error: {str(e)}")
        
        # Calculate validation time
        validation_time = (timezone.now() - start_time).total_seconds() * 1000
        
        # Determine if this is a false positive
        false_positive = self._detect_false_positive(event_data, schema, validation_errors)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(event_data, schema, validation_errors)
        
        # Create validation result
        result = SchemaValidationResult(
            id=str(uuid.uuid4()),
            event_id=event_data.get("id", "unknown"),
            schema_id=schema_id,
            is_valid=is_valid,
            validation_errors=validation_errors,
            validation_time_ms=validation_time,
            timestamp=timezone.now(),
            false_positive=false_positive,
            confidence_score=confidence_score
        )
        
        self.validation_results.append(result)
        
        # Update schema block statistics
        self._update_block_statistics(schema_id, result)
        
        # Publish validation event
        event_bus.publish(
            event_type='EVENT_SCHEMA_VALIDATED',
            data={
                'validation_id': result.id,
                'event_id': result.event_id,
                'schema_id': schema_id,
                'is_valid': is_valid,
                'false_positive': false_positive,
                'validation_time_ms': validation_time
            },
            company_id=company.id
        )
        
        logger.debug(f"Event validated against schema {schema_id}: {is_valid}")
        return result
    
    def _should_sample_event(self, event_data: Dict[str, Any], schema: EventSchema) -> bool:
        """Determine if event should be sampled for validation"""
        # Use event ID hash for consistent sampling
        event_id = event_data.get("id", "unknown")
        hash_value = int(hashlib.md5(event_id.encode()).hexdigest(), 16)
        sample_threshold = int(schema.sample_rate * 10000)
        
        return (hash_value % 10000) < sample_threshold
    
    def _detect_false_positive(self, event_data: Dict[str, Any], 
                             schema: EventSchema, validation_errors: List[str]) -> bool:
        """Detect if validation result is a false positive"""
        if not validation_errors:
            return False
        
        # Check for common false positive patterns
        false_positive_patterns = [
            "additional properties not allowed",
            "expected string, received null",
            "expected number, received string"
        ]
        
        for error in validation_errors:
            for pattern in false_positive_patterns:
                if pattern.lower() in error.lower():
                    return True
        
        # Check confidence score
        confidence = self._calculate_confidence_score(event_data, schema, validation_errors)
        return confidence < self.sampling_config["confidence_threshold"]
    
    def _calculate_confidence_score(self, event_data: Dict[str, Any], 
                                  schema: EventSchema, validation_errors: List[str]) -> float:
        """Calculate confidence score for validation result"""
        if not validation_errors:
            return 1.0
        
        # Base confidence on error severity
        error_weights = {
            "required": 0.9,
            "type": 0.8,
            "format": 0.7,
            "pattern": 0.6,
            "additional": 0.5
        }
        
        min_confidence = 1.0
        for error in validation_errors:
            for error_type, weight in error_weights.items():
                if error_type in error.lower():
                    min_confidence = min(min_confidence, weight)
        
        # Adjust for data quality
        data_quality_score = self._assess_data_quality(event_data)
        confidence = min_confidence * data_quality_score
        
        return max(0.0, min(1.0, confidence))
    
    def _assess_data_quality(self, event_data: Dict[str, Any]) -> float:
        """Assess data quality of event"""
        if not event_data:
            return 0.0
        
        # Check for null values
        null_count = sum(1 for v in event_data.values() if v is None)
        null_ratio = null_count / len(event_data) if event_data else 0
        
        # Check for empty strings
        empty_count = sum(1 for v in event_data.values() if v == "")
        empty_ratio = empty_count / len(event_data) if event_data else 0
        
        # Calculate quality score
        quality_score = 1.0 - (null_ratio * 0.5 + empty_ratio * 0.3)
        return max(0.0, min(1.0, quality_score))
    
    def _update_block_statistics(self, schema_id: str, result: SchemaValidationResult):
        """Update schema block statistics"""
        for block in self.schema_blocks.values():
            if schema_id in block.schema_ids:
                block.total_validations += 1
                if result.false_positive:
                    block.false_positive_count += 1
    
    def validate_event_block(self, event_data: Dict[str, Any], block_id: str,
                           company: Company) -> List[SchemaValidationResult]:
        """Validate event against all schemas in a block"""
        if block_id not in self.schema_blocks:
            raise ValueError(f"Schema block not found: {block_id}")
        
        block = self.schema_blocks[block_id]
        if not block.is_active:
            raise ValueError(f"Schema block is not active: {block_id}")
        
        results = []
        for schema_id in block.schema_ids:
            try:
                result = self.validate_event(event_data, schema_id, company)
                results.append(result)
            except Exception as e:
                logger.error(f"Validation failed for schema {schema_id}: {e}")
        
        return results
    
    def get_schema_performance_metrics(self, schema_id: str, 
                                     lookback_days: int = 7) -> Dict[str, Any]:
        """Get performance metrics for a schema"""
        if schema_id not in self.event_schemas:
            return {"error": "Schema not found"}
        
        schema = self.event_schemas[schema_id]
        cutoff_date = timezone.now() - timedelta(days=lookback_days)
        
        # Filter validation results
        schema_results = [
            result for result in self.validation_results
            if result.schema_id == schema_id and result.timestamp >= cutoff_date
        ]
        
        if not schema_results:
            return {"status": "no_data", "message": "No validation data available"}
        
        # Calculate metrics
        total_validations = len(schema_results)
        valid_count = sum(1 for r in schema_results if r.is_valid)
        false_positive_count = sum(1 for r in schema_results if r.false_positive)
        
        false_positive_rate = false_positive_count / total_validations if total_validations > 0 else 0
        validation_accuracy = valid_count / total_validations if total_validations > 0 else 0
        
        # Calculate average validation time
        avg_validation_time = np.mean([r.validation_time_ms for r in schema_results])
        
        # Calculate confidence distribution
        confidence_scores = [r.confidence_score for r in schema_results]
        avg_confidence = np.mean(confidence_scores)
        
        return {
            "schema_id": schema_id,
            "schema_name": schema.schema_name,
            "period_days": lookback_days,
            "total_validations": total_validations,
            "valid_count": valid_count,
            "false_positive_count": false_positive_count,
            "false_positive_rate": false_positive_rate,
            "validation_accuracy": validation_accuracy,
            "avg_validation_time_ms": avg_validation_time,
            "avg_confidence_score": avg_confidence,
            "target_met": false_positive_rate < schema.false_positive_threshold,
            "threshold": schema.false_positive_threshold
        }
    
    def get_block_performance_metrics(self, block_id: str, 
                                    lookback_days: int = 7) -> Dict[str, Any]:
        """Get performance metrics for a schema block"""
        if block_id not in self.schema_blocks:
            return {"error": "Block not found"}
        
        block = self.schema_blocks[block_id]
        cutoff_date = timezone.now() - timedelta(days=lookback_days)
        
        # Get all validation results for schemas in this block
        block_results = []
        for schema_id in block.schema_ids:
            schema_results = [
                result for result in self.validation_results
                if result.schema_id == schema_id and result.timestamp >= cutoff_date
            ]
            block_results.extend(schema_results)
        
        if not block_results:
            return {"status": "no_data", "message": "No validation data available"}
        
        # Calculate block-level metrics
        total_validations = len(block_results)
        false_positive_count = sum(1 for r in block_results if r.false_positive)
        false_positive_rate = false_positive_count / total_validations if total_validations > 0 else 0
        
        # Calculate per-schema metrics
        schema_metrics = {}
        for schema_id in block.schema_ids:
            schema_results = [r for r in block_results if r.schema_id == schema_id]
            if schema_results:
                schema_fp_count = sum(1 for r in schema_results if r.false_positive)
                schema_fp_rate = schema_fp_count / len(schema_results) if schema_results else 0
                schema_metrics[schema_id] = {
                    "total_validations": len(schema_results),
                    "false_positive_count": schema_fp_count,
                    "false_positive_rate": schema_fp_rate
                }
        
        return {
            "block_id": block_id,
            "block_name": block.block_name,
            "period_days": lookback_days,
            "total_validations": total_validations,
            "false_positive_count": false_positive_count,
            "false_positive_rate": false_positive_rate,
            "target_met": false_positive_rate < self.sampling_config["false_positive_threshold"],
            "threshold": self.sampling_config["false_positive_threshold"],
            "schema_metrics": schema_metrics,
            "is_active": block.is_active
        }
    
    def optimize_schema_sampling(self, schema_id: str) -> Dict[str, Any]:
        """Optimize schema sampling to reduce false positives"""
        if schema_id not in self.event_schemas:
            return {"error": "Schema not found"}
        
        schema = self.event_schemas[schema_id]
        
        # Get recent validation results
        recent_results = [
            result for result in self.validation_results
            if result.schema_id == schema_id and result.timestamp >= timezone.now() - timedelta(days=7)
        ]
        
        if not recent_results:
            return {"status": "no_data", "message": "No recent validation data"}
        
        # Analyze false positive patterns
        false_positives = [r for r in recent_results if r.false_positive]
        fp_patterns = {}
        
        for fp in false_positives:
            for error in fp.validation_errors:
                error_type = self._classify_error_type(error)
                fp_patterns[error_type] = fp_patterns.get(error_type, 0) + 1
        
        # Generate optimization recommendations
        recommendations = []
        
        if fp_patterns.get("type_mismatch", 0) > len(false_positives) * 0.5:
            recommendations.append("Consider relaxing type constraints for optional fields")
        
        if fp_patterns.get("format_validation", 0) > len(false_positives) * 0.3:
            recommendations.append("Review format patterns for common data variations")
        
        if fp_patterns.get("required_fields", 0) > len(false_positives) * 0.4:
            recommendations.append("Make some required fields optional or provide defaults")
        
        # Calculate optimized sample rate
        current_fp_rate = len(false_positives) / len(recent_results)
        if current_fp_rate > schema.false_positive_threshold:
            # Reduce sample rate to focus on higher confidence validations
            optimized_rate = min(1.0, schema.sample_rate * 0.8)
        else:
            # Can increase sample rate
            optimized_rate = min(1.0, schema.sample_rate * 1.2)
        
        return {
            "schema_id": schema_id,
            "current_false_positive_rate": current_fp_rate,
            "target_rate": schema.false_positive_threshold,
            "current_sample_rate": schema.sample_rate,
            "optimized_sample_rate": optimized_rate,
            "false_positive_patterns": fp_patterns,
            "recommendations": recommendations,
            "optimization_needed": current_fp_rate > schema.false_positive_threshold
        }
    
    def _classify_error_type(self, error_message: str) -> str:
        """Classify error type for pattern analysis"""
        error_lower = error_message.lower()
        
        if "required" in error_lower:
            return "required_fields"
        elif "type" in error_lower and ("expected" in error_lower or "received" in error_lower):
            return "type_mismatch"
        elif "format" in error_lower:
            return "format_validation"
        elif "pattern" in error_lower:
            return "pattern_validation"
        elif "additional" in error_lower:
            return "additional_properties"
        else:
            return "other"

# Global instance
event_schema_sampling = EventSchemaSampling()
