# core/search/schemas.py
# Search data schemas and result structures

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class SearchQuery:
    """
    Represents a search query with all parameters.
    """
    query_string: str
    company_id: str
    user_id: Optional[str] = None
    fuzzy: bool = True
    max_results: int = 50
    offset: int = 0
    filters: Dict[str, Any] = field(default_factory=dict)
    sort_by: Optional[str] = None
    sort_order: str = 'desc'  # 'asc' or 'desc'
    include_inactive: bool = False
    boost_fields: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate query parameters"""
        if not self.query_string or not self.query_string.strip():
            raise ValueError("query_string cannot be empty")
        if not self.company_id:
            raise ValueError("company_id is required")
        if self.max_results < 1 or self.max_results > 1000:
            raise ValueError("max_results must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("offset must be non-negative")
        if self.sort_order not in ('asc', 'desc'):
            raise ValueError("sort_order must be 'asc' or 'desc'")


@dataclass
class SearchResult:
    """
    Represents a single search result with metadata.
    """
    model: str  # Model name (e.g., 'Account', 'Contact')
    record_id: str
    score: float  # Relevance score (0-100)
    data: Dict[str, Any]  # Record data
    highlights: Dict[str, List[str]] = field(default_factory=dict)  # Highlighted fields
    matched_fields: List[str] = field(default_factory=list)  # Fields that matched
    pii_filtered: bool = False  # Whether PII fields were filtered
    
    def __post_init__(self):
        """Validate result data"""
        if not self.model:
            raise ValueError("model is required")
        if not self.record_id:
            raise ValueError("record_id is required")
        if self.score < 0 or self.score > 100:
            raise ValueError("score must be between 0 and 100")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'model': self.model,
            'record_id': self.record_id,
            'score': self.score,
            'data': self.data,
            'highlights': self.highlights,
            'matched_fields': self.matched_fields,
            'pii_filtered': self.pii_filtered,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Create from dictionary"""
        return cls(
            model=data['model'],
            record_id=data['record_id'],
            score=data['score'],
            data=data.get('data', {}),
            highlights=data.get('highlights', {}),
            matched_fields=data.get('matched_fields', []),
            pii_filtered=data.get('pii_filtered', False),
        )


@dataclass
class SearchResponse:
    """
    Complete search response with results and metadata.
    """
    query: SearchQuery
    results: List[SearchResult]
    total_count: int
    execution_time_ms: float
    backend: str
    filters_applied: List[str] = field(default_factory=list)
    api_version: str = 'v1'
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'query': {
                'query_string': self.query.query_string,
                'filters': self.query.filters,
                'sort_by': self.query.sort_by,
                'sort_order': self.query.sort_order,
            },
            'results': [r.to_dict() for r in self.results],
            'total_count': self.total_count,
            'execution_time_ms': self.execution_time_ms,
            'backend': self.backend,
            'filters_applied': self.filters_applied,
            'api_version': self.api_version,
            'timestamp': self.timestamp.isoformat(),
            'pagination': {
                'offset': self.query.offset,
                'limit': self.query.max_results,
                'has_more': self.total_count > (self.query.offset + len(self.results))
            }
        }


@dataclass
class SearchScoringConfig:
    """
    Configuration for search scoring weights.
    """
    # Field weights for scoring
    field_weights: Dict[str, float] = field(default_factory=lambda: {
        'name': 10.0,
        'email': 8.0,
        'phone': 5.0,
        'company': 7.0,
        'title': 6.0,
        'description': 3.0,
        'notes': 2.0,
    })
    
    # Boost factors for different conditions
    exact_match_boost: float = 2.0
    prefix_match_boost: float = 1.5
    recent_record_boost: float = 1.2  # Boost records modified recently
    active_record_boost: float = 1.1  # Boost active records
    
    # Decay factors
    distance_decay_factor: float = 0.9  # Decay score by edit distance
    recency_decay_days: int = 90  # Number of days for recency decay
    
    def get_field_weight(self, field: str) -> float:
        """Get weight for a field"""
        return self.field_weights.get(field, 1.0)
