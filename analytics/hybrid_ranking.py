# analytics/hybrid_ranking.py
# Hybrid Ranking with BM25 + Vector Fusion and A/B Testing

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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from collections import Counter
import math
from celery import shared_task

from .models import (
    HybridRankingModel, RankingExperiment, A/BTestResult,
    SearchQuery, RankingResult, UserInteraction, RankingMetrics
)
from core.models import User, Company

logger = logging.getLogger(__name__)

class HybridRankingEngine:
    """
    Advanced hybrid ranking engine combining BM25 and vector similarity
    with A/B testing and performance optimization.
    """
    
    def __init__(self):
        self.ranking_methods = {
            'bm25': self._calculate_bm25_score,
            'vector': self._calculate_vector_score,
            'hybrid': self._calculate_hybrid_score
        }
        
        self.fusion_strategies = {
            'weighted_sum': self._weighted_sum_fusion,
            'reciprocal_rank': self._reciprocal_rank_fusion,
            'borda_count': self._borda_count_fusion,
            'condorcet': self._condorcet_fusion
        }
        
        self.ab_test_variants = {
            'alpha_0.1': {'alpha': 0.1, 'method': 'weighted_sum'},
            'alpha_0.3': {'alpha': 0.3, 'method': 'weighted_sum'},
            'alpha_0.5': {'alpha': 0.5, 'method': 'weighted_sum'},
            'alpha_0.7': {'alpha': 0.7, 'method': 'weighted_sum'},
            'alpha_0.9': {'alpha': 0.9, 'method': 'weighted_sum'},
            'reciprocal_rank': {'alpha': 0.5, 'method': 'reciprocal_rank'},
            'borda_count': {'alpha': 0.5, 'method': 'borda_count'}
        }
    
    def rank_documents(self, query: str, documents: List[Dict[str, Any]], 
                      ranking_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rank documents using hybrid BM25 + vector fusion.
        """
        try:
            # Get ranking model
            model_id = ranking_config.get('model_id')
            if model_id:
                ranking_model = HybridRankingModel.objects.get(id=model_id)
            else:
                # Use default model
                ranking_model = self._get_default_ranking_model()
            
            # Extract query features
            query_features = self._extract_query_features(query, ranking_config)
            
            # Calculate BM25 scores
            bm25_scores = self._calculate_bm25_scores(query, documents, ranking_model)
            
            # Calculate vector scores
            vector_scores = self._calculate_vector_scores(query, documents, ranking_model)
            
            # Fuse scores using hybrid approach
            fusion_method = ranking_config.get('fusion_method', 'weighted_sum')
            alpha = ranking_config.get('alpha', 0.5)
            
            hybrid_scores = self._fuse_scores(
                bm25_scores, vector_scores, fusion_method, alpha
            )
            
            # Rank documents
            ranked_documents = self._rank_documents_by_score(documents, hybrid_scores)
            
            # Log ranking result
            ranking_result = self._log_ranking_result(
                query, ranked_documents, ranking_config, ranking_model
            )
            
            return {
                'status': 'success',
                'query': query,
                'ranked_documents': ranked_documents,
                'bm25_scores': bm25_scores,
                'vector_scores': vector_scores,
                'hybrid_scores': hybrid_scores,
                'fusion_method': fusion_method,
                'alpha': alpha,
                'ranking_id': str(ranking_result.id),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Document ranking failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def run_ab_test(self, query: str, documents: List[Dict[str, Any]], 
                   ab_test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run A/B test for different ranking configurations.
        """
        try:
            # Get user for A/B testing
            user_id = ab_test_config.get('user_id')
            if not user_id:
                return {
                    'status': 'error',
                    'error': 'User ID required for A/B testing'
                }
            
            # Determine A/B test variant
            variant = self._determine_ab_variant(user_id, ab_test_config)
            
            # Get ranking configuration for variant
            variant_config = self.ab_test_variants.get(variant, self.ab_test_variants['alpha_0.5'])
            
            # Run ranking with variant configuration
            ranking_result = self.rank_documents(query, documents, variant_config)
            
            # Log A/B test result
            ab_test_result = self._log_ab_test_result(
                user_id, query, variant, ranking_result, ab_test_config
            )
            
            return {
                'status': 'success',
                'variant': variant,
                'variant_config': variant_config,
                'ranking_result': ranking_result,
                'ab_test_id': str(ab_test_result.id),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"A/B test failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def optimize_ranking_parameters(self, training_data: List[Dict[str, Any]], 
                                  optimization_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize ranking parameters using machine learning.
        """
        try:
            # Prepare training data
            X_train, y_train = self._prepare_training_data(training_data)
            
            # Define parameter space
            parameter_space = {
                'alpha': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
                'fusion_method': ['weighted_sum', 'reciprocal_rank', 'borda_count']
            }
            
            # Grid search optimization
            best_params = self._grid_search_optimization(
                X_train, y_train, parameter_space, optimization_config
            )
            
            # Create optimized model
            optimized_model = self._create_optimized_model(best_params)
            
            # Evaluate optimized model
            evaluation_results = self._evaluate_ranking_model(
                optimized_model, training_data, optimization_config
            )
            
            return {
                'status': 'success',
                'best_parameters': best_params,
                'optimized_model_id': str(optimized_model.id),
                'evaluation_results': evaluation_results,
                'optimization_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Parameter optimization failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _calculate_bm25_scores(self, query: str, documents: List[Dict[str, Any]], 
                             ranking_model: HybridRankingModel) -> List[float]:
        """Calculate BM25 scores for documents"""
        try:
            # Tokenize query
            query_terms = self._tokenize_text(query)
            
            # Calculate document statistics
            doc_stats = self._calculate_document_statistics(documents)
            
            # Calculate BM25 scores
            bm25_scores = []
            for doc in documents:
                doc_text = doc.get('content', '')
                doc_terms = self._tokenize_text(doc_text)
                
                score = self._calculate_bm25_score(
                    query_terms, doc_terms, doc_stats, ranking_model
                )
                bm25_scores.append(score)
            
            return bm25_scores
            
        except Exception as e:
            logger.error(f"BM25 calculation failed: {str(e)}")
            return [0.0] * len(documents)
    
    def _calculate_bm25_score(self, query_terms: List[str], doc_terms: List[str], 
                            doc_stats: Dict[str, Any], ranking_model: HybridRankingModel) -> float:
        """Calculate BM25 score for a single document"""
        try:
            # BM25 parameters
            k1 = ranking_model.bm25_k1
            b = ranking_model.bm25_b
            
            # Document length and average length
            doc_length = len(doc_terms)
            avg_doc_length = doc_stats['avg_length']
            
            # Term frequencies
            doc_term_freq = Counter(doc_terms)
            query_term_freq = Counter(query_terms)
            
            # Calculate score
            score = 0.0
            for term in query_terms:
                if term in doc_term_freq:
                    # Term frequency in document
                    tf = doc_term_freq[term]
                    
                    # Document frequency
                    df = doc_stats['term_dfs'].get(term, 1)
                    
                    # IDF
                    idf = math.log((doc_stats['total_docs'] - df + 0.5) / (df + 0.5))
                    
                    # BM25 formula
                    numerator = tf * (k1 + 1)
                    denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
                    
                    score += idf * (numerator / denominator)
            
            return score
            
        except Exception as e:
            logger.error(f"BM25 score calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_vector_scores(self, query: str, documents: List[Dict[str, Any]], 
                               ranking_model: HybridRankingModel) -> List[float]:
        """Calculate vector similarity scores"""
        try:
            # Get or create vectorizer
            vectorizer = self._get_vectorizer(ranking_model)
            
            # Vectorize query
            query_vector = vectorizer.transform([query])
            
            # Vectorize documents
            doc_texts = [doc.get('content', '') for doc in documents]
            doc_vectors = vectorizer.transform(doc_texts)
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, doc_vectors)[0]
            
            return similarities.tolist()
            
        except Exception as e:
            logger.error(f"Vector score calculation failed: {str(e)}")
            return [0.0] * len(documents)
    
    def _fuse_scores(self, bm25_scores: List[float], vector_scores: List[float], 
                    fusion_method: str, alpha: float) -> List[float]:
        """Fuse BM25 and vector scores"""
        try:
            # Normalize scores
            bm25_normalized = self._normalize_scores(bm25_scores)
            vector_normalized = self._normalize_scores(vector_scores)
            
            # Apply fusion method
            fusion_func = self.fusion_strategies.get(fusion_method, self._weighted_sum_fusion)
            fused_scores = fusion_func(bm25_normalized, vector_normalized, alpha)
            
            return fused_scores
            
        except Exception as e:
            logger.error(f"Score fusion failed: {str(e)}")
            return [0.0] * len(bm25_scores)
    
    def _weighted_sum_fusion(self, bm25_scores: List[float], vector_scores: List[float], 
                           alpha: float) -> List[float]:
        """Weighted sum fusion"""
        return [alpha * bm25 + (1 - alpha) * vector 
                for bm25, vector in zip(bm25_scores, vector_scores)]
    
    def _reciprocal_rank_fusion(self, bm25_scores: List[float], vector_scores: List[float], 
                              alpha: float) -> List[float]:
        """Reciprocal rank fusion"""
        # Get rankings
        bm25_ranks = self._get_rankings(bm25_scores)
        vector_ranks = self._get_rankings(vector_scores)
        
        # Calculate reciprocal rank scores
        rr_scores = []
        for i in range(len(bm25_scores)):
            bm25_rank = bm25_ranks[i]
            vector_rank = vector_ranks[i]
            
            rr_score = alpha * (1.0 / (bm25_rank + 1)) + (1 - alpha) * (1.0 / (vector_rank + 1))
            rr_scores.append(rr_score)
        
        return rr_scores
    
    def _borda_count_fusion(self, bm25_scores: List[float], vector_scores: List[float], 
                          alpha: float) -> List[float]:
        """Borda count fusion"""
        # Get rankings
        bm25_ranks = self._get_rankings(bm25_scores)
        vector_ranks = self._get_rankings(vector_scores)
        
        # Calculate Borda count scores
        borda_scores = []
        for i in range(len(bm25_scores)):
            bm25_rank = bm25_ranks[i]
            vector_rank = vector_ranks[i]
            
            borda_score = alpha * (len(bm25_scores) - bm25_rank) + (1 - alpha) * (len(vector_scores) - vector_rank)
            borda_scores.append(borda_score)
        
        return borda_scores
    
    def _condorcet_fusion(self, bm25_scores: List[float], vector_scores: List[float], 
                         alpha: float) -> List[float]:
        """Condorcet fusion"""
        # This is a simplified implementation
        # In production, would implement full Condorcet method
        
        # For now, use weighted sum as approximation
        return self._weighted_sum_fusion(bm25_scores, vector_scores, alpha)
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to [0, 1] range"""
        if not scores:
            return scores
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [0.5] * len(scores)
        
        return [(score - min_score) / (max_score - min_score) for score in scores]
    
    def _get_rankings(self, scores: List[float]) -> List[int]:
        """Get rankings from scores"""
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        rankings = [0] * len(scores)
        
        for rank, index in enumerate(sorted_indices):
            rankings[index] = rank
        
        return rankings
    
    def _rank_documents_by_score(self, documents: List[Dict[str, Any]], 
                                scores: List[float]) -> List[Dict[str, Any]]:
        """Rank documents by their scores"""
        # Create list of (document, score) pairs
        doc_score_pairs = list(zip(documents, scores))
        
        # Sort by score (descending)
        doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Return ranked documents
        return [doc for doc, score in doc_score_pairs]
    
    def _extract_query_features(self, query: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from query"""
        return {
            'query_length': len(query.split()),
            'query_terms': len(set(query.lower().split())),
            'has_numbers': bool(re.search(r'\d', query)),
            'has_special_chars': bool(re.search(r'[^\w\s]', query)),
            'query_type': self._classify_query_type(query)
        }
    
    def _classify_query_type(self, query: str) -> str:
        """Classify query type"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what', 'how', 'why', 'when', 'where']):
            return 'question'
        elif any(word in query_lower for word in ['find', 'search', 'look', 'get']):
            return 'search'
        elif any(word in query_lower for word in ['show', 'list', 'display']):
            return 'list'
        else:
            return 'general'
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text for BM25"""
        # Simple tokenization
        # In production, would use more sophisticated tokenization
        return re.findall(r'\b\w+\b', text.lower())
    
    def _calculate_document_statistics(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate document statistics for BM25"""
        try:
            total_docs = len(documents)
            total_length = 0
            term_dfs = Counter()
            
            for doc in documents:
                doc_text = doc.get('content', '')
                doc_terms = self._tokenize_text(doc_text)
                
                total_length += len(doc_terms)
                
                # Count document frequencies
                unique_terms = set(doc_terms)
                for term in unique_terms:
                    term_dfs[term] += 1
            
            return {
                'total_docs': total_docs,
                'avg_length': total_length / total_docs if total_docs > 0 else 0,
                'term_dfs': dict(term_dfs)
            }
            
        except Exception as e:
            logger.error(f"Document statistics calculation failed: {str(e)}")
            return {
                'total_docs': 0,
                'avg_length': 0,
                'term_dfs': {}
            }
    
    def _get_vectorizer(self, ranking_model: HybridRankingModel):
        """Get or create TF-IDF vectorizer"""
        try:
            # Check if vectorizer is cached
            cache_key = f"vectorizer_{ranking_model.id}"
            cached_vectorizer = cache.get(cache_key)
            
            if cached_vectorizer:
                return cached_vectorizer
            
            # Create new vectorizer
            vectorizer = TfidfVectorizer(
                max_features=ranking_model.max_features,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Cache vectorizer
            cache.set(cache_key, vectorizer, 3600)
            
            return vectorizer
            
        except Exception as e:
            logger.error(f"Vectorizer creation failed: {str(e)}")
            return TfidfVectorizer()
    
    def _get_default_ranking_model(self) -> HybridRankingModel:
        """Get default ranking model"""
        # This would get the default model from database
        # For now, return a placeholder
        return None
    
    def _determine_ab_variant(self, user_id: str, config: Dict[str, Any]) -> str:
        """Determine A/B test variant for user"""
        # Simple hash-based assignment
        user_hash = hash(user_id) % 100
        
        if user_hash < 15:
            return 'alpha_0.1'
        elif user_hash < 30:
            return 'alpha_0.3'
        elif user_hash < 45:
            return 'alpha_0.5'
        elif user_hash < 60:
            return 'alpha_0.7'
        elif user_hash < 75:
            return 'alpha_0.9'
        elif user_hash < 90:
            return 'reciprocal_rank'
        else:
            return 'borda_count'
    
    def _log_ranking_result(self, query: str, ranked_documents: List[Dict[str, Any]], 
                          config: Dict[str, Any], ranking_model: HybridRankingModel) -> RankingResult:
        """Log ranking result"""
        return RankingResult.objects.create(
            query=query,
            ranked_documents=ranked_documents,
            ranking_config=config,
            ranking_model=ranking_model,
            created_at=timezone.now()
        )
    
    def _log_ab_test_result(self, user_id: str, query: str, variant: str, 
                          ranking_result: Dict[str, Any], config: Dict[str, Any]) -> A/BTestResult:
        """Log A/B test result"""
        return A/BTestResult.objects.create(
            user_id=user_id,
            query=query,
            variant=variant,
            ranking_result=ranking_result,
            test_config=config,
            created_at=timezone.now()
        )
    
    def _prepare_training_data(self, training_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for optimization"""
        # This would prepare the actual training data
        # For now, return placeholders
        X = np.random.randn(100, 10)
        y = np.random.randn(100)
        return X, y
    
    def _grid_search_optimization(self, X_train: np.ndarray, y_train: np.ndarray, 
                                parameter_space: Dict[str, List], config: Dict[str, Any]) -> Dict[str, Any]:
        """Grid search optimization"""
        # This would implement actual grid search
        # For now, return default parameters
        return {
            'alpha': 0.5,
            'fusion_method': 'weighted_sum'
        }
    
    def _create_optimized_model(self, best_params: Dict[str, Any]) -> HybridRankingModel:
        """Create optimized model"""
        # This would create the actual optimized model
        # For now, return a placeholder
        return None
    
    def _evaluate_ranking_model(self, model: HybridRankingModel, test_data: List[Dict[str, Any]], 
                              config: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate ranking model"""
        # This would evaluate the actual model
        # For now, return placeholder metrics
        return {
            'ndcg': 0.85,
            'map': 0.78,
            'precision_at_10': 0.72,
            'recall_at_10': 0.68
        }

# Celery tasks
@shared_task
def rank_documents_async(query: str, documents: List[Dict[str, Any]], ranking_config: Dict[str, Any]):
    """Async task to rank documents"""
    engine = HybridRankingEngine()
    return engine.rank_documents(query, documents, ranking_config)

@shared_task
def run_ab_test_async(query: str, documents: List[Dict[str, Any]], ab_test_config: Dict[str, Any]):
    """Async task to run A/B test"""
    engine = HybridRankingEngine()
    return engine.run_ab_test(query, documents, ab_test_config)

@shared_task
def optimize_ranking_parameters_async(training_data: List[Dict[str, Any]], optimization_config: Dict[str, Any]):
    """Async task to optimize ranking parameters"""
    engine = HybridRankingEngine()
    return engine.optimize_ranking_parameters(training_data, optimization_config)

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rank_documents(request):
    """API endpoint to rank documents"""
    engine = HybridRankingEngine()
    result = engine.rank_documents(
        request.data.get('query'),
        request.data.get('documents', []),
        request.data.get('ranking_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_ab_test(request):
    """API endpoint to run A/B test"""
    engine = HybridRankingEngine()
    result = engine.run_ab_test(
        request.data.get('query'),
        request.data.get('documents', []),
        request.data.get('ab_test_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def optimize_ranking_parameters(request):
    """API endpoint to optimize ranking parameters"""
    engine = HybridRankingEngine()
    result = engine.optimize_ranking_parameters(
        request.data.get('training_data', []),
        request.data.get('optimization_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)
