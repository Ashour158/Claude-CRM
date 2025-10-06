# Global Search Foundation

## Overview

The Global Search Foundation provides fast, relevant search across multiple entity types with intelligent scoring and caching.

## Features

- **Multi-Model Search**: Search accounts, contacts, leads, and deals simultaneously
- **Relevance Scoring**: Weighted scoring based on field importance
- **Query Caching**: 30-second cache to reduce database load
- **Entity Filtering**: Optional filtering by entity types
- **Pagination**: Configurable result limits per entity type

## Architecture

```
User Query → Search Service → Cache Check → DB Query → Scoring → Response
```

### Components

1. **GlobalSearchService**: Core search logic
2. **GlobalSearchView**: API endpoint
3. **SearchSuggestionsView**: Quick suggestions endpoint

## API Endpoints

### Global Search

```
GET /api/core/search/?q={query}&types={types}&limit={limit}
```

**Query Parameters:**

- `q` (required): Search query string (minimum 2 characters)
- `types` (optional): Comma-separated entity types (account, contact, lead, deal)
- `limit` (optional): Max results per entity type (default: 50, max: 100)

**Example Request:**

```
GET /api/core/search/?q=john&types=contact,lead&limit=20
```

**Response:**

```json
{
  "query": "john",
  "total_results": 15,
  "cached": false,
  "results": {
    "contact": [
      {
        "id": "uuid",
        "type": "contact",
        "title": "John Smith",
        "subtitle": "john.smith@example.com",
        "description": "Senior Account Manager",
        "metadata": {
          "account": "Acme Corp"
        },
        "score": 18
      }
    ],
    "lead": [
      {
        "id": "uuid",
        "type": "lead",
        "title": "John Doe",
        "subtitle": "john.doe@company.com",
        "description": "Tech Solutions Inc",
        "metadata": {
          "status": "qualified",
          "source": "website"
        },
        "score": 15
      }
    ]
  }
}
```

### Search Suggestions

```
GET /api/core/search/suggestions/?q={query}
```

Returns top 5 results per entity type, flattened and sorted by score.

**Response:**

```json
{
  "query": "john",
  "suggestions": [
    {
      "type": "contact",
      "id": "uuid",
      "text": "John Smith",
      "subtitle": "john.smith@example.com"
    },
    {
      "type": "lead",
      "id": "uuid",
      "text": "John Doe",
      "subtitle": "john.doe@company.com"
    }
  ]
}
```

## Scoring Algorithm

### Field Weights

| Field | Weight | Use Case |
|-------|--------|----------|
| name | 10 | Primary identifier |
| email | 8 | Unique contact info |
| company_name | 7 | Company reference |
| title | 6 | Job title/position |
| description | 3 | Additional context |
| notes | 2 | Detailed information |

### Score Calculation

```python
score = 0
if query in name:
    score += 10
if query in email:
    score += 8
if query in company_name:
    score += 7
# ... etc
```

Results are sorted by score in descending order.

## Search Fields by Entity

### Account

- name (weight: 10)
- domain (weight: 7)
- industry (weight: 5)
- description (weight: 3)

### Contact

- first_name + last_name (weight: 10)
- email (weight: 8)
- title (weight: 6)
- phone (weight: 4)

### Lead

- first_name + last_name (weight: 10)
- email (weight: 8)
- company_name (weight: 7)
- title (weight: 6)

### Deal

- name (weight: 10)
- account.name (weight: 7)
- description (weight: 3)

## Caching Strategy

### Cache Key Format

```
global_search:{company_id}:{query}:{entity_types}:{limit}
```

### Cache Configuration

- **TTL**: 30 seconds
- **Backend**: Redis (configurable)
- **Invalidation**: Automatic expiration

### Cache Behavior

```python
# Check cache
cache_key = f"global_search:{company.id}:{query}:all:50"
cached_results = cache.get(cache_key)

if cached_results:
    return cached_results

# Perform search
results = perform_search(query)

# Cache results
cache.set(cache_key, results, 30)  # 30 seconds TTL
```

## Performance Optimization

### Query Optimization

1. **Limit Results**: Maximum 100 results per entity type
2. **Distinct Results**: Use `.distinct()` to avoid duplicates
3. **Select Related**: Prefetch related objects for metadata
4. **Index Usage**: Search fields should have database indexes

### Recommended Indexes

```sql
-- Accounts
CREATE INDEX idx_account_name ON accounts(name);
CREATE INDEX idx_account_domain ON accounts(domain);

-- Contacts
CREATE INDEX idx_contact_email ON contacts(email);
CREATE INDEX idx_contact_name ON contacts(first_name, last_name);

-- Leads
CREATE INDEX idx_lead_email ON leads(email);
CREATE INDEX idx_lead_company ON leads(company_name);

-- Deals
CREATE INDEX idx_deal_name ON deals(name);
```

## Usage Examples

### Python/Django

```python
from core.search.service import GlobalSearchService

# Initialize service
search_service = GlobalSearchService(company, user)

# Perform search
results = search_service.search(
    query='john smith',
    entity_types=['contact', 'lead'],
    limit=20
)
```

### JavaScript/Frontend

```javascript
async function globalSearch(query, types = null) {
  const params = new URLSearchParams({ q: query });
  if (types) {
    params.append('types', types.join(','));
  }
  
  const response = await fetch(`/api/core/search/?${params}`);
  return response.json();
}

// Usage
const results = await globalSearch('acme', ['account', 'contact']);
```

### React Component

```jsx
function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const handleSearch = async () => {
    if (query.length < 2) return;
    
    setLoading(true);
    const data = await globalSearch(query);
    setResults(data);
    setLoading(false);
  };
  
  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
      />
      {loading && <Spinner />}
      {results && <SearchResults data={results} />}
    </div>
  );
}
```

## Error Handling

### Invalid Query

```json
{
  "error": "Query parameter 'q' is required"
}
```
Status: `400 Bad Request`

### Query Too Short

```json
{
  "error": "Query must be at least 2 characters"
}
```
Status: `400 Bad Request`

### Invalid Entity Types

```json
{
  "error": "Invalid entity types: invalid_type",
  "valid_types": ["account", "contact", "lead", "deal"]
}
```
Status: `400 Bad Request`

## Best Practices

1. **Minimum Query Length**: Enforce 2+ characters to avoid overwhelming results
2. **Debouncing**: Use debouncing in frontend to reduce API calls
3. **Result Limits**: Set reasonable limits based on UI requirements
4. **Entity Type Filtering**: Filter by relevant types for better performance
5. **Cache Monitoring**: Monitor cache hit rates and adjust TTL as needed

## Future Enhancements

### Short Term
- Full-text search with PostgreSQL tsvector
- Fuzzy matching for typo tolerance
- Synonym support
- Phrase search with quotes

### Long Term
- Elasticsearch integration for advanced search
- Faceted search with filters
- Search history and trending queries
- Personalized search ranking
- Vector search for semantic similarity
- Multi-language support

## Monitoring

### Key Metrics

- **Search Volume**: Total searches per hour/day
- **Cache Hit Rate**: % of cached responses
- **Average Response Time**: p50, p95, p99
- **Top Queries**: Most common search terms
- **Zero Result Queries**: Queries with no results

### Logging

Search queries are logged for analytics:

```python
logger.info(f"Search: query={query}, types={types}, results={total}, cached={cached}")
```

## Security Considerations

1. **Company Scoping**: All searches are scoped to user's company
2. **Permission Filtering**: Results respect user permissions
3. **Rate Limiting**: Implement rate limits to prevent abuse
4. **SQL Injection**: Use ORM query building (no raw SQL)
5. **Input Validation**: Sanitize and validate all input

## Testing

### Unit Tests

```python
def test_search_accounts():
    service = GlobalSearchService(company, user)
    results = service.search('acme', ['account'], 10)
    
    assert 'account' in results['results']
    assert len(results['results']['account']) <= 10
    assert results['total_results'] > 0

def test_search_scoring():
    # Create test data
    Account.objects.create(name='Acme Corp')
    Account.objects.create(name='Acme Solutions')
    
    service = GlobalSearchService(company, user)
    results = service.search('acme')
    
    # First result should have higher score
    accounts = results['results']['account']
    assert accounts[0]['score'] >= accounts[1]['score']
```

### Integration Tests

```python
def test_search_endpoint():
    client = APIClient()
    client.force_authenticate(user=user)
    
    response = client.get('/api/core/search/?q=test')
    
    assert response.status_code == 200
    assert 'results' in response.data
```
