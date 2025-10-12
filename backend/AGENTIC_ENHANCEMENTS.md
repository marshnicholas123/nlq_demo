# Agentic Text2SQL Enhancements

## Overview

The `AgenticText2SQLService` has been significantly enhanced to include all features from `ChatText2SQLService` plus advanced agentic capabilities including reflection and user clarification.

## Key Features

### 1. **Session Management & Conversation Context**
- Maintains conversation history (last 10 turns per session)
- Automatically resolves follow-up queries using context
- Detects patterns like "what about", "how about", "show me"
- Session-based state tracking (use Redis in production)

### 2. **Hybrid Retrieval (Vector + BM25)**
- Combines vector embeddings and keyword matching
- Retrieves relevant table schemas using both approaches
- Deduplicates and prioritizes BM25 results
- Integrates business rules using hybrid retrieval

### 3. **LangGraph State Machine Orchestration**
- Structured workflow with explicit states and transitions
- Nodes: `detect_clarification` → `plan` → `execute_tools` → `generate_sql` → `reflect` → `complete`
- Conditional edges for dynamic routing
- Iterative refinement with max iteration limits

### 4. **Reflection & Self-Correction**
- Automatically evaluates generated SQL quality
- Checks for syntax errors, proper JOINs, business rule application
- Returns confidence scores and identified issues
- Triggers refinement if quality is insufficient
- Prevents infinite loops with iteration limits

### 5. **Clarification Detection**
- LLM-powered ambiguity detection before SQL generation
- Identifies queries with multiple valid interpretations
- Detects missing critical context (dates, entities, metrics)
- Returns specific clarifying questions to the user
- Only requests clarification when absolutely necessary

### 6. **Enhanced Tool System**
- **get_schema**: Hybrid retrieval for relevant schemas
- **search_metadata**: Business rules via hybrid search
- **get_sample_data**: BM25-based relevant sample rows
- **execute_sql**: Query execution with tracing
- **validate_results**: Multi-criteria validation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │  Detect Clarification  │
           └───────────┬────────────┘
                       │
              ┌────────┴────────┐
              │                 │
         [Clarify]         [Proceed]
              │                 │
              ▼                 ▼
         Return Q's        ┌───────┐
                          │  Plan  │◄────────────┐
                          └───┬────┘             │
                              │                  │
                 ┌────────────┼──────────────┐   │
                 │            │              │   │
            [Execute      [Generate]    [Complete] │
             Tools]           │              │   │
                 │            ▼              ▼   │
                 ▼      ┌──────────┐      END   │
            Execute     │ Generate │            │
             Tools      │   SQL    │            │
                 │      └────┬─────┘            │
                 └───────►   │                  │
                             ▼                  │
                       ┌──────────┐             │
                       │ Reflect  │             │
                       └────┬─────┘             │
                            │                   │
                   ┌────────┴────────┐          │
                   │                 │          │
              [Refine]          [Complete]      │
                   │                 │          │
                   └─────────────────┴──────────┘
```

## Usage Examples

### Basic Query with Reflection

```python
from app.services.agentic_text2sql import AgenticText2SQLService
import uuid

service = AgenticText2SQLService()
session_id = str(uuid.uuid4())

result = service.generate_sql_with_agent(
    user_query="How many operational nuclear plants are in Asia?",
    session_id=session_id,
    max_iterations=3
)

print(result['sql'])
print(result['reflection'])  # Quality metrics
print(result['iterations'])   # Number of refinements
```

### Follow-up Queries with Context

```python
# First query
result1 = service.generate_sql_with_agent(
    user_query="List nuclear power plants in France",
    session_id=session_id
)

# Follow-up automatically uses context
result2 = service.generate_sql_with_agent(
    user_query="How many reactors do they have?",  # Resolves "they" to France
    session_id=session_id
)

print(result2['resolved_query'])  # Shows full resolved query
```

### Handling Clarification Requests

```python
result = service.generate_sql_with_agent(
    user_query="Show me the data",  # Ambiguous
    session_id=session_id
)

if result.get('needs_clarification'):
    print("Clarifying questions:")
    for question in result['questions']:
        print(f"  - {question}")
    # User provides more context...
```

### Clearing Session History

```python
service.clear_history(session_id)
```

## Response Format

### Success Response
```python
{
    "success": True,
    "sql": "SELECT ...",
    "method": "agentic_hybrid",
    "session_id": "uuid-string",
    "resolved_query": "Full resolved query (if follow-up)",
    "iterations": 2,
    "tool_calls": 5,
    "execution_result": {...},
    "validation_result": {...},
    "reflection": {
        "is_acceptable": True,
        "confidence": 0.95,
        "issues": [],
        "should_refine": False
    },
    "context_used": {
        "schema": True,
        "metadata_rules": 3,
        "sample_tables": ["nuclear_power_plants", "countries"]
    }
}
```

### Clarification Response
```python
{
    "success": False,
    "needs_clarification": True,
    "questions": [
        "Which specific data would you like to see?",
        "Are you interested in operational plants or all plants?"
    ],
    "method": "agentic_hybrid",
    "session_id": "uuid-string"
}
```

## Agent State Structure

```python
class AgentState(TypedDict):
    # Core query info
    user_query: str
    session_id: str
    resolved_query: str

    # Conversation context
    chat_history: List[Dict]

    # Iteration tracking
    iteration: int
    max_iterations: int

    # Retrieved context
    schema: Optional[str]
    sample_data: Dict[str, str]
    metadata_context: List[Dict]

    # Generated artifacts
    sql_query: Optional[str]
    execution_result: Optional[Dict]
    validation_result: Optional[Dict]

    # Reflection and clarification
    reflection_result: Optional[Dict]
    clarification_needed: bool
    clarification_questions: List[str]

    # Tool tracking
    tool_calls: List[Dict]

    # Flow control
    next_action: str
    is_complete: bool
    error: Optional[str]
```

## Observability & Tracing

All operations are instrumented with OpenTelemetry:

- **Spans per node**: Each workflow node creates a span
- **Tool execution tracing**: Every tool call is traced
- **Attributes tracked**:
  - User query and resolved query
  - Session ID and history length
  - Iteration count and tool calls
  - Clarification needs and questions
  - Reflection results and confidence
  - Generated SQL and context used

View traces in Arize Phoenix or your OpenTelemetry backend.

## Dependencies

```
langgraph>=0.0.20  # State machine orchestration
langchain==0.1.0   # LLM integrations
opentelemetry      # Observability
```

## Production Considerations

1. **Session Storage**: Replace in-memory `chat_sessions` dict with Redis or database
2. **Rate Limiting**: Add rate limits on clarification detection LLM calls
3. **Caching**: Cache schema retrievals and reflection results
4. **Monitoring**: Set up alerts for high iteration counts or frequent clarifications
5. **Tuning**: Adjust `max_iterations` based on query complexity
6. **Cost**: Monitor LLM usage for reflection and clarification features

## Comparison: Basic vs. Enhanced Agentic

| Feature | Basic Agentic | Enhanced Agentic |
|---------|---------------|------------------|
| Tool usage | ✓ | ✓ |
| Session management | ✗ | ✓ |
| Conversation context | ✗ | ✓ |
| Follow-up resolution | ✗ | ✓ |
| Hybrid retrieval | ✗ | ✓ |
| Business rules | ✗ | ✓ |
| Reflection | ✗ | ✓ |
| Clarification | ✗ | ✓ |
| LangGraph orchestration | ✗ | ✓ |
| State machine | Simple loop | Complex graph |

## Testing

Run the test suite:

```bash
cd backend
python test_agentic_enhanced.py
```

Tests cover:
1. Basic query with agentic approach
2. Follow-up query resolution
3. Clarification detection
4. Multi-turn conversation history
5. Reflection and refinement

## Future Enhancements

- [ ] Multi-agent collaboration (planner + executor + reviewer)
- [ ] User feedback loop for learning
- [ ] Query plan explanation generation
- [ ] Cost-based query optimization
- [ ] Streaming responses for long-running queries
- [ ] A/B testing different reflection strategies
