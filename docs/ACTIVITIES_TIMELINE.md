# Activities Timeline Design

## Overview
The Activities Timeline provides a unified view of all customer interactions across different entity types (Accounts, Contacts, Leads, Deals). This document describes the implementation and future performance enhancements.

## Current Implementation (Phase 2)

### Data Model

Activities use Django's ContentTypes framework for generic relationships:

```python
class Activity(CompanyIsolatedModel):
    # Activity metadata
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    activity_date = models.DateTimeField()
    
    # Generic relationship to any entity
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
```

### API Endpoint

**GET /api/v1/activities/timeline/**

Query Parameters:
- `object_type` - Filter by entity type (e.g., "crm.account", "crm.lead")
- `object_id` - Filter by specific entity ID
- `activity_type` - Filter by activity type (call, email, meeting, etc.)
- `date_from` - Start date filter
- `date_to` - End date filter
- `assigned_to` - Filter by assigned user

Response Structure:
```json
{
    "count": 123,
    "results": [
        {
            "id": "uuid",
            "activity_type": "call",
            "subject": "Follow-up call",
            "activity_date": "2024-01-15T10:30:00Z",
            "related_to": {
                "type": "crm.lead",
                "id": "lead-uuid",
                "name": "Acme Corp"
            },
            "assigned_to": {
                "id": "user-uuid",
                "name": "John Doe"
            },
            "status": "completed",
            "priority": "high"
        }
    ]
}
```

### Current Indexes

```python
class Activity:
    class Meta:
        indexes = [
            models.Index(fields=['company', 'activity_type']),
            models.Index(fields=['company', 'assigned_to']),
            models.Index(fields=['company', 'activity_date']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'priority']),
        ]
```

## Performance Considerations

### Current Limitations
1. **Linear scaling**: As activity count grows, queries slow down
2. **No full-text search**: Subject/description searches use ILIKE (slow)
3. **ContentType joins**: Generic FK requires additional joins
4. **No caching**: Every request hits database

### Query Optimization (Current)
```python
# In api_views.py
activities = Activity.objects.filter(
    company=request.user.company_access.first().company
).select_related(
    'content_type',
    'assigned_to'
).order_by('-activity_date')[:100]  # Limit for performance
```

## Future Performance Enhancements (Phase 3)

### 1. GIN Index for Full-Text Search

PostgreSQL GIN (Generalized Inverted Index) for subject/description search:

```python
# Migration
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField

class Activity(CompanyIsolatedModel):
    # ... existing fields ...
    
    # Add search vector field
    search_vector = SearchVectorField(null=True, blank=True)
    
    class Meta:
        indexes = [
            # ... existing indexes ...
            GinIndex(fields=['search_vector'], name='activity_search_gin_idx'),
        ]

# Trigger to maintain search_vector
"""
CREATE TRIGGER activity_search_vector_update
BEFORE INSERT OR UPDATE ON activities_activity
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.english', subject, description);
"""
```

Usage:
```python
from django.contrib.postgres.search import SearchQuery, SearchRank

# Full-text search
query = SearchQuery('follow up call')
activities = Activity.objects.annotate(
    rank=SearchRank(F('search_vector'), query)
).filter(search_vector=query).order_by('-rank')
```

**Benefits:**
- 10-100x faster text searches
- Handles stemming, stop words
- Relevance ranking

### 2. Table Partitioning

For companies with millions of activities, partition by date:

```sql
-- Create partitioned table
CREATE TABLE activities_activity_partitioned (
    LIKE activities_activity INCLUDING ALL
) PARTITION BY RANGE (activity_date);

-- Create partitions (quarterly)
CREATE TABLE activities_activity_2024_q1 
    PARTITION OF activities_activity_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE activities_activity_2024_q2
    PARTITION OF activities_activity_partitioned
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- ... continue for other quarters
```

**Benefits:**
- Faster queries (scans only relevant partitions)
- Easier archival (drop old partitions)
- Better vacuum performance

### 3. Materialized View for Timeline Summary

Pre-aggregate common queries:

```sql
CREATE MATERIALIZED VIEW activity_timeline_summary AS
SELECT
    company_id,
    DATE(activity_date) as activity_day,
    activity_type,
    status,
    COUNT(*) as activity_count,
    COUNT(DISTINCT assigned_to_id) as user_count
FROM activities_activity
GROUP BY company_id, DATE(activity_date), activity_type, status;

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY activity_timeline_summary;

-- Create index
CREATE INDEX ON activity_timeline_summary (company_id, activity_day);
```

**Benefits:**
- Instant dashboard metrics
- Reduced load on main table
- Can refresh on schedule

### 4. Redis Caching Strategy

Cache common timeline queries:

```python
from django.core.cache import cache
import hashlib
import json

def get_cached_timeline(company_id, filters):
    """Get timeline with caching"""
    # Create cache key from filters
    cache_key_data = {
        'company_id': str(company_id),
        'filters': filters
    }
    cache_key = 'timeline:' + hashlib.md5(
        json.dumps(cache_key_data, sort_keys=True).encode()
    ).hexdigest()
    
    # Try cache
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Query database
    activities = Activity.objects.filter(company_id=company_id)
    # ... apply filters ...
    results = list(activities.values())
    
    # Cache for 5 minutes
    cache.set(cache_key, results, timeout=300)
    
    return results

# Invalidate cache on activity changes
@receiver(post_save, sender=Activity)
def invalidate_timeline_cache(sender, instance, **kwargs):
    # Clear all timeline caches for this company
    cache_pattern = f"timeline:*{instance.company_id}*"
    # Use Redis SCAN to find and delete matching keys
```

**Benefits:**
- Near-instant response for repeated queries
- Reduced database load
- Configurable TTL

### 5. Elasticsearch Integration

For advanced search and analytics:

```python
from elasticsearch_dsl import Document, Date, Integer, Keyword, Text

class ActivityDocument(Document):
    company_id = Keyword()
    activity_type = Keyword()
    subject = Text()
    description = Text()
    activity_date = Date()
    assigned_to_id = Keyword()
    status = Keyword()
    priority = Keyword()
    
    # Related entity info (denormalized)
    related_type = Keyword()
    related_id = Keyword()
    related_name = Text()
    
    class Index:
        name = 'activities'
        settings = {
            'number_of_shards': 2,
            'number_of_replicas': 1
        }

# Index on create/update
@receiver(post_save, sender=Activity)
def index_activity(sender, instance, **kwargs):
    doc = ActivityDocument(
        meta={'id': instance.id},
        company_id=str(instance.company_id),
        activity_type=instance.activity_type,
        subject=instance.subject,
        description=instance.description,
        activity_date=instance.activity_date,
        # ... other fields
    )
    doc.save()
```

Search:
```python
from elasticsearch_dsl import Search

def search_activities(company_id, query):
    s = Search(index='activities')
    s = s.filter('term', company_id=str(company_id))
    s = s.query('multi_match', query=query, fields=['subject', 'description'])
    s = s.sort('-activity_date')
    
    response = s.execute()
    return response.hits
```

**Benefits:**
- Sub-second full-text search
- Faceted search (filters)
- Aggregations for analytics
- Scales horizontally

### 6. Database Connection Pooling

Use PgBouncer for connection pooling:

```ini
# pgbouncer.ini
[databases]
crm_db = host=localhost port=5432 dbname=crm_db

[pgbouncer]
pool_mode = transaction
max_client_conn = 100
default_pool_size = 25
min_pool_size = 5
```

**Benefits:**
- Reduced connection overhead
- Better resource utilization
- Handles traffic spikes

## Implementation Roadmap

### Phase 3 (Q1 2024)
- [ ] Add GIN index for full-text search
- [ ] Implement Redis caching for timeline queries
- [ ] Add cache invalidation on activity changes
- [ ] Performance testing with 1M+ activities

### Phase 4 (Q2 2024)
- [ ] Implement table partitioning (for customers with high volume)
- [ ] Create materialized view for dashboard
- [ ] Add Elasticsearch integration
- [ ] Implement connection pooling with PgBouncer

### Phase 5 (Q3 2024)
- [ ] Real-time updates via WebSocket
- [ ] Advanced analytics dashboards
- [ ] AI-powered activity suggestions
- [ ] Activity sentiment analysis

## Performance Benchmarks (Target)

| Scenario | Current | Phase 3 Target | Phase 4 Target |
|----------|---------|----------------|----------------|
| Timeline load (100 activities) | 200ms | 50ms | 20ms |
| Full-text search | 1500ms | 150ms | 30ms |
| Filter by date range | 300ms | 80ms | 30ms |
| Aggregate queries | 2000ms | 500ms | 100ms |
| Concurrent users | 50 | 200 | 1000 |

## Monitoring

### Metrics to Track
- Query execution time (p50, p95, p99)
- Cache hit rate
- Index usage
- Connection pool utilization
- Elasticsearch cluster health

### Tools
- Django Debug Toolbar (development)
- New Relic / Datadog (production)
- PostgreSQL pg_stat_statements
- Elasticsearch Marvel

## Testing Checklist

- [ ] Timeline query with various filters
- [ ] Performance with 1K activities
- [ ] Performance with 100K activities
- [ ] Performance with 1M+ activities
- [ ] Cache hit rate measurement
- [ ] Concurrent user load test
- [ ] Full-text search relevance
- [ ] Elasticsearch indexing lag
- [ ] Cache invalidation correctness

## Notes

- GIN indexes are write-heavy; consider for read-heavy workloads
- Partitioning requires PostgreSQL 10+
- Elasticsearch adds operational complexity
- Monitor cache memory usage
- Consider read replicas for reporting queries
