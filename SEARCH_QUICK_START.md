# Search & Knowledge Layer Quick Start Guide

## Overview
The Search & Knowledge Layer provides advanced search capabilities including faceted search, personalized ranking, query expansion, relationship graphs, and semantic caching.

## Quick Start

### 1. Basic Search
Search across all entity types:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/search/advanced/?q=acme"
```

### 2. Filtered Search
Search with specific entity types and filters:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/search/advanced/?q=tech&entity_type=accounts,leads&owner=<user_id>&status=active"
```

### 3. Search with Explainability
Get detailed scoring information:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/search/advanced/?q=acme&explain=true"
```

## Features

### Faceted Search
Filter results by:
- **owner**: Filter by record owner UUID
- **status**: Filter by status value
- **territory**: Filter by territory UUID
- **type**: Filter by type (for accounts)
- **rating**: Filter by rating (for leads)
- **source**: Filter by source (for leads)

Example:
```bash
GET /api/search/advanced/?q=tech&owner=<uuid>&status=open&territory=<uuid>
```

### Query Expansion
Add synonyms and acronyms to improve search results.

Create expansion term:
```bash
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "term": "CEO",
    "expansions": ["Chief Executive Officer", "President", "Managing Director"],
    "term_type": "synonym",
    "priority": 10,
    "is_active": true
  }' \
  "http://localhost:8000/api/search/query-expansion/"
```

List expansion terms:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/search/query-expansion/"
```

### Relationship Graph

#### Get Related Objects
Find all objects related to an entity:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/search/graph/?source_type=account&source_id=<uuid>"
```

Response:
```json
{
  "source_type": "account",
  "source_id": "...",
  "related_objects": {
    "contacts": ["uuid1", "uuid2"],
    "deals": ["uuid3", "uuid4"],
    "lead": ["uuid5"]
  }
}
```

#### Find Paths Between Objects
Find relationship paths between two entities:
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/search/graph/?source_type=lead&source_id=<uuid>&target_type=deal"
```

Response:
```json
{
  "source_type": "lead",
  "source_id": "...",
  "target_type": "deal",
  "paths": [
    [
      {"type": "lead", "id": "..."},
      {"type": "account", "id": "...", "relationship": "converted_to", "weight": 1.0},
      {"type": "deal", "id": "...", "relationship": "associated_with", "weight": 1.0}
    ]
  ],
  "path_count": 1
}
```

#### Rebuild Graph
Refresh the relationship graph after bulk changes:
```bash
curl -X POST -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/search/graph/rebuild/"
```

### Search Metrics

#### View Metrics Summary
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/search/metrics/summary/"
```

Response:
```json
{
  "total_searches": 1500,
  "cache_hit_rate": 0.65,
  "avg_execution_time": 42.5,
  "popular_queries": [
    {"query": "acme", "count": 50},
    {"query": "tech", "count": 35}
  ],
  "popular_entity_types": [
    {"entity_type": "accounts", "count": 800},
    {"entity_type": "contacts", "count": 500}
  ]
}
```

#### Track User Interactions
Track when users click on search results (for ranking improvement):
```bash
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "search_metric_id": "<metric_uuid>",
    "result_id": "<result_uuid>",
    "result_rank": 1
  }' \
  "http://localhost:8000/api/search/track/"
```

## Response Format

### Advanced Search Response
```json
{
  "query": "acme",
  "expanded_queries": ["acme corp", "acme corporation"],
  "results": {
    "accounts": [
      {
        "id": "uuid",
        "name": "Acme Corporation",
        "type": "customer",
        "industry": "Technology",
        "owner": "owner-uuid"
      }
    ],
    "contacts": [
      {
        "id": "uuid",
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "email": "john@acme.com",
        "account": "account-uuid",
        "owner": "owner-uuid"
      }
    ]
  },
  "facets": {
    "accounts": {
      "owner": [{"value": "uuid", "count": 5}],
      "type": [
        {"value": "customer", "count": 10},
        {"value": "prospect", "count": 7}
      ],
      "industry": [{"value": "Technology", "count": 15}]
    }
  },
  "total_results": 12,
  "cache_hit": false,
  "execution_time_ms": 45
}
```

### Explainability Response (when explain=true)
```json
{
  "explanations": {
    "accounts:uuid": {
      "result_id": "uuid",
      "entity_type": "accounts",
      "scores": {
        "lexical": 0.8,
        "personalization": 0.7,
        "boosting": 0.4
      },
      "total_score": 1.9,
      "matched_fields": [
        {"field": "name", "term": "acme", "score": 1.0}
      ],
      "ranking_factors": [
        {"factor": "ownership", "boost": 0.4}
      ]
    }
  }
}
```

## Personalized Ranking

Results are automatically ranked based on:

1. **Recency (30%)**: Items created/updated recently rank higher
   - Score decays over 365 days
   - Recent = created within last 7 days gets extra boost

2. **Ownership (40%)**: Your own items rank higher
   - Owned items: 1.0 score
   - Others' items: 0.5 score

3. **Interaction (30%)**: Frequently accessed items rank higher
   - Based on click history (last 30 days)
   - Max score at 10+ interactions

## Performance Tips

1. **Use Facets**: Filter by owner, status, territory to reduce result set
2. **Enable Caching**: Identical queries are cached for 1 hour
3. **Limit Entity Types**: Specify only needed entity types
4. **Use Query Expansion**: Add common synonyms for your industry
5. **Track Interactions**: Click tracking improves personalization

## Example Workflows

### Search for Customer Accounts
```bash
GET /api/search/advanced/?q=tech&entity_type=accounts&type=customer&is_active=true
```

### Find Hot Leads
```bash
GET /api/search/advanced/?q=software&entity_type=leads&rating=hot&status=qualified
```

### Search My Records
```bash
GET /api/search/advanced/?q=acme&owner=<my_user_id>
```

### Analyze Deal Pipeline
```bash
# Find all related entities from a lead
GET /api/search/graph/?source_type=lead&source_id=<lead_id>&depth=2
```

## Integration with Frontend

### React/JavaScript Example
```javascript
import axios from 'axios';

async function searchAccounts(query, filters = {}) {
  const params = new URLSearchParams({
    q: query,
    entity_type: 'accounts',
    ...filters
  });
  
  const response = await axios.get(
    `/api/search/advanced/?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  return response.data;
}

// Usage
const results = await searchAccounts('acme', {
  owner: userId,
  status: 'active'
});
```

### Track Search Click
```javascript
async function trackClick(metricId, resultId, rank) {
  await axios.post(
    '/api/search/track/',
    {
      search_metric_id: metricId,
      result_id: resultId,
      result_rank: rank
    },
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
}
```

## Best Practices

1. **Always track clicks** for better personalization
2. **Use query expansion** for industry-specific terms
3. **Rebuild graph** after bulk imports/updates
4. **Monitor metrics** to optimize search quality
5. **Explain results** during development to understand ranking
6. **Use facets** to guide users to relevant results
7. **Cache frequently-used queries** for better performance

## Troubleshooting

### Slow Searches
- Check if database has indexes
- Use more specific facet filters
- Limit entity types
- Check cache hit rate

### Poor Ranking
- Verify ownership data is correct
- Add more query expansion terms
- Track more user interactions
- Check recency of records

### Missing Results
- Verify permissions
- Check is_active filters
- Try query expansion terms
- Check company isolation

## Support
For issues or questions, refer to:
- API Documentation: `/docs/API_REFERENCE.md`
- Implementation Summary: `/SEARCH_IMPLEMENTATION_SUMMARY.md`
- Tests: `/search/tests.py`
