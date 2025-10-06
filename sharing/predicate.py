# sharing/predicate.py
# Predicate evaluation engine for sharing rules

from django.db.models import Q
from typing import Dict, Any, List


class PredicateEvaluator:
    """
    Evaluates JSON predicates and converts them to Django Q objects.
    
    Supported operators:
    - eq: Equal to
    - ne: Not equal to
    - in: In list
    - nin: Not in list
    - contains: String contains (case-sensitive)
    - icontains: String contains (case-insensitive)
    - gt: Greater than
    - gte: Greater than or equal to
    - lt: Less than
    - lte: Less than or equal to
    """
    
    SUPPORTED_OPERATORS = {
        'eq': '__exact',
        'ne': '__exact',  # Special handling for negation
        'in': '__in',
        'nin': '__in',  # Special handling for negation
        'contains': '__contains',
        'icontains': '__icontains',
        'gt': '__gt',
        'gte': '__gte',
        'lt': '__lt',
        'lte': '__lte',
    }
    
    @classmethod
    def evaluate(cls, predicate: Dict[str, Any]) -> Q:
        """
        Convert a predicate dictionary to a Django Q object.
        
        Args:
            predicate: Dictionary with 'field', 'operator', and 'value' keys
            
        Returns:
            Django Q object representing the predicate
            
        Raises:
            ValueError: If operator is not supported or predicate is invalid
        """
        if not isinstance(predicate, dict):
            raise ValueError("Predicate must be a dictionary")
        
        field = predicate.get('field')
        operator = predicate.get('operator')
        value = predicate.get('value')
        
        if not field:
            raise ValueError("Predicate must have a 'field' key")
        if not operator:
            raise ValueError("Predicate must have an 'operator' key")
        if value is None:
            raise ValueError("Predicate must have a 'value' key")
        
        if operator not in cls.SUPPORTED_OPERATORS:
            raise ValueError(
                f"Unsupported operator '{operator}'. "
                f"Supported operators: {', '.join(cls.SUPPORTED_OPERATORS.keys())}"
            )
        
        # Handle negation operators
        if operator == 'ne':
            lookup = f"{field}{cls.SUPPORTED_OPERATORS['eq']}"
            return ~Q(**{lookup: value})
        elif operator == 'nin':
            lookup = f"{field}{cls.SUPPORTED_OPERATORS['in']}"
            return ~Q(**{lookup: value})
        else:
            lookup = f"{field}{cls.SUPPORTED_OPERATORS[operator]}"
            return Q(**{lookup: value})
    
    @classmethod
    def evaluate_multiple(cls, predicates: List[Dict[str, Any]], combine_with_or: bool = True) -> Q:
        """
        Evaluate multiple predicates and combine them.
        
        Args:
            predicates: List of predicate dictionaries
            combine_with_or: If True, combine with OR (default). If False, combine with AND.
            
        Returns:
            Combined Django Q object
        """
        if not predicates:
            return Q()
        
        q_objects = [cls.evaluate(p) for p in predicates]
        
        if combine_with_or:
            # Combine with OR
            result = q_objects[0]
            for q in q_objects[1:]:
                result |= q
            return result
        else:
            # Combine with AND
            result = q_objects[0]
            for q in q_objects[1:]:
                result &= q
            return result
