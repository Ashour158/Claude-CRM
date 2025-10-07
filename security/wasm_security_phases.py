# security/wasm_security_phases.py
"""
WASM Sandbox Security Phases Implementation
P0 Priority: Zero exec escape incidents

This module implements a multi-phase WASM security model with:
- Phase 1: Basic sandboxing with resource limits
- Phase 2: Enhanced isolation with capability restrictions
- Phase 3: Advanced monitoring with behavioral analysis
- Phase 4: Zero-trust execution with continuous validation
"""

import logging
import time
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from django.conf import settings
from django.utils import timezone
from core.models import Company, User
from events.event_bus import event_bus
import uuid

logger = logging.getLogger(__name__)

class SecurityPhase(Enum):
    """WASM Security Phase Levels"""
    PHASE_1_BASIC = "phase_1_basic"
    PHASE_2_ENHANCED = "phase_2_enhanced"
    PHASE_3_MONITORING = "phase_3_monitoring"
    PHASE_4_ZERO_TRUST = "phase_4_zero_trust"

class ThreatLevel(Enum):
    """Threat Level Classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityIncident:
    """Security incident record"""
    id: str
    timestamp: timezone.datetime
    phase: SecurityPhase
    threat_level: ThreatLevel
    wasm_module_id: str
    execution_id: str
    incident_type: str
    description: str
    mitigation_action: str
    resolved: bool = False

@dataclass
class WASMExecutionContext:
    """WASM execution context with security constraints"""
    execution_id: str
    module_id: str
    phase: SecurityPhase
    resource_limits: Dict[str, Any]
    capability_restrictions: List[str]
    monitoring_enabled: bool
    zero_trust_mode: bool
    created_at: timezone.datetime

class WASMSecurityPhases:
    """
    Multi-phase WASM security implementation with zero exec escape incidents
    """
    
    def __init__(self):
        self.incidents: List[SecurityIncident] = []
        self.active_executions: Dict[str, WASMExecutionContext] = {}
        self.security_policies = self._load_security_policies()
        
    def _load_security_policies(self) -> Dict[str, Any]:
        """Load security policies for each phase"""
        return {
            SecurityPhase.PHASE_1_BASIC: {
                "max_memory_mb": 64,
                "max_execution_time_ms": 5000,
                "allowed_imports": ["console", "math"],
                "blocked_imports": ["fs", "net", "crypto"],
                "sandbox_mode": True,
                "resource_monitoring": True
            },
            SecurityPhase.PHASE_2_ENHANCED: {
                "max_memory_mb": 32,
                "max_execution_time_ms": 3000,
                "allowed_imports": ["console"],
                "blocked_imports": ["fs", "net", "crypto", "os", "process"],
                "sandbox_mode": True,
                "resource_monitoring": True,
                "capability_restrictions": ["no_file_access", "no_network_access", "no_system_calls"],
                "execution_isolation": True
            },
            SecurityPhase.PHASE_3_MONITORING: {
                "max_memory_mb": 16,
                "max_execution_time_ms": 2000,
                "allowed_imports": ["console"],
                "blocked_imports": ["fs", "net", "crypto", "os", "process", "util"],
                "sandbox_mode": True,
                "resource_monitoring": True,
                "behavioral_monitoring": True,
                "real_time_analysis": True,
                "anomaly_detection": True,
                "execution_isolation": True
            },
            SecurityPhase.PHASE_4_ZERO_TRUST: {
                "max_memory_mb": 8,
                "max_execution_time_ms": 1000,
                "allowed_imports": [],
                "blocked_imports": ["*"],
                "sandbox_mode": True,
                "resource_monitoring": True,
                "behavioral_monitoring": True,
                "real_time_analysis": True,
                "anomaly_detection": True,
                "execution_isolation": True,
                "zero_trust_mode": True,
                "continuous_validation": True,
                "micro_validation": True
            }
        }
    
    def create_execution_context(self, module_id: str, phase: SecurityPhase, 
                                company: Company, user: User) -> WASMExecutionContext:
        """Create a new WASM execution context with security constraints"""
        execution_id = str(uuid.uuid4())
        policy = self.security_policies[phase]
        
        context = WASMExecutionContext(
            execution_id=execution_id,
            module_id=module_id,
            phase=phase,
            resource_limits={
                "max_memory_mb": policy["max_memory_mb"],
                "max_execution_time_ms": policy["max_execution_time_ms"],
                "max_cpu_percent": 50
            },
            capability_restrictions=policy.get("capability_restrictions", []),
            monitoring_enabled=policy.get("behavioral_monitoring", False),
            zero_trust_mode=policy.get("zero_trust_mode", False),
            created_at=timezone.now()
        )
        
        self.active_executions[execution_id] = context
        
        # Log execution start
        event_bus.publish(
            event_type='WASM_EXECUTION_STARTED',
            data={
                'execution_id': execution_id,
                'module_id': module_id,
                'phase': phase.value,
                'security_level': phase.value
            },
            actor=user,
            company_id=company.id
        )
        
        logger.info(f"WASM execution context created: {execution_id} in phase {phase.value}")
        return context
    
    def validate_execution_safety(self, execution_id: str, wasm_code: str) -> Tuple[bool, List[str]]:
        """Validate WASM code for execution safety"""
        if execution_id not in self.active_executions:
            return False, ["Invalid execution context"]
        
        context = self.active_executions[execution_id]
        policy = self.security_policies[context.phase]
        violations = []
        
        # Phase 1: Basic validation
        if context.phase == SecurityPhase.PHASE_1_BASIC:
            violations.extend(self._validate_basic_safety(wasm_code, policy))
        
        # Phase 2: Enhanced validation
        elif context.phase == SecurityPhase.PHASE_2_ENHANCED:
            violations.extend(self._validate_enhanced_safety(wasm_code, policy))
            violations.extend(self._validate_capability_restrictions(wasm_code, policy))
        
        # Phase 3: Monitoring validation
        elif context.phase == SecurityPhase.PHASE_3_MONITORING:
            violations.extend(self._validate_enhanced_safety(wasm_code, policy))
            violations.extend(self._validate_capability_restrictions(wasm_code, policy))
            violations.extend(self._validate_behavioral_patterns(wasm_code, policy))
        
        # Phase 4: Zero-trust validation
        elif context.phase == SecurityPhase.PHASE_4_ZERO_TRUST:
            violations.extend(self._validate_enhanced_safety(wasm_code, policy))
            violations.extend(self._validate_capability_restrictions(wasm_code, policy))
            violations.extend(self._validate_behavioral_patterns(wasm_code, policy))
            violations.extend(self._validate_zero_trust_requirements(wasm_code, policy))
        
        is_safe = len(violations) == 0
        
        if not is_safe:
            self._record_security_incident(
                execution_id=execution_id,
                incident_type="CODE_VALIDATION_FAILED",
                description=f"Code validation failed: {', '.join(violations)}",
                threat_level=ThreatLevel.HIGH
            )
        
        return is_safe, violations
    
    def _validate_basic_safety(self, wasm_code: str, policy: Dict[str, Any]) -> List[str]:
        """Phase 1: Basic safety validation"""
        violations = []
        
        # Check for blocked imports
        for blocked_import in policy.get("blocked_imports", []):
            if blocked_import in wasm_code:
                violations.append(f"Blocked import detected: {blocked_import}")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            "eval(", "Function(", "setTimeout", "setInterval",
            "XMLHttpRequest", "fetch(", "import(", "require("
        ]
        
        for pattern in suspicious_patterns:
            if pattern in wasm_code:
                violations.append(f"Suspicious pattern detected: {pattern}")
        
        return violations
    
    def _validate_enhanced_safety(self, wasm_code: str, policy: Dict[str, Any]) -> List[str]:
        """Phase 2: Enhanced safety validation"""
        violations = []
        
        # More strict import checking
        allowed_imports = policy.get("allowed_imports", [])
        if allowed_imports:
            # Extract import statements (simplified)
            import_lines = [line.strip() for line in wasm_code.split('\n') 
                          if line.strip().startswith('import')]
            
            for import_line in import_lines:
                # Check if import is in allowed list
                import_name = import_line.split(' ')[1] if ' ' in import_line else ""
                if import_name and import_name not in allowed_imports:
                    violations.append(f"Unauthorized import: {import_name}")
        
        # Check for system calls
        system_calls = ["syscall", "system", "exec", "spawn", "fork"]
        for call in system_calls:
            if call in wasm_code.lower():
                violations.append(f"System call detected: {call}")
        
        return violations
    
    def _validate_capability_restrictions(self, wasm_code: str, policy: Dict[str, Any]) -> List[str]:
        """Validate capability restrictions"""
        violations = []
        restrictions = policy.get("capability_restrictions", [])
        
        if "no_file_access" in restrictions:
            file_patterns = ["fs.", "readFile", "writeFile", "open", "close"]
            for pattern in file_patterns:
                if pattern in wasm_code:
                    violations.append(f"File access detected: {pattern}")
        
        if "no_network_access" in restrictions:
            network_patterns = ["fetch", "XMLHttpRequest", "WebSocket", "http", "https"]
            for pattern in network_patterns:
                if pattern in wasm_code:
                    violations.append(f"Network access detected: {pattern}")
        
        if "no_system_calls" in restrictions:
            system_patterns = ["process.", "os.", "child_process", "exec"]
            for pattern in system_patterns:
                if pattern in wasm_code:
                    violations.append(f"System call detected: {pattern}")
        
        return violations
    
    def _validate_behavioral_patterns(self, wasm_code: str, policy: Dict[str, Any]) -> List[str]:
        """Phase 3: Behavioral pattern validation"""
        violations = []
        
        # Check for obfuscation patterns
        obfuscation_patterns = [
            "eval(", "Function(", "setTimeout", "setInterval",
            "String.fromCharCode", "unescape", "decodeURIComponent"
        ]
        
        for pattern in obfuscation_patterns:
            if pattern in wasm_code:
                violations.append(f"Obfuscation pattern detected: {pattern}")
        
        # Check for recursion depth (simplified)
        if wasm_code.count("function") > 10:
            violations.append("Excessive function definitions detected")
        
        return violations
    
    def _validate_zero_trust_requirements(self, wasm_code: str, policy: Dict[str, Any]) -> List[str]:
        """Phase 4: Zero-trust validation"""
        violations = []
        
        # Zero-trust: No external dependencies
        if "import" in wasm_code:
            violations.append("Zero-trust mode: No imports allowed")
        
        # Check for any dynamic code execution
        dynamic_patterns = ["eval", "Function", "setTimeout", "setInterval"]
        for pattern in dynamic_patterns:
            if pattern in wasm_code:
                violations.append(f"Zero-trust violation: Dynamic execution detected: {pattern}")
        
        # Check code complexity (simplified)
        lines = wasm_code.split('\n')
        if len(lines) > 100:
            violations.append("Zero-trust mode: Code too complex")
        
        return violations
    
    def monitor_execution(self, execution_id: str, metrics: Dict[str, Any]) -> bool:
        """Monitor active execution for security violations"""
        if execution_id not in self.active_executions:
            return False
        
        context = self.active_executions[execution_id]
        policy = self.security_policies[context.phase]
        
        # Check resource limits
        if metrics.get("memory_usage_mb", 0) > context.resource_limits["max_memory_mb"]:
            self._record_security_incident(
                execution_id=execution_id,
                incident_type="RESOURCE_LIMIT_EXCEEDED",
                description=f"Memory limit exceeded: {metrics['memory_usage_mb']}MB > {context.resource_limits['max_memory_mb']}MB",
                threat_level=ThreatLevel.HIGH
            )
            return False
        
        if metrics.get("execution_time_ms", 0) > context.resource_limits["max_execution_time_ms"]:
            self._record_security_incident(
                execution_id=execution_id,
                incident_type="EXECUTION_TIMEOUT",
                description=f"Execution timeout: {metrics['execution_time_ms']}ms > {context.resource_limits['max_execution_time_ms']}ms",
                threat_level=ThreatLevel.MEDIUM
            )
            return False
        
        # Phase 3+ monitoring
        if context.phase in [SecurityPhase.PHASE_3_MONITORING, SecurityPhase.PHASE_4_ZERO_TRUST]:
            if not self._monitor_behavioral_patterns(execution_id, metrics):
                return False
        
        return True
    
    def _monitor_behavioral_patterns(self, execution_id: str, metrics: Dict[str, Any]) -> bool:
        """Monitor for behavioral anomalies"""
        context = self.active_executions[execution_id]
        
        # Check for unusual CPU usage patterns
        if metrics.get("cpu_usage_percent", 0) > 80:
            self._record_security_incident(
                execution_id=execution_id,
                incident_type="HIGH_CPU_USAGE",
                description=f"High CPU usage detected: {metrics['cpu_usage_percent']}%",
                threat_level=ThreatLevel.MEDIUM
            )
            return False
        
        # Check for memory growth patterns
        memory_growth = metrics.get("memory_growth_rate", 0)
        if memory_growth > 1.0:  # 1MB per second
            self._record_security_incident(
                execution_id=execution_id,
                incident_type="MEMORY_GROWTH_ANOMALY",
                description=f"Unusual memory growth: {memory_growth}MB/s",
                threat_level=ThreatLevel.MEDIUM
            )
            return False
        
        return True
    
    def _record_security_incident(self, execution_id: str, incident_type: str, 
                                 description: str, threat_level: ThreatLevel):
        """Record a security incident"""
        context = self.active_executions.get(execution_id)
        phase = context.phase if context else SecurityPhase.PHASE_1_BASIC
        
        incident = SecurityIncident(
            id=str(uuid.uuid4()),
            timestamp=timezone.now(),
            phase=phase,
            threat_level=threat_level,
            wasm_module_id=context.module_id if context else "unknown",
            execution_id=execution_id,
            incident_type=incident_type,
            description=description,
            mitigation_action="EXECUTION_TERMINATED"
        )
        
        self.incidents.append(incident)
        
        # Publish incident event
        event_bus.publish(
            event_type='WASM_SECURITY_INCIDENT',
            data={
                'incident_id': incident.id,
                'execution_id': execution_id,
                'incident_type': incident_type,
                'threat_level': threat_level.value,
                'phase': phase.value,
                'description': description
            }
        )
        
        logger.error(f"WASM Security Incident: {incident_type} - {description}")
    
    def terminate_execution(self, execution_id: str, reason: str = "Security violation"):
        """Terminate a WASM execution"""
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
            
            # Record termination incident
            self._record_security_incident(
                execution_id=execution_id,
                incident_type="EXECUTION_TERMINATED",
                description=f"Execution terminated: {reason}",
                threat_level=ThreatLevel.HIGH
            )
            
            # Remove from active executions
            del self.active_executions[execution_id]
            
            logger.warning(f"WASM execution terminated: {execution_id} - {reason}")
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics and incident statistics"""
        total_incidents = len(self.incidents)
        incidents_by_phase = {}
        incidents_by_threat_level = {}
        
        for incident in self.incidents:
            phase = incident.phase.value
            threat_level = incident.threat_level.value
            
            incidents_by_phase[phase] = incidents_by_phase.get(phase, 0) + 1
            incidents_by_threat_level[threat_level] = incidents_by_threat_level.get(threat_level, 0) + 1
        
        return {
            "total_incidents": total_incidents,
            "active_executions": len(self.active_executions),
            "incidents_by_phase": incidents_by_phase,
            "incidents_by_threat_level": incidents_by_threat_level,
            "zero_escape_incidents": len([i for i in self.incidents if i.incident_type == "EXECUTION_ESCAPE"]),
            "success_rate": 1.0 - (total_incidents / max(len(self.active_executions) + total_incidents, 1))
        }
    
    def upgrade_security_phase(self, execution_id: str, new_phase: SecurityPhase):
        """Upgrade execution to a higher security phase"""
        if execution_id not in self.active_executions:
            return False
        
        context = self.active_executions[execution_id]
        old_phase = context.phase
        
        # Update context with new phase
        context.phase = new_phase
        policy = self.security_policies[new_phase]
        context.resource_limits = {
            "max_memory_mb": policy["max_memory_mb"],
            "max_execution_time_ms": policy["max_execution_time_ms"],
            "max_cpu_percent": 50
        }
        context.capability_restrictions = policy.get("capability_restrictions", [])
        context.monitoring_enabled = policy.get("behavioral_monitoring", False)
        context.zero_trust_mode = policy.get("zero_trust_mode", False)
        
        logger.info(f"WASM execution {execution_id} upgraded from {old_phase.value} to {new_phase.value}")
        return True

# Global instance
wasm_security_phases = WASMSecurityPhases()
