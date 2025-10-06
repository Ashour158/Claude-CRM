# Deals Kanban Design

## Overview

The Deals Kanban provides a visual board interface for managing sales pipeline with drag-and-drop functionality, stage management, and WIP limits.

## Architecture

### Components

1. **Pipeline**: Container for stages
2. **PipelineStage**: Individual stages in the pipeline
3. **Deal**: Cards on the board
4. **Board Endpoint**: Retrieves stage-organized deals
5. **Move Endpoint**: Handles deal movement between stages

## Data Models

### Pipeline

```python
{
  "id": "uuid",
  "name": "Standard Sales Pipeline",
  "description": "Default sales process",
  "is_default": true,
  "is_active": true,
  "company": "company_id",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### PipelineStage

```python
{
  "id": "uuid",
  "pipeline": "pipeline_id",
  "name": "Qualification",
  "description": "Qualify the opportunity",
  "sequence": 2,
  "probability": 25,
  "is_closed": false,
  "is_won": false,
  "wip_limit": 10,  # Optional work-in-progress limit
  "is_active": true,
  "company": "company_id"
}
```

## API Endpoints

### Get Board View

```
GET /api/deals/board/?pipeline_id={id}
```

**Query Parameters:**
- `pipeline_id` (optional): Specific pipeline ID, defaults to default pipeline

**Response:**

```json
{
  "pipeline": {
    "id": "uuid",
    "name": "Standard Sales Pipeline"
  },
  "stages": [
    {
      "id": "uuid",
      "name": "Prospecting",
      "sequence": 1,
      "probability": 10,
      "wip_limit": null,
      "deal_count": 5,
      "deals": [
        {
          "id": "uuid",
          "name": "Acme Corp Deal",
          "amount": "50000.00",
          "account": "Acme Corporation",
          "owner": "John Doe",
          "expected_close_date": "2024-03-15"
        }
      ]
    },
    {
      "id": "uuid",
      "name": "Qualification",
      "sequence": 2,
      "probability": 25,
      "wip_limit": 10,
      "deal_count": 8,
      "deals": [...]
    }
  ]
}
```

### Move Deal

```
POST /api/deals/move/
```

**Request Body:**

```json
{
  "deal_id": "uuid",
  "to_stage_id": "uuid",
  "position": 0  # Optional: position in the new stage
}
```

**Response (Success):**

```json
{
  "message": "Deal moved successfully",
  "deal_id": "uuid",
  "new_stage": "qualification",
  "new_probability": 25
}
```

**Response (WIP Limit Warning):**

```json
{
  "warning": "Stage WIP limit (10) reached",
  "current_count": 10,
  "can_proceed": false
}
```

Status Code: `200 OK`

## Stage Configuration

### Standard Pipeline Stages

| Stage | Sequence | Probability | Closed | Won |
|-------|----------|-------------|--------|-----|
| Prospecting | 1 | 10% | No | No |
| Qualification | 2 | 25% | No | No |
| Proposal | 3 | 50% | No | No |
| Negotiation | 4 | 75% | No | No |
| Closed Won | 5 | 100% | Yes | Yes |
| Closed Lost | 6 | 0% | Yes | No |

### Configuring Stages

Stages can be customized per pipeline:

```python
# Example: Create a custom pipeline with stages
pipeline = Pipeline.objects.create(
    company=company,
    name="Enterprise Sales",
    is_default=False
)

# Add stages
PipelineStage.objects.create(
    pipeline=pipeline,
    company=company,
    name="Discovery",
    sequence=1,
    probability=10,
    wip_limit=5
)

PipelineStage.objects.create(
    pipeline=pipeline,
    company=company,
    name="Technical Review",
    sequence=2,
    probability=30,
    wip_limit=8
)
```

## WIP (Work In Progress) Limits

### Purpose

WIP limits prevent bottlenecks by restricting the number of deals in a stage.

### Behavior

- **Warning Only**: When limit is reached, the API returns a warning but allows the move
- **Optional**: Can be set to `null` to disable
- **Per Stage**: Each stage can have its own limit

### Example

```python
# Stage with WIP limit of 10
stage = PipelineStage.objects.get(name="Qualification")
stage.wip_limit = 10
stage.save()

# When moving a deal:
current_count = Deal.objects.filter(
    stage=stage.name,
    status='open'
).count()

if current_count >= stage.wip_limit:
    # Return warning
    return {
        'warning': f'Stage WIP limit ({stage.wip_limit}) reached',
        'can_proceed': False
    }
```

## Timeline Events

When a deal moves between stages, a timeline event is created:

```json
{
  "event_type": "stage_change",
  "deal_id": "uuid",
  "old_stage": "prospecting",
  "new_stage": "qualification",
  "user": "user_id",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Race Condition Prevention

The move endpoint uses database locking to prevent race conditions:

```python
with transaction.atomic():
    # Lock the deal row
    deal = Deal.objects.select_for_update().get(id=deal_id)
    
    # Update stage
    deal.stage = new_stage
    deal.save()
```

## Performance Optimization

### Prefetching

The board endpoint uses `select_related` and `prefetch_related` to minimize queries:

```python
stages = PipelineStage.objects.filter(
    pipeline=pipeline
).prefetch_related(
    Prefetch(
        'deals',
        queryset=Deal.objects.select_related('account', 'owner')
    )
).order_by('sequence')
```

### Pagination

- Maximum 20 deals per stage in board view
- Full list available via standard deals list endpoint
- Use query parameters to adjust limits

## Frontend Integration

### Example: React Kanban Board

```jsx
function KanbanBoard() {
  const [board, setBoard] = useState(null);
  
  useEffect(() => {
    fetchBoard();
  }, []);
  
  const fetchBoard = async () => {
    const response = await api.get('/api/deals/board/');
    setBoard(response.data);
  };
  
  const moveDeal = async (dealId, toStageId) => {
    await api.post('/api/deals/move/', {
      deal_id: dealId,
      to_stage_id: toStageId
    });
    fetchBoard(); // Refresh board
  };
  
  return (
    <div className="kanban-board">
      {board?.stages.map(stage => (
        <Stage
          key={stage.id}
          stage={stage}
          onMoveDeal={moveDeal}
        />
      ))}
    </div>
  );
}
```

## Best Practices

1. **Stage Naming**: Use clear, action-oriented stage names
2. **Probability Alignment**: Set realistic probabilities based on historical data
3. **WIP Limits**: Start conservative, adjust based on team capacity
4. **Regular Reviews**: Review pipeline health weekly
5. **Stage Transitions**: Document required criteria for moving between stages
6. **Automation**: Use workflow rules to auto-move deals when criteria are met

## Metrics & Analytics

### Key Metrics

- **Conversion Rate**: % of deals moving from one stage to the next
- **Average Time in Stage**: Days spent in each stage
- **Win Rate**: % of deals reaching "Closed Won"
- **Pipeline Value**: Total value of open deals per stage
- **Weighted Pipeline**: Sum of (deal amount × probability)

### Example Query

```python
from django.db.models import Sum, Count, Avg

# Pipeline value by stage
pipeline_value = Deal.objects.filter(
    company=company,
    status='open'
).values('stage').annotate(
    total_value=Sum('amount'),
    deal_count=Count('id'),
    avg_deal_size=Avg('amount')
)
```

## Future Enhancements

- Drag-and-drop position persistence
- Stage-level automation rules
- Forecasting with confidence intervals
- Stage duration tracking
- Deal aging alerts
- Collaborative features (mentions, comments)
- Mobile-optimized board view
- Customizable card layouts
