# analytics/hybrid_search_fusion.py
"""
Hybrid Search Fusion Implementation
P1 Priority: CTR/relevance +10%

This module implements:
- BM25 + Vector fusion for hybrid ranking
- A/B testing framework for search optimization
- Relevance scoring and CTR tracking
- Search performance analytics
- Multi-modal search capabilities
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from core.models import Company, User
from events.event_bus import event_bus
import uuid
import json
from collections import defaultdict
import math

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Search result with hybrid scoring"""
    id: str
    content: str
    bm25_score: float
    vector_score: float
    hybrid_score: float
    relevance_score: float
    rank: int
    result_type: str
    metadata: Dict[str, Any]

@dataclass
class SearchQuery:
    """Search query with tracking"""
    id: str
    query_text: str
    user_id: str
    company_id: str
    timestamp: timezone.datetime
    filters: Dict[str, Any]
    search_type: str
    results_count: int
    clicked_results: List[str]
    session_id: str

@dataclass
class ABTestConfig:
    """A/B test configuration for search"""
    test_id: str
    name: str
    description: str
    variants: Dict[str, Dict[str, Any]]
    traffic_split: Dict[str, float]
    start_date: timezone.datetime
    end_date: timezone.datetime
    success_metrics: List[str]
    is_active: bool

class HybridSearchFusion:
    """
    Hybrid search fusion with BM25 + Vector ranking
    """
    
    def __init__(self):
        self.search_queries: List[SearchQuery] = []
        self.search_results: List[SearchResult] = []
        self.ab_tests: Dict[str, ABTestConfig] = {}
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Search configuration
        self.fusion_weights = {
            "bm25_weight": 0.4,
            "vector_weight": 0.6,
            "relevance_boost": 1.2,
            "recency_boost": 1.1
        }
        
        # Performance targets
        self.performance_targets = {
            "ctr_improvement": 0.10,  # 10% CTR improvement
            "relevance_threshold": 0.8,
            "response_time_ms": 200
        }
    
    def create_ab_test(self, name: str, description: str, 
                      variants: Dict[str, Dict[str, Any]],
                      traffic_split: Dict[str, float],
                      duration_days: int = 14) -> ABTestConfig:
        """Create A/B test for search optimization"""
        test_id = str(uuid.uuid4())
        
        # Validate traffic split
        if abs(sum(traffic_split.values()) - 1.0) > 0.01:
            raise ValueError("Traffic split must sum to 1.0")
        
        ab_test = ABTestConfig(
            test_id=test_id,
            name=name,
            description=description,
            variants=variants,
            traffic_split=traffic_split,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=duration_days),
            success_metrics=["ctr", "relevance", "response_time"],
            is_active=True
        )
        
        self.ab_tests[test_id] = ab_test
        
        logger.info(f"A/B test created: {name} ({test_id})")
        return ab_test
    
    def search(self, query_text: str, user: User, company: Company,
               filters: Dict[str, Any] = None, search_type: str = "hybrid",
               session_id: str = None) -> Tuple[List[SearchResult], SearchQuery]:
        """Perform hybrid search with fusion ranking"""
        start_time = timezone.now()
        
        # Create search query record
        search_query = SearchQuery(
            id=str(uuid.uuid4()),
            query_text=query_text,
            user_id=str(user.id),
            company_id=str(company.id),
            timestamp=start_time,
            filters=filters or {},
            search_type=search_type,
            results_count=0,
            clicked_results=[],
            session_id=session_id or str(uuid.uuid4())
        )
        
        # Determine search variant for A/B testing
        variant = self._get_ab_test_variant(search_query)
        
        # Perform search based on variant
        if variant == "control":
            results = self._perform_control_search(query_text, filters)
        elif variant == "hybrid_fusion":
            results = self._perform_hybrid_fusion_search(query_text, filters)
        elif variant == "vector_boosted":
            results = self._perform_vector_boosted_search(query_text, filters)
        else:
            results = self._perform_hybrid_fusion_search(query_text, filters)
        
        # Apply fusion ranking
        ranked_results = self._apply_fusion_ranking(results, query_text, variant)
        
        # Update search query with results
        search_query.results_count = len(ranked_results)
        self.search_queries.append(search_query)
        
        # Track performance metrics
        self._track_search_performance(search_query, ranked_results, start_time)
        
        # Publish search event
        event_bus.publish(
            event_type='SEARCH_PERFORMED',
            data={
                'query_id': search_query.id,
                'query_text': query_text,
                'results_count': len(ranked_results),
                'search_type': search_type,
                'variant': variant,
                'response_time_ms': (timezone.now() - start_time).total_seconds() * 1000
            },
            actor=user,
            company_id=company.id
        )
        
        logger.info(f"Search performed: {query_text} -> {len(ranked_results)} results")
        return ranked_results, search_query
    
    def _get_ab_test_variant(self, search_query: SearchQuery) -> str:
        """Get A/B test variant for search query"""
        # Check for active A/B tests
        active_tests = [
            test for test in self.ab_tests.values()
            if test.is_active and test.start_date <= search_query.timestamp <= test.end_date
        ]
        
        if not active_tests:
            return "control"
        
        # Use the most recent test
        test = active_tests[-1]
        
        # Determine variant based on traffic split
        user_hash = hash(search_query.user_id + search_query.query_text) % 100
        cumulative_split = 0
        
        for variant, split in test.traffic_split.items():
            cumulative_split += split * 100
            if user_hash < cumulative_split:
                return variant
        
        return "control"
    
    def _perform_control_search(self, query_text: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform control search (BM25 only)"""
        # Mock search results - in real implementation, this would query the search index
        mock_results = [
            {
                "id": f"result_{i}",
                "content": f"Search result {i} for query: {query_text}",
                "bm25_score": np.random.uniform(0.1, 0.9),
                "vector_score": 0.0,  # No vector scoring in control
                "result_type": "document",
                "metadata": {"source": "control_search"}
            }
            for i in range(10)
        ]
        return mock_results
    
    def _perform_hybrid_fusion_search(self, query_text: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform hybrid fusion search (BM25 + Vector)"""
        # Mock search results with both BM25 and vector scores
        mock_results = [
            {
                "id": f"result_{i}",
                "content": f"Search result {i} for query: {query_text}",
                "bm25_score": np.random.uniform(0.1, 0.9),
                "vector_score": np.random.uniform(0.1, 0.9),
                "result_type": "document",
                "metadata": {"source": "hybrid_fusion"}
            }
            for i in range(15)  # More results with hybrid search
        ]
        return mock_results
    
    def _perform_vector_boosted_search(self, query_text: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform vector-boosted search"""
        # Mock search results with higher vector scores
        mock_results = [
            {
                "id": f"result_{i}",
                "content": f"Search result {i} for query: {query_text}",
                "bm25_score": np.random.uniform(0.1, 0.7),
                "vector_score": np.random.uniform(0.3, 0.95),  # Higher vector scores
                "result_type": "document",
                "metadata": {"source": "vector_boosted"}
            }
            for i in range(12)
        ]
        return mock_results
    
    def _apply_fusion_ranking(self, results: List[Dict[str, Any]], 
                             query_text: str, variant: str) -> List[SearchResult]:
        """Apply fusion ranking to search results"""
        ranked_results = []
        
        for i, result in enumerate(results):
            # Calculate hybrid score
            bm25_score = result.get("bm25_score", 0)
            vector_score = result.get("vector_score", 0)
            
            # Apply fusion weights based on variant
            if variant == "control":
                hybrid_score = bm25_score
            elif variant == "vector_boosted":
                hybrid_score = (0.3 * bm25_score + 0.7 * vector_score)
            else:  # hybrid_fusion
                hybrid_score = (self.fusion_weights["bm25_weight"] * bm25_score + 
                              self.fusion_weights["vector_weight"] * vector_score)
            
            # Apply relevance boost
            relevance_score = self._calculate_relevance_score(result["content"], query_text)
            boosted_score = hybrid_score * self.fusion_weights["relevance_boost"] * relevance_score
            
            # Apply recency boost if applicable
            if "created_at" in result.get("metadata", {}):
                recency_boost = self._calculate_recency_boost(result["metadata"]["created_at"])
                boosted_score *= recency_boost
            
            # Create search result
            search_result = SearchResult(
                id=result["id"],
                content=result["content"],
                bm25_score=bm25_score,
                vector_score=vector_score,
                hybrid_score=hybrid_score,
                relevance_score=relevance_score,
                rank=i + 1,
                result_type=result.get("result_type", "document"),
                metadata=result.get("metadata", {})
            )
            
            ranked_results.append(search_result)
        
        # Sort by boosted score
        ranked_results.sort(key=lambda x: x.hybrid_score, reverse=True)
        
        # Update ranks
        for i, result in enumerate(ranked_results):
            result.rank = i + 1
        
        return ranked_results
    
    def _calculate_relevance_score(self, content: str, query_text: str) -> float:
        """Calculate relevance score between content and query"""
        # Simple relevance calculation - in real implementation, this would be more sophisticated
        query_words = query_text.lower().split()
        content_words = content.lower().split()
        
        if not query_words:
            return 0.0
        
        # Calculate word overlap
        overlap = sum(1 for word in query_words if word in content_words)
        relevance = overlap / len(query_words)
        
        # Apply length normalization
        length_factor = min(1.0, len(content) / 1000)  # Normalize by content length
        
        return relevance * length_factor
    
    def _calculate_recency_boost(self, created_at: str) -> float:
        """Calculate recency boost for content"""
        try:
            if isinstance(created_at, str):
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_date = created_at
            
            days_old = (timezone.now() - created_date).days
            recency_boost = max(0.5, 1.0 - (days_old / 365))  # Decay over a year
            
            return recency_boost
        except:
            return 1.0  # No boost if date parsing fails
    
    def _track_search_performance(self, search_query: SearchQuery, 
                                results: List[SearchResult], start_time: timezone.datetime):
        """Track search performance metrics"""
        response_time = (timezone.now() - start_time).total_seconds() * 1000
        
        # Update performance metrics
        if search_query.user_id not in self.performance_metrics:
            self.performance_metrics[search_query.user_id] = {
                "total_searches": 0,
                "total_clicks": 0,
                "average_ctr": 0.0,
                "average_relevance": 0.0,
                "average_response_time": 0.0
            }
        
        metrics = self.performance_metrics[search_query.user_id]
        metrics["total_searches"] += 1
        
        # Calculate average relevance
        if results:
            avg_relevance = np.mean([r.relevance_score for r in results])
            metrics["average_relevance"] = (metrics["average_relevance"] * (metrics["total_searches"] - 1) + avg_relevance) / metrics["total_searches"]
        
        # Update average response time
        metrics["average_response_time"] = (metrics["average_response_time"] * (metrics["total_searches"] - 1) + response_time) / metrics["total_searches"]
    
    def record_click(self, search_query_id: str, result_id: str, user: User):
        """Record click on search result"""
        # Find the search query
        search_query = next((q for q in self.search_queries if q.id == search_query_id), None)
        if not search_query:
            logger.warning(f"Search query not found: {search_query_id}")
            return
        
        # Add to clicked results
        if result_id not in search_query.clicked_results:
            search_query.clicked_results.append(result_id)
        
        # Update performance metrics
        if search_query.user_id in self.performance_metrics:
            metrics = self.performance_metrics[search_query.user_id]
            metrics["total_clicks"] += 1
            metrics["average_ctr"] = metrics["total_clicks"] / metrics["total_searches"]
        
        # Publish click event
        event_bus.publish(
            event_type='SEARCH_RESULT_CLICKED',
            data={
                'query_id': search_query_id,
                'result_id': result_id,
                'user_id': str(user.id),
                'timestamp': timezone.now().isoformat()
            },
            actor=user,
            company_id=user.company.id
        )
        
        logger.info(f"Search result clicked: {result_id} for query {search_query_id}")
    
    def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test results"""
        if test_id not in self.ab_tests:
            return {"error": "Test not found"}
        
        test = self.ab_tests[test_id]
        
        # Get queries for this test
        test_queries = [
            q for q in self.search_queries
            if test.start_date <= q.timestamp <= test.end_date
        ]
        
        # Group by variant
        variant_metrics = {}
        for variant in test.traffic_split.keys():
            variant_queries = [q for q in test_queries if self._get_ab_test_variant(q) == variant]
            
            if variant_queries:
                total_searches = len(variant_queries)
                total_clicks = sum(len(q.clicked_results) for q in variant_queries)
                ctr = total_clicks / total_searches if total_searches > 0 else 0
                
                # Calculate average relevance
                avg_relevance = 0.0
                if variant_queries:
                    all_relevance = []
                    for q in variant_queries:
                        # Get results for this query (simplified)
                        all_relevance.extend([0.8] * q.results_count)  # Mock relevance
                    avg_relevance = np.mean(all_relevance) if all_relevance else 0.0
                
                variant_metrics[variant] = {
                    "total_searches": total_searches,
                    "total_clicks": total_clicks,
                    "ctr": ctr,
                    "average_relevance": avg_relevance,
                    "traffic_percentage": test.traffic_split[variant] * 100
                }
        
        return {
            "test_id": test_id,
            "test_name": test.name,
            "start_date": test.start_date.isoformat(),
            "end_date": test.end_date.isoformat(),
            "is_active": test.is_active,
            "variants": variant_metrics,
            "success_metrics": test.success_metrics
        }
    
    def get_search_analytics(self, company: Company, 
                           start_date: timezone.datetime = None,
                           end_date: timezone.datetime = None) -> Dict[str, Any]:
        """Get search analytics for a company"""
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        # Filter queries by company and date range
        company_queries = [
            q for q in self.search_queries
            if q.company_id == str(company.id) and start_date <= q.timestamp <= end_date
        ]
        
        if not company_queries:
            return {"status": "no_data", "message": "No search data available"}
        
        # Calculate metrics
        total_searches = len(company_queries)
        total_clicks = sum(len(q.clicked_results) for q in company_queries)
        overall_ctr = total_clicks / total_searches if total_searches > 0 else 0
        
        # Search type distribution
        search_types = {}
        for query in company_queries:
            search_types[query.search_type] = search_types.get(query.search_type, 0) + 1
        
        # Top queries
        query_counts = {}
        for query in company_queries:
            query_counts[query.query_text] = query_counts.get(query.query_text, 0) + 1
        
        top_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Performance metrics
        performance_metrics = {}
        for user_id in set(q.user_id for q in company_queries):
            if user_id in self.performance_metrics:
                performance_metrics[user_id] = self.performance_metrics[user_id]
        
        return {
            "company_id": str(company.id),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "overall_metrics": {
                "total_searches": total_searches,
                "total_clicks": total_clicks,
                "overall_ctr": overall_ctr,
                "unique_users": len(set(q.user_id for q in company_queries))
            },
            "search_type_distribution": search_types,
            "top_queries": top_queries,
            "performance_metrics": performance_metrics,
            "ctr_improvement_target": self.performance_targets["ctr_improvement"],
            "target_met": overall_ctr >= self.performance_targets["ctr_improvement"]
        }

# Global instance
hybrid_search_fusion = HybridSearchFusion()
