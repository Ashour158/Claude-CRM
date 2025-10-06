# tests/sharing/test_predicate.py
# Tests for predicate evaluation engine

import pytest
from django.db.models import Q
from sharing.predicate import PredicateEvaluator


class TestPredicateEvaluator:
    """Test the predicate evaluation engine"""
    
    def test_eq_operator(self):
        """Test equality operator"""
        predicate = {'field': 'status', 'operator': 'eq', 'value': 'qualified'}
        q = PredicateEvaluator.evaluate(predicate)
        assert isinstance(q, Q)
        assert str(q) == "(AND: ('status__exact', 'qualified'))"
    
    def test_ne_operator(self):
        """Test not equal operator"""
        predicate = {'field': 'status', 'operator': 'ne', 'value': 'new'}
        q = PredicateEvaluator.evaluate(predicate)
        assert isinstance(q, Q)
        # Negation should be wrapped
        assert q.negated
    
    def test_in_operator(self):
        """Test in operator"""
        predicate = {'field': 'status', 'operator': 'in', 'value': ['qualified', 'converted']}
        q = PredicateEvaluator.evaluate(predicate)
        assert isinstance(q, Q)
        assert str(q) == "(AND: ('status__in', ['qualified', 'converted']))"
    
    def test_nin_operator(self):
        """Test not in operator"""
        predicate = {'field': 'status', 'operator': 'nin', 'value': ['new', 'contacted']}
        q = PredicateEvaluator.evaluate(predicate)
        assert isinstance(q, Q)
        assert q.negated
    
    def test_contains_operator(self):
        """Test contains operator"""
        predicate = {'field': 'name', 'operator': 'contains', 'value': 'test'}
        q = PredicateEvaluator.evaluate(predicate)
        assert isinstance(q, Q)
        assert str(q) == "(AND: ('name__contains', 'test'))"
    
    def test_icontains_operator(self):
        """Test case-insensitive contains operator"""
        predicate = {'field': 'name', 'operator': 'icontains', 'value': 'TEST'}
        q = PredicateEvaluator.evaluate(predicate)
        assert isinstance(q, Q)
        assert str(q) == "(AND: ('name__icontains', 'TEST'))"
    
    def test_gt_operator(self):
        """Test greater than operator"""
        predicate = {'field': 'amount', 'operator': 'gt', 'value': 1000}
        q = PredicateEvaluator.evaluate(predicate)
        assert isinstance(q, Q)
        assert str(q) == "(AND: ('amount__gt', 1000))"
    
    def test_gte_operator(self):
        """Test greater than or equal operator"""
        predicate = {'field': 'amount', 'operator': 'gte', 'value': 1000}
        q = PredicateEvaluator.evaluate(predicate)
        assert isinstance(q, Q)
        assert str(q) == "(AND: ('amount__gte', 1000))"
    
    def test_lt_operator(self):
        """Test less than operator"""
        predicate = {'field': 'amount', 'operator': 'lt', 'value': 5000}
        q = PredicateEvaluator.evaluate(predicate)
        assert isinstance(q, Q)
        assert str(q) == "(AND: ('amount__lt', 5000))"
    
    def test_lte_operator(self):
        """Test less than or equal operator"""
        predicate = {'field': 'amount', 'operator': 'lte', 'value': 5000}
        q = PredicateEvaluator.evaluate(predicate)
        assert isinstance(q, Q)
        assert str(q) == "(AND: ('amount__lte', 5000))"
    
    def test_invalid_predicate_not_dict(self):
        """Test validation for non-dict predicate"""
        with pytest.raises(ValueError, match="Predicate must be a dictionary"):
            PredicateEvaluator.evaluate("invalid")
    
    def test_invalid_predicate_missing_field(self):
        """Test validation for missing field"""
        with pytest.raises(ValueError, match="Predicate must have 'field' key"):
            PredicateEvaluator.evaluate({'operator': 'eq', 'value': 'test'})
    
    def test_invalid_predicate_missing_operator(self):
        """Test validation for missing operator"""
        with pytest.raises(ValueError, match="Predicate must have 'operator' key"):
            PredicateEvaluator.evaluate({'field': 'status', 'value': 'test'})
    
    def test_invalid_predicate_missing_value(self):
        """Test validation for missing value"""
        with pytest.raises(ValueError, match="Predicate must have 'value' key"):
            PredicateEvaluator.evaluate({'field': 'status', 'operator': 'eq'})
    
    def test_unsupported_operator(self):
        """Test validation for unsupported operator"""
        with pytest.raises(ValueError, match="Unsupported operator"):
            PredicateEvaluator.evaluate({
                'field': 'status',
                'operator': 'invalid_op',
                'value': 'test'
            })
    
    def test_evaluate_multiple_or(self):
        """Test evaluating multiple predicates with OR"""
        predicates = [
            {'field': 'status', 'operator': 'eq', 'value': 'qualified'},
            {'field': 'status', 'operator': 'eq', 'value': 'converted'},
        ]
        q = PredicateEvaluator.evaluate_multiple(predicates, combine_with_or=True)
        assert isinstance(q, Q)
    
    def test_evaluate_multiple_and(self):
        """Test evaluating multiple predicates with AND"""
        predicates = [
            {'field': 'status', 'operator': 'eq', 'value': 'qualified'},
            {'field': 'rating', 'operator': 'eq', 'value': 'hot'},
        ]
        q = PredicateEvaluator.evaluate_multiple(predicates, combine_with_or=False)
        assert isinstance(q, Q)
    
    def test_evaluate_multiple_empty(self):
        """Test evaluating empty predicates list"""
        q = PredicateEvaluator.evaluate_multiple([])
        assert isinstance(q, Q)
        # Empty Q should match everything
        assert str(q) == "(AND: )"
