# Lead Scoring v2 Design

## Overview
Lead Scoring v2 implements a multi-factor heuristic scoring system that evaluates leads across multiple dimensions and provides detailed explanations for scores. This replaces the basic scoring logic with a comprehensive, transparent, and actionable system.

## Scoring Components

### 1. Status Component (25% default weight)
**Purpose**: Evaluate lead qualification status

**Status Weights**:
- `new`: 30/100
- `contacted`: 50/100
- `qualified`: 80/100
- `unqualified`: 10/100
- `converted`: 100/100
- `lost`: 0/100

**Calculation**:
```
score = (status_weight / 100) * component_weight
```

**Example**: Qualified lead with 25% component weight
```
score = (80 / 100) * 25 = 20 points
```

### 2. Recent Activity Component (20% default weight)
**Purpose**: Measure engagement through activities

**Activity Tracking**:
- Count activities in last 30 days
- Cap at 10 activities for scoring
- Activity types: calls, emails, meetings, demos

**Calculation**:
```
activity_factor = min(activity_count / 10, 1.0)
score = activity_factor * component_weight
```

**Example**: Lead with 7 activities
```
activity_factor = 7 / 10 = 0.7
score = 0.7 * 20 = 14 points
```

### 3. Age/Freshness Component (15% default weight)
**Purpose**: Prioritize recent leads

**Age Brackets**:
- 0-7 days: 100% factor (very fresh)
- 8-30 days: 80% factor (fresh)
- 31-90 days: 50% factor (moderate)
- 90+ days: 20% factor (old)

**Calculation**:
```
score = age_factor * component_weight
```

**Example**: 15-day old lead
```
score = 0.8 * 15 = 12 points
```

### 4. Completeness Component (20% default weight)
**Purpose**: Reward complete lead profiles

**Tracked Fields**:
- email
- phone
- company_name
- industry
- annual_revenue
- budget
- title

**Calculation**:
```
completeness_factor = filled_count / total_fields
score = completeness_factor * component_weight
```

**Example**: 5 of 7 fields filled
```
completeness_factor = 5 / 7 = 0.714
score = 0.714 * 20 = 14.3 points
```

### 5. Engagement Component (15% default weight)
**Purpose**: Measure digital engagement

**Engagement Signals**:
- Email opened: +30%
- Link clicked: +30%
- Form submitted: +40%

**Calculation**:
```
engagement_score = sum of signal percentages (capped at 100%)
score = min(engagement_score, 1.0) * component_weight
```

**Example**: Email opened + link clicked
```
engagement_score = 0.3 + 0.3 = 0.6
score = 0.6 * 15 = 9 points
```

### 6. Custom Fields Component (5% default weight)
**Purpose**: Organization-specific scoring factors

**Configuration**:
```json
{
  "custom_field_weights": {
    "budget_approved": 30,
    "decision_maker": 40,
    "urgent_need": 30
  }
}
```

**Calculation**:
```
custom_score = sum of matched field weights / 100
score = custom_score * component_weight
```

## Score Interpretation

### Score Ranges

| Score | Quality | Icon | Recommendation |
|-------|---------|------|----------------|
| 80-100 | HOT | 🔥 | Contact immediately, high priority |
| 60-79 | WARM | 🌡️ | Schedule follow-up within 24 hours |
| 40-59 | COOL | ❄️ | Add to nurture campaign |
| 0-39 | COLD | 🧊 | Consider disqualifying or long-term nurture |

### Explanation Format

```json
{
  "total_score": 78,
  "quality": "WARM",
  "recommendation": "Schedule follow-up within 24 hours",
  "components": [
    {
      "name": "status",
      "weight": 25,
      "contribution": 20,
      "explanation": "Status 'qualified' contributes 80% weight"
    },
    {
      "name": "recent_activity",
      "weight": 20,
      "contribution": 14,
      "explanation": "7 activities in last 30 days"
    },
    {
      "name": "age",
      "weight": 15,
      "contribution": 12,
      "explanation": "15 days old"
    },
    {
      "name": "completeness",
      "weight": 20,
      "contribution": 14,
      "explanation": "5/7 key fields filled"
    },
    {
      "name": "engagement",
      "weight": 15,
      "contribution": 9,
      "explanation": "Engagement signals: email_opened, link_clicked"
    },
    {
      "name": "custom_fields",
      "weight": 5,
      "contribution": 3,
      "explanation": "Custom fields scored: budget_approved"
    }
  ],
  "top_factors": ["status", "recent_activity", "completeness"],
  "calculated_at": "2024-01-15T10:30:00Z",
  "score_version": "v2"
}
```

## Score Cache

### Purpose
- Avoid recalculating scores on every request
- Provide historical scoring data
- Enable efficient sorting and filtering

### Cache Model
```python
class LeadScoreCache:
    lead: Lead
    total_score: int
    score_components: dict
    explanation: dict
    status_weight: int
    recent_activity_count: int
    days_since_creation: int
    custom_field_weights: dict
    calculated_at: datetime
    score_version: str
```

### Cache Refresh Strategy

#### Real-Time Triggers
- Lead status change
- New activity added
- Lead fields updated
- Manual recalculation request

#### Batch Refresh
- Scheduled: Daily at 2 AM
- Concurrency: 100 leads per batch
- Priority: Recently updated leads first

#### Cache Invalidation
- On lead deletion
- On score configuration change
- After 7 days (stale threshold)

## API Integration

### Get Lead Score
```http
GET /api/v1/leads/{id}/score/

Response:
{
  "lead_id": "uuid",
  "total_score": 78,
  "components": [...],
  "explanation": {...},
  "recommendation": "Schedule follow-up within 24 hours"
}
```

### Bulk Score Calculation
```http
POST /api/v1/leads/score-bulk/
{
  "lead_ids": ["uuid1", "uuid2", "uuid3"]
}

Response:
{
  "results": [
    {"lead_id": "uuid1", "total_score": 85, ...},
    {"lead_id": "uuid2", "total_score": 62, ...},
    {"lead_id": "uuid3", "total_score": 45, ...}
  ]
}
```

### Update Scoring Configuration
```http
PUT /api/v1/companies/{id}/scoring-config/
{
  "weights": {
    "status": 30,
    "recent_activity": 20,
    "age": 10,
    "completeness": 20,
    "engagement": 15,
    "custom_fields": 5
  },
  "custom_field_weights": {
    "budget_approved": 40,
    "decision_maker": 60
  }
}
```

## Customization

### Company-Specific Weights
Companies can adjust component weights based on their sales process:

**Example: Enterprise Sales Focus**
```json
{
  "status": 30,
  "recent_activity": 15,
  "age": 5,
  "completeness": 30,
  "engagement": 10,
  "custom_fields": 10
}
```

**Example: High-Volume Transactional Sales**
```json
{
  "status": 20,
  "recent_activity": 30,
  "age": 20,
  "completeness": 15,
  "engagement": 15,
  "custom_fields": 0
}
```

### Custom Field Scoring
Organizations can define custom boolean/choice fields that contribute to scoring:

```python
# Configuration
score_config = {
    "custom_field_weights": {
        "budget_approved": 40,
        "c_level_contact": 30,
        "urgent_timeline": 20,
        "existing_customer": 10
    }
}

# Lead with custom fields
lead.custom_fields = {
    "budget_approved": True,
    "c_level_contact": True,
    "urgent_timeline": False,
    "existing_customer": False
}

# Score calculation
# budget_approved (40) + c_level_contact (30) = 70
# normalized: 70/100 * 5% = 3.5 points
```

## Extension Path

### Phase 5+ Enhancements

#### ML-Based Scoring
- Train models on historical conversion data
- Feature importance from random forest
- Probability-based scores
- Automatic weight optimization

#### Predictive Features
- Time to conversion prediction
- Deal size estimation
- Churn risk for existing customers
- Next best action recommendations

#### Advanced Segmentation
- Lookalike modeling
- Cohort analysis
- Dynamic scoring based on industry/segment

#### Integration Enhancements
- External data enrichment (Clearbit, ZoomInfo)
- Intent data signals
- Website behavior tracking
- Social media engagement

## Performance Considerations

### Calculation Performance
- Single lead: <50ms
- Batch (100 leads): <2s
- Full company recalc: <5 min

### Caching Strategy
- Cache hit rate target: >90%
- Stale data acceptable: <24 hours
- Refresh batch size: 100 concurrent

### Database Optimization
- Indexed fields: company, total_score, calculated_at
- Denormalized cache for fast retrieval
- Separate table from main Lead model

## Testing Strategy

### Unit Tests
- Each component calculation
- Edge cases (missing fields, null values)
- Weight normalization
- Score clamping (0-100)

### Integration Tests
- Full score calculation with real lead
- Cache creation and updates
- Bulk scoring performance
- API endpoint responses

### Performance Tests
- 1000 lead scoring benchmark
- Cache hit rate measurement
- Concurrent scoring requests
- Database query counts

## Usage Examples

### Example 1: High-Quality Enterprise Lead
```
Status: qualified (20 pts)
Recent Activity: 10+ activities (20 pts)
Age: 5 days (15 pts)
Completeness: 7/7 fields (20 pts)
Engagement: All signals (15 pts)
Custom: Budget approved + C-level (5 pts)

Total: 95 pts (HOT) 🔥
Recommendation: Contact immediately
```

### Example 2: Average SMB Lead
```
Status: contacted (12.5 pts)
Recent Activity: 3 activities (6 pts)
Age: 45 days (7.5 pts)
Completeness: 4/7 fields (11.4 pts)
Engagement: Email opened (4.5 pts)
Custom: None (0 pts)

Total: 42 pts (COOL) ❄️
Recommendation: Add to nurture campaign
```

### Example 3: Stale Unqualified Lead
```
Status: unqualified (2.5 pts)
Recent Activity: 0 activities (0 pts)
Age: 120 days (3 pts)
Completeness: 2/7 fields (5.7 pts)
Engagement: None (0 pts)
Custom: None (0 pts)

Total: 11 pts (COLD) 🧊
Recommendation: Consider disqualifying
```

## Migration from v1

### Compatibility
- Existing `lead_score` field preserved
- V2 scores stored in separate cache table
- Gradual migration per company

### Migration Steps
1. Deploy v2 code
2. Create LeadScoreCache table
3. Backfill scores for active leads
4. Enable v2 in UI with toggle
5. Monitor performance and accuracy
6. Phase out v1 after validation period

## Monitoring

### Metrics to Track
- Average score by company
- Score distribution (HOT/WARM/COOL/COLD)
- Conversion rate by score bracket
- Score accuracy (predicted vs actual conversion)
- Cache hit rate
- Calculation latency

### Alerts
- Bulk scoring job failures
- Cache refresh delays >1 hour
- Calculation errors >1%
- Unusual score distributions

## Conclusion
Lead Scoring v2 provides a transparent, customizable, and actionable scoring system that helps sales teams prioritize leads effectively. The explanation-driven approach ensures users understand why leads receive certain scores, building trust in the system and improving adoption.
