# Search API Quick Reference

## Endpoints

### 1. Main Search
```http
POST /api/v1/search/
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "john smith",
  "models": ["Account", "Contact", "Lead", "Deal"],  // Optional
  "filters": {"is_active": true},                    // Optional
  "fuzzy": true,                                      // Optional, default: true
  "max_results": 50,                                  // Optional, default: 50
  "offset": 0,                                        // Optional, default: 0
  "apply_gdpr": true                                  // Optional, default: true
}
```

**Response:**
```json
{
  "query": {
    "query_string": "john smith",
    "filters": {"is_active": true}
  },
  "results": [
    {
      "model": "Contact",
      "record_id": "550e8400-e29b-41d4-a716-446655440000",
      "score": 85.5,
      "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "full_name": "John Smith",
        "email": "j***@example.com",
        "title": "CEO",
        "created_at": "2024-01-01T00:00:00Z"
      },
      "matched_fields": ["full_name", "email"],
      "pii_filtered": true
    }
  ],
  "total_count": 42,
  "execution_time_ms": 45.2,
  "backend": "PostgresSearchBackend",
  "filters_applied": ["GDPR"],
  "api_version": "v1",
  "timestamp": "2024-01-15T10:30:00Z",
  "pagination": {
    "offset": 0,
    "limit": 50,
    "has_more": false
  }
}
```

### 2. Autocomplete
```http
GET /api/v1/search/autocomplete/?query=john&field=name&limit=10
Authorization: Bearer <token>
```

**Response:**
```json
{
  "suggestions": [
    "John Smith",
    "John Doe",
    "Johnny Appleseed"
  ]
}
```

### 3. Health Check
```http
GET /api/v1/search/health/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "service": "SearchService",
  "backend": "postgres",
  "status": "healthy",
  "details": {
    "backend": "PostgresSearchBackend",
    "extensions": {
      "pg_trgm": true
    },
    "tables": {
      "Account": {"table": "crm_account", "count": 1523},
      "Contact": {"table": "crm_contact", "count": 4892},
      "Lead": {"table": "crm_lead", "count": 2341},
      "Deal": {"table": "deals_deal", "count": 987}
    }
  },
  "gdpr_enabled": true
}
```

## Python SDK Usage

### Basic Search
```python
from core.search import SearchService

search_service = SearchService()

response = search_service.search(
    query_string="john smith",
    company_id="your-company-id",
    models=['Contact', 'Lead'],
    fuzzy=True,
    max_results=50
)

for result in response.results:
    print(f"{result.model}: {result.data['name']} (score: {result.score})")
```

### Autocomplete
```python
suggestions = search_service.get_suggestions(
    query="john",
    field="name",
    limit=10
)
print(suggestions)
```

### Health Check
```python
health = search_service.health_check()
print(f"Status: {health['status']}")
```

### Backend Switching
```python
# Switch to external backend
search_service.switch_backend('external')

# Or initialize with specific backend
search_service = SearchService(backend_name='postgres')
```

## Management Commands

### Rebuild Indexes
```bash
# Rebuild all indexes
python manage.py search_index rebuild

# Rebuild specific models
python manage.py search_index rebuild --models Account Contact

# Use specific backend
python manage.py search_index rebuild --backend external
```

### Check Health
```bash
python manage.py search_index health
```

### Show Info
```bash
python manage.py search_index info
```

## Configuration

### settings.py
```python
# Backend selection
SEARCH_BACKEND = 'postgres'  # or 'external'

SEARCH_CONFIG = {
    'backend': {
        'engine': 'meilisearch',  # For external backend
        'host': 'http://localhost:7700',
        'api_key': 'your_api_key',
        'index_prefix': 'crm_',
    },
    'scoring': {
        'field_weights': {
            'name': 10.0,
            'email': 8.0,
            'phone': 5.0,
            'company': 7.0,
            'title': 6.0,
        },
        'exact_match_boost': 2.0,
        'recent_record_boost': 1.2,
    },
    'gdpr': {
        'mask_pii': True,
        'remove_pii': False,
        'mask_phi': True,
        'allowed_roles': ['admin', 'compliance'],
    }
}
```

### Environment Variables
```bash
# Backend selection
export SEARCH_BACKEND=postgres

# External engine (if using external backend)
export SEARCH_ENGINE=meilisearch
export SEARCH_HOST=http://localhost:7700
export SEARCH_API_KEY=your_api_key

# GDPR settings
export SEARCH_MASK_PII=True
export SEARCH_REMOVE_PII=False
```

## Error Handling

### Common Errors

**400 Bad Request**
```json
{
  "error": "Invalid request",
  "details": {
    "query": ["This field is required."]
  }
}
```

**401 Unauthorized**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**500 Internal Server Error**
```json
{
  "error": "Search failed",
  "details": "Connection to search backend failed"
}
```

## Rate Limits

- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour
- Autocomplete endpoint: Cached for 5 minutes

## Search Features

### Supported Models
- Account (crm_account)
- Contact (crm_contact)
- Lead (crm_lead)
- Deal (deals_deal)

### Search Types
- **Fuzzy**: Typo-tolerant using trigram similarity
- **Exact**: Case-insensitive exact match
- **Cross-model**: Search across multiple models simultaneously

### Filters
- `is_active`: Boolean
- `status`: String
- `type`: String
- `owner_id`: UUID
- Custom filters based on model fields

### GDPR Masking

**PII Fields:**
- email → `j***@example.com`
- phone → `***-***-4567`
- mobile → `***-***-4567`
- ssn → `***-**-****`

**PHI Fields:**
- Completely removed unless user has permission

**Address Fields:**
- `123 Main St, City, State` → `City, State`

### Scoring Factors
1. Field weights (configurable)
2. Exact match boost (2x)
3. Prefix match boost (1.5x)
4. Recent record boost (1.2x)
5. Active record boost (1.1x)
6. Edit distance penalty

## Performance Tips

1. **Use Filters**: Reduce result set with filters
2. **Limit Results**: Use `max_results` parameter
3. **Cache Autocomplete**: Results cached for 5 minutes
4. **Specific Models**: Search specific models instead of all
5. **Fuzzy Toggle**: Disable fuzzy for faster exact matches

## Migration

### From Direct Queries
```python
# Before
accounts = Account.objects.filter(name__icontains=query)

# After
response = search_service.search(
    query_string=query,
    company_id=company_id,
    models=['Account']
)
accounts = [r.data for r in response.results]
```

### To External Engine
```python
# 1. Deploy external engine (e.g., Meilisearch)
docker run -p 7700:7700 getmeili/meilisearch:latest

# 2. Update settings.py
SEARCH_BACKEND = 'external'
SEARCH_CONFIG['backend'] = {
    'engine': 'meilisearch',
    'host': 'http://localhost:7700',
    'api_key': 'your_api_key'
}

# 3. Rebuild indexes
python manage.py search_index rebuild

# 4. Test
python manage.py search_index health
```

## Troubleshooting

### Slow Searches
```bash
# Check indexes
python manage.py search_index health

# Analyze tables
python manage.py dbshell
ANALYZE crm_account;
ANALYZE crm_contact;
```

### Backend Connection Issues
```bash
# Check health
python manage.py search_index health

# Test connection
curl http://localhost:7700/health  # For Meilisearch
```

### Missing Results
1. Verify data is indexed
2. Check company isolation
3. Review GDPR filtering
4. Check `is_active` filter

## Support

- Documentation: `/core/search/README.md`
- Evolution: `/SEARCH_EVOLUTION.md`
- Tests: `/tests/test_search.py`
- Management: `python manage.py search_index --help`

## Version History

- **v1.0** (Wave 1): PostgreSQL backend, fuzzy search, GDPR filtering
- **v2.0** (Wave 2 - Planned): Semantic search, NLP queries
- **v3.0** (Wave 3 - Planned): AI ranking, voice search
- **v4.0** (Wave 4 - Planned): Multi-datacenter, federation
