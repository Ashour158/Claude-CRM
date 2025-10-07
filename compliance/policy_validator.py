# compliance/policy_validator.py
# Policy configuration validator

import yaml
import json
from typing import Dict, List, Tuple


class PolicyValidator:
    """Validator for policy-as-code configurations"""
    
    VALID_POLICY_KEYS = [
        'name', 'version', 'rules', 'enforcement', 'scope',
        'data_residency', 'retention', 'encryption', 'access_control'
    ]
    
    VALID_RULE_KEYS = [
        'id', 'name', 'type', 'condition', 'action', 'severity'
    ]
    
    def validate(self, policy_config: Dict) -> Tuple[bool, List[str]]:
        """
        Validate policy configuration
        
        Args:
            policy_config: Policy configuration dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required keys
        if 'name' not in policy_config:
            errors.append("Policy must have a 'name' field")
        
        if 'version' not in policy_config:
            errors.append("Policy must have a 'version' field")
        
        if 'rules' not in policy_config:
            errors.append("Policy must have a 'rules' field")
        
        # Validate rules
        if 'rules' in policy_config:
            rules_errors = self._validate_rules(policy_config['rules'])
            errors.extend(rules_errors)
        
        # Validate enforcement settings
        if 'enforcement' in policy_config:
            enforcement_errors = self._validate_enforcement(policy_config['enforcement'])
            errors.extend(enforcement_errors)
        
        # Validate data residency rules
        if 'data_residency' in policy_config:
            residency_errors = self._validate_data_residency(policy_config['data_residency'])
            errors.extend(residency_errors)
        
        # Validate retention rules
        if 'retention' in policy_config:
            retention_errors = self._validate_retention(policy_config['retention'])
            errors.extend(retention_errors)
        
        return len(errors) == 0, errors
    
    def _validate_rules(self, rules: List[Dict]) -> List[str]:
        """Validate policy rules"""
        errors = []
        
        if not isinstance(rules, list):
            errors.append("Rules must be a list")
            return errors
        
        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                errors.append(f"Rule {idx} must be a dictionary")
                continue
            
            # Check required fields
            if 'id' not in rule:
                errors.append(f"Rule {idx} must have an 'id' field")
            
            if 'type' not in rule:
                errors.append(f"Rule {idx} must have a 'type' field")
            
            if 'action' not in rule:
                errors.append(f"Rule {idx} must have an 'action' field")
        
        return errors
    
    def _validate_enforcement(self, enforcement: Dict) -> List[str]:
        """Validate enforcement settings"""
        errors = []
        
        if not isinstance(enforcement, dict):
            errors.append("Enforcement must be a dictionary")
            return errors
        
        valid_levels = ['soft', 'hard']
        if 'level' in enforcement and enforcement['level'] not in valid_levels:
            errors.append(f"Enforcement level must be one of: {', '.join(valid_levels)}")
        
        return errors
    
    def _validate_data_residency(self, residency: Dict) -> List[str]:
        """Validate data residency rules"""
        errors = []
        
        if not isinstance(residency, dict):
            errors.append("Data residency must be a dictionary")
            return errors
        
        if 'regions' in residency:
            if not isinstance(residency['regions'], list):
                errors.append("Data residency regions must be a list")
        
        return errors
    
    def _validate_retention(self, retention: Dict) -> List[str]:
        """Validate retention rules"""
        errors = []
        
        if not isinstance(retention, dict):
            errors.append("Retention must be a dictionary")
            return errors
        
        if 'policies' in retention:
            if not isinstance(retention['policies'], list):
                errors.append("Retention policies must be a list")
                return errors
            
            for idx, policy in enumerate(retention['policies']):
                if 'entity_type' not in policy:
                    errors.append(f"Retention policy {idx} must have 'entity_type'")
                
                if 'retention_days' not in policy:
                    errors.append(f"Retention policy {idx} must have 'retention_days'")
                elif not isinstance(policy['retention_days'], int) or policy['retention_days'] < 0:
                    errors.append(f"Retention policy {idx} retention_days must be a positive integer")
        
        return errors
    
    @staticmethod
    def parse_yaml(yaml_content: str) -> Tuple[Dict, str]:
        """
        Parse YAML policy content
        
        Args:
            yaml_content: YAML string content
            
        Returns:
            Tuple of (parsed_dict, error_message)
        """
        try:
            policy_dict = yaml.safe_load(yaml_content)
            return policy_dict, None
        except yaml.YAMLError as e:
            return None, f"YAML parsing error: {str(e)}"
    
    @staticmethod
    def to_yaml(policy_config: Dict) -> str:
        """
        Convert policy configuration to YAML
        
        Args:
            policy_config: Policy configuration dictionary
            
        Returns:
            YAML string
        """
        return yaml.dump(policy_config, default_flow_style=False, sort_keys=False)
