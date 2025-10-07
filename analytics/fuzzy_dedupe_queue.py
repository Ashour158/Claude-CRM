# analytics/fuzzy_dedupe_queue.py
"""
Fuzzy Dedupe Queue Implementation
P2 Priority: Merge accuracy >90% sample

This module implements:
- Fuzzy matching algorithms for duplicate detection
- Queue-based processing for large datasets
- Merge accuracy tracking and optimization
- Machine learning-based similarity scoring
- Automated merge decision making
"""

import logging
import hashlib
import difflib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from core.models import Company, User
from events.event_bus import event_bus
import uuid
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import Levenshtein

logger = logging.getLogger(__name__)

@dataclass
class DedupeCandidate:
    """Candidate for deduplication"""
    id: str
    entity_type: str
    entity_id: str
    company_id: str
    data: Dict[str, Any]
    fingerprint: str
    similarity_score: float
    confidence_score: float
    created_at: timezone.datetime
    processed: bool = False

@dataclass
class MergeDecision:
    """Merge decision result"""
    id: str
    primary_id: str
    duplicate_id: str
    merge_confidence: float
    merge_reason: str
    merged_data: Dict[str, Any]
    created_at: timezone.datetime
    approved_by: Optional[str] = None
    status: str = "pending"

@dataclass
class DedupeMetrics:
    """Deduplication metrics"""
    total_candidates: int
    duplicates_found: int
    merge_accuracy: float
    false_positives: int
    false_negatives: int
    processing_time_ms: float
    confidence_threshold: float

class FuzzyDedupeQueue:
    """
    Fuzzy deduplication queue with high merge accuracy
    """
    
    def __init__(self):
        self.dedupe_queue: List[DedupeCandidate] = []
        self.merge_decisions: List[MergeDecision] = []
        self.similarity_cache: Dict[str, float] = {}
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
        # Configuration
        self.config = {
            "similarity_threshold": 0.85,
            "confidence_threshold": 0.90,
            "merge_accuracy_target": 0.90,
            "batch_size": 100,
            "max_queue_size": 10000
        }
        
        # Field weights for similarity calculation
        self.field_weights = {
            "name": 0.4,
            "email": 0.3,
            "phone": 0.2,
            "address": 0.1
        }
    
    def add_to_queue(self, entity_type: str, entity_id: str, 
                    data: Dict[str, Any], company: Company) -> DedupeCandidate:
        """Add entity to deduplication queue"""
        # Create fingerprint for the entity
        fingerprint = self._create_fingerprint(data)
        
        candidate = DedupeCandidate(
            id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            company_id=str(company.id),
            data=data,
            fingerprint=fingerprint,
            similarity_score=0.0,
            confidence_score=0.0,
            created_at=timezone.now()
        )
        
        self.dedupe_queue.append(candidate)
        
        # Publish queue addition event
        event_bus.publish(
            event_type='DEDUPE_CANDIDATE_ADDED',
            data={
                'candidate_id': candidate.id,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'queue_size': len(self.dedupe_queue)
            },
            company_id=company.id
        )
        
        logger.info(f"Dedupe candidate added: {entity_type}:{entity_id}")
        return candidate
    
    def _create_fingerprint(self, data: Dict[str, Any]) -> str:
        """Create fingerprint for entity data"""
        # Normalize data for fingerprinting
        normalized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                normalized_data[key] = value.lower().strip()
            else:
                normalized_data[key] = str(value).lower().strip()
        
        # Create hash of normalized data
        data_str = json.dumps(normalized_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def process_queue(self, company: Company) -> List[MergeDecision]:
        """Process deduplication queue for a company"""
        start_time = timezone.now()
        
        # Filter candidates for the company
        company_candidates = [
            c for c in self.dedupe_queue 
            if c.company_id == str(company.id) and not c.processed
        ]
        
        if not company_candidates:
            return []
        
        # Group candidates by entity type
        candidates_by_type = {}
        for candidate in company_candidates:
            if candidate.entity_type not in candidates_by_type:
                candidates_by_type[candidate.entity_type] = []
            candidates_by_type[candidate.entity_type].append(candidate)
        
        merge_decisions = []
        
        # Process each entity type
        for entity_type, candidates in candidates_by_type.items():
            entity_merges = self._process_entity_type(candidates, entity_type)
            merge_decisions.extend(entity_merges)
        
        # Update processing metrics
        processing_time = (timezone.now() - start_time).total_seconds() * 1000
        self._update_processing_metrics(len(company_candidates), len(merge_decisions), processing_time)
        
        # Publish processing completion event
        event_bus.publish(
            event_type='DEDUPE_QUEUE_PROCESSED',
            data={
                'company_id': str(company.id),
                'candidates_processed': len(company_candidates),
                'merges_found': len(merge_decisions),
                'processing_time_ms': processing_time
            },
            company_id=company.id
        )
        
        logger.info(f"Dedupe queue processed for {company.id}: {len(merge_decisions)} merges found")
        return merge_decisions
    
    def _process_entity_type(self, candidates: List[DedupeCandidate], 
                            entity_type: str) -> List[MergeDecision]:
        """Process candidates of a specific entity type"""
        merge_decisions = []
        
        # Sort candidates by creation time
        candidates.sort(key=lambda x: x.created_at)
        
        # Find similar pairs
        for i, candidate1 in enumerate(candidates):
            if candidate1.processed:
                continue
            
            best_match = None
            best_similarity = 0.0
            
            for j, candidate2 in enumerate(candidates[i+1:], i+1):
                if candidate2.processed:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_similarity(candidate1, candidate2)
                
                if similarity > best_similarity and similarity >= self.config["similarity_threshold"]:
                    best_similarity = similarity
                    best_match = candidate2
            
            # Create merge decision if good match found
            if best_match and best_similarity >= self.config["confidence_threshold"]:
                merge_decision = self._create_merge_decision(candidate1, best_match, best_similarity)
                merge_decisions.append(merge_decision)
                
                # Mark candidates as processed
                candidate1.processed = True
                best_match.processed = True
        
        return merge_decisions
    
    def _calculate_similarity(self, candidate1: DedupeCandidate, 
                            candidate2: DedupeCandidate) -> float:
        """Calculate similarity between two candidates"""
        # Check cache first
        cache_key = f"{candidate1.id}_{candidate2.id}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        # Calculate field-level similarities
        similarities = {}
        
        for field, weight in self.field_weights.items():
            if field in candidate1.data and field in candidate2.data:
                field_similarity = self._calculate_field_similarity(
                    candidate1.data[field], candidate2.data[field]
                )
                similarities[field] = field_similarity * weight
        
        # Calculate overall similarity
        if similarities:
            overall_similarity = sum(similarities.values()) / sum(self.field_weights.values())
        else:
            overall_similarity = 0.0
        
        # Apply ML-based similarity boost
        ml_similarity = self._calculate_ml_similarity(candidate1, candidate2)
        final_similarity = (overall_similarity * 0.7) + (ml_similarity * 0.3)
        
        # Cache result
        self.similarity_cache[cache_key] = final_similarity
        
        return final_similarity
    
    def _calculate_field_similarity(self, value1: Any, value2: Any) -> float:
        """Calculate similarity between two field values"""
        if value1 is None or value2 is None:
            return 0.0
        
        str1 = str(value1).lower().strip()
        str2 = str(value2).lower().strip()
        
        if str1 == str2:
            return 1.0
        
        # Use Levenshtein distance for string similarity
        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 0.0
        
        distance = Levenshtein.distance(str1, str2)
        similarity = 1.0 - (distance / max_len)
        
        # Use difflib for additional similarity check
        difflib_similarity = difflib.SequenceMatcher(None, str1, str2).ratio()
        
        # Combine both methods
        return (similarity + difflib_similarity) / 2
    
    def _calculate_ml_similarity(self, candidate1: DedupeCandidate, 
                               candidate2: DedupeCandidate) -> float:
        """Calculate ML-based similarity using TF-IDF"""
        try:
            # Extract text features from both candidates
            text1 = self._extract_text_features(candidate1.data)
            text2 = self._extract_text_features(candidate2.data)
            
            if not text1 or not text2:
                return 0.0
            
            # Vectorize texts
            texts = [text1, text2]
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return similarity
        except Exception as e:
            logger.warning(f"ML similarity calculation failed: {e}")
            return 0.0
    
    def _extract_text_features(self, data: Dict[str, Any]) -> str:
        """Extract text features from entity data"""
        text_parts = []
        
        for key, value in data.items():
            if isinstance(value, str) and value.strip():
                text_parts.append(f"{key}:{value}")
        
        return " ".join(text_parts)
    
    def _create_merge_decision(self, primary: DedupeCandidate, 
                             duplicate: DedupeCandidate, 
                             similarity: float) -> MergeDecision:
        """Create merge decision for two candidates"""
        merge_id = str(uuid.uuid4())
        
        # Merge data (primary takes precedence)
        merged_data = primary.data.copy()
        for key, value in duplicate.data.items():
            if key not in merged_data or not merged_data[key]:
                merged_data[key] = value
        
        merge_decision = MergeDecision(
            id=merge_id,
            primary_id=primary.entity_id,
            duplicate_id=duplicate.entity_id,
            merge_confidence=similarity,
            merge_reason=f"Similarity: {similarity:.3f}, Fields: {self._get_similar_fields(primary.data, duplicate.data)}",
            merged_data=merged_data,
            created_at=timezone.now()
        )
        
        self.merge_decisions.append(merge_decision)
        
        # Publish merge decision event
        event_bus.publish(
            event_type='MERGE_DECISION_CREATED',
            data={
                'merge_id': merge_id,
                'primary_id': primary.entity_id,
                'duplicate_id': duplicate.entity_id,
                'similarity': similarity,
                'confidence': similarity
            }
        )
        
        return merge_decision
    
    def _get_similar_fields(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> List[str]:
        """Get list of similar fields between two datasets"""
        similar_fields = []
        
        for key in set(data1.keys()) & set(data2.keys()):
            if data1.get(key) and data2.get(key):
                similarity = self._calculate_field_similarity(data1[key], data2[key])
                if similarity > 0.8:
                    similar_fields.append(key)
        
        return similar_fields
    
    def approve_merge(self, merge_id: str, approved_by: User) -> bool:
        """Approve a merge decision"""
        merge_decision = next((m for m in self.merge_decisions if m.id == merge_id), None)
        if not merge_decision:
            return False
        
        merge_decision.approved_by = str(approved_by.id)
        merge_decision.status = "approved"
        
        # Publish merge approval event
        event_bus.publish(
            event_type='MERGE_APPROVED',
            data={
                'merge_id': merge_id,
                'primary_id': merge_decision.primary_id,
                'duplicate_id': merge_decision.duplicate_id,
                'approved_by': str(approved_by.id)
            },
            actor=approved_by,
            company_id=approved_by.company.id
        )
        
        logger.info(f"Merge approved: {merge_id} by {approved_by.id}")
        return True
    
    def reject_merge(self, merge_id: str, rejected_by: User, reason: str = "") -> bool:
        """Reject a merge decision"""
        merge_decision = next((m for m in self.merge_decisions if m.id == merge_id), None)
        if not merge_decision:
            return False
        
        merge_decision.approved_by = str(rejected_by.id)
        merge_decision.status = "rejected"
        merge_decision.merge_reason += f" | Rejected: {reason}"
        
        # Publish merge rejection event
        event_bus.publish(
            event_type='MERGE_REJECTED',
            data={
                'merge_id': merge_id,
                'primary_id': merge_decision.primary_id,
                'duplicate_id': merge_decision.duplicate_id,
                'rejected_by': str(rejected_by.id),
                'reason': reason
            },
            actor=rejected_by,
            company_id=rejected_by.company.id
        )
        
        logger.info(f"Merge rejected: {merge_id} by {rejected_by.id}")
        return True
    
    def _update_processing_metrics(self, total_candidates: int, 
                                 merges_found: int, processing_time_ms: float):
        """Update processing metrics"""
        # This would typically update a metrics store
        # For now, we'll log the metrics
        logger.info(f"Processing metrics: {total_candidates} candidates, {merges_found} merges, {processing_time_ms:.2f}ms")
    
    def get_dedupe_metrics(self, company: Company, 
                          lookback_days: int = 7) -> DedupeMetrics:
        """Get deduplication metrics for a company"""
        cutoff_date = timezone.now() - timedelta(days=lookback_days)
        
        # Filter merge decisions by company and time
        company_merges = [
            merge for merge in self.merge_decisions
            if merge.created_at >= cutoff_date
        ]
        
        # Calculate metrics
        total_candidates = len([c for c in self.dedupe_queue if c.company_id == str(company.id)])
        duplicates_found = len(company_merges)
        
        # Calculate merge accuracy (simplified)
        approved_merges = [m for m in company_merges if m.status == "approved"]
        merge_accuracy = len(approved_merges) / len(company_merges) if company_merges else 0
        
        # Calculate false positives/negatives (simplified)
        false_positives = len([m for m in company_merges if m.status == "rejected"])
        false_negatives = 0  # Would need ground truth data to calculate
        
        return DedupeMetrics(
            total_candidates=total_candidates,
            duplicates_found=duplicates_found,
            merge_accuracy=merge_accuracy,
            false_positives=false_positives,
            false_negatives=false_negatives,
            processing_time_ms=0.0,  # Would be tracked separately
            confidence_threshold=self.config["confidence_threshold"]
        )
    
    def optimize_similarity_threshold(self, company: Company) -> Dict[str, Any]:
        """Optimize similarity threshold based on performance"""
        # Get recent merge decisions
        recent_merges = [
            merge for merge in self.merge_decisions
            if merge.created_at >= timezone.now() - timedelta(days=7)
        ]
        
        if not recent_merges:
            return {"status": "no_data", "message": "No recent merge data available"}
        
        # Analyze merge performance
        approved_merges = [m for m in recent_merges if m.status == "approved"]
        rejected_merges = [m for m in recent_merges if m.status == "rejected"]
        
        # Calculate optimal threshold
        if approved_merges:
            avg_approved_confidence = np.mean([m.merge_confidence for m in approved_merges])
        else:
            avg_approved_confidence = 0.0
        
        if rejected_merges:
            avg_rejected_confidence = np.mean([m.merge_confidence for m in rejected_merges])
        else:
            avg_rejected_confidence = 1.0
        
        # Suggest optimal threshold
        optimal_threshold = (avg_approved_confidence + avg_rejected_confidence) / 2
        
        return {
            "current_threshold": self.config["similarity_threshold"],
            "optimal_threshold": optimal_threshold,
            "approved_merges": len(approved_merges),
            "rejected_merges": len(rejected_merges),
            "avg_approved_confidence": avg_approved_confidence,
            "avg_rejected_confidence": avg_rejected_confidence,
            "threshold_adjustment_needed": abs(optimal_threshold - self.config["similarity_threshold"]) > 0.05
        }
    
    def get_queue_status(self, company: Company) -> Dict[str, Any]:
        """Get deduplication queue status"""
        company_candidates = [c for c in self.dedupe_queue if c.company_id == str(company.id)]
        
        return {
            "company_id": str(company.id),
            "queue_size": len(company_candidates),
            "processed_candidates": len([c for c in company_candidates if c.processed]),
            "pending_candidates": len([c for c in company_candidates if not c.processed]),
            "pending_merges": len([m for m in self.merge_decisions if m.status == "pending"]),
            "approved_merges": len([m for m in self.merge_decisions if m.status == "approved"]),
            "rejected_merges": len([m for m in self.merge_decisions if m.status == "rejected"]),
            "similarity_threshold": self.config["similarity_threshold"],
            "confidence_threshold": self.config["confidence_threshold"]
        }

# Global instance
fuzzy_dedupe_queue = FuzzyDedupeQueue()
