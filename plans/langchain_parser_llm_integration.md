# LangChain Parser LLM Integration Plan

## Overview

This document specifies the integration of a LangChain-based "parser LLM" into the Simple Text2SQL service. The parser LLM will process SQL query results and generate natural language responses that directly answer user questions.

## Architecture

### Current Flow (Before)
```
User Query → SQL Generator LLM → SQL Query → Database Execution → Raw Results
```

### Enhanced Flow (After)
```
User Query → SQL Generator LLM → SQL Query → Database Execution → Raw Results
                                                                          ↓
                                                Parser LLM ← (Query + SQL + Results)
                                                     ↓
                                        Natural Language Response
```

## Components

### 1. Dependencies
- **langchain**: Core LangChain framework
- **langchain-aws**: AWS Bedrock integration for LangChain

### 2. Parser LLM Implementation

**Location:** `backend/app/services/simple_text2sql.py`

**New Method:** `parse_results_to_text()`
```python
def parse_results_to_text(
    self,
    user_query: str,
    sql_query: str,
    execution_result: Dict
) -> str:
    """
    Parse SQL execution results into natural language response

    Args:
        user_query: Original user question in natural language
        sql_query: Generated SQL query that was executed
        execution_result: Dictionary containing query results

    Returns:
        Natural language response answering the user's question
    """
```

**Implementation Details:**
- Uses `ChatBedrock` from `langchain-aws` to connect to AWS Bedrock
- Uses same model configuration as SQL generator (Claude via Bedrock)
- Implements prompt template for consistent result parsing
- Handles empty results, errors, and large result sets appropriately

### 3. Prompt Design for Parser LLM

**System Prompt:**
```
You are a helpful data analyst assistant. Your job is to analyze SQL query results
and provide clear, concise answers to user questions in natural language.

Rules:
1. Provide direct answers based on the data shown
2. Use specific numbers, names, and facts from the results
3. If results are empty, clearly state that no data was found
4. Format numbers appropriately (e.g., add commas, units)
5. Keep responses concise but informative
6. Do not make assumptions beyond what the data shows
```

**User Prompt Template:**
```
User Question: {user_query}

SQL Query Executed:
{sql_query}

Query Results:
{formatted_results}

Please provide a natural language answer to the user's question based on these results.
```

### 4. Response Schema Update

**File:** `backend/app/models/schemas.py`

**Changes:**
```python
class Text2SQLResponse(BaseModel):
    sql: str
    method: str
    # ... existing fields ...
    parsed_response: Optional[str] = Field(
        None,
        description="Natural language response from parser LLM"
    )
```

### 5. API Endpoint Update

**File:** `backend/app/routes/text2sql.py`

**Endpoint:** `POST /api/text2sql/simple`

**Updated Logic:**
1. Generate SQL query (existing)
2. If `execute=True`:
   - Execute SQL query (existing)
   - Call `parse_results_to_text()` with query, SQL, and results (new)
   - Include `parsed_response` in response (new)

## Example Request/Response Flows

### Example 1: Successful Query with Results

**Request:**
```json
{
  "query": "How many operational nuclear power plants are there?",
  "execute": true
}
```

**Response:**
```json
{
  "sql": "SELECT COUNT(*) as count FROM nuclear_power_plants WHERE StatusId = 3 LIMIT 100",
  "method": "simple",
  "execution_result": {
    "success": true,
    "data": [{"count": 437}],
    "row_count": 1
  },
  "parsed_response": "There are 437 operational nuclear power plants in the database."
}
```

### Example 2: Query with Multiple Rows

**Request:**
```json
{
  "query": "What are the top 5 countries by number of nuclear plants?",
  "execute": true
}
```

**Response:**
```json
{
  "sql": "SELECT c.name, COUNT(*) as plant_count FROM nuclear_power_plants npp JOIN countries c ON npp.CountryCode = c.id GROUP BY c.name ORDER BY plant_count DESC LIMIT 5",
  "method": "simple",
  "execution_result": {
    "success": true,
    "data": [
      {"name": "United States", "plant_count": 93},
      {"name": "France", "plant_count": 56},
      {"name": "China", "plant_count": 55},
      {"name": "Russia", "plant_count": 38},
      {"name": "Japan", "plant_count": 33}
    ],
    "row_count": 5
  },
  "parsed_response": "The top 5 countries by number of nuclear power plants are:\n1. United States with 93 plants\n2. France with 56 plants\n3. China with 55 plants\n4. Russia with 38 plants\n5. Japan with 33 plants"
}
```

### Example 3: Query with No Results

**Request:**
```json
{
  "query": "Show me plants with capacity over 10000 MW",
  "execute": true
}
```

**Response:**
```json
{
  "sql": "SELECT * FROM nuclear_power_plants WHERE Capacity > 10000 LIMIT 100",
  "method": "simple",
  "execution_result": {
    "success": true,
    "data": [],
    "row_count": 0
  },
  "parsed_response": "No nuclear power plants were found with a capacity over 10,000 MW. This is because individual nuclear power plant units typically have capacities ranging from 300 to 1,600 MW."
}
```

### Example 4: Query Execution Error

**Request:**
```json
{
  "query": "Show me all plants",
  "execute": true
}
```

**Response:**
```json
{
  "sql": "SELECT * FROM nuclear_power_plants LIMIT 100",
  "method": "simple",
  "execution_result": {
    "success": false,
    "error": "Table 'nuclear_power_plants' doesn't exist"
  },
  "parsed_response": "I encountered an error while executing the query: Table 'nuclear_power_plants' doesn't exist. Please check the database connection and table names."
}
```

## Configuration Options

### Parser LLM Settings
- **Model:** Same as SQL generator (configured via `BEDROCK_MODEL_ID`)
- **Max Tokens:** 1000 (sufficient for natural language responses)
- **Temperature:** 0.3 (slightly higher than SQL generation for more natural language)

### Result Formatting
- **Max Rows to Display:** 100 (to avoid token limit issues)
- **Truncation Message:** If results exceed max rows, inform user
- **Number Formatting:** Add thousand separators for readability

## Error Handling

### Parser LLM Failures
- If parser LLM fails, return `parsed_response: null`
- Log error for debugging
- Still return SQL and execution results
- Do not block the entire request

### Empty Results
- Parser LLM should provide helpful context
- Explain possible reasons (e.g., filters too restrictive)
- Suggest alternative queries if appropriate

### Large Result Sets
- Truncate results before sending to parser LLM
- Inform parser LLM that results are truncated
- Parser LLM should mention truncation in response

## Implementation Phases

### Phase 1: Core Integration (Current)
- Add LangChain dependencies
- Implement `parse_results_to_text()` method
- Update response schema
- Update `/simple` endpoint

### Phase 2: Future Enhancements
- Add parser LLM to other text2sql variants (advanced, chat, agentic)
- Implement caching for similar queries
- Add configuration to enable/disable parser LLM
- Support different output formats (bullet points, tables, paragraphs)

## Testing Strategy

### Unit Tests
- Test `parse_results_to_text()` with various result types
- Test empty results handling
- Test error result handling
- Test large result sets

### Integration Tests
- Test end-to-end flow from query to parsed response
- Test with real database connections
- Test parser LLM prompt variations

### Performance Testing
- Measure latency impact of parser LLM
- Test with concurrent requests
- Monitor token usage

## Performance Considerations

### Latency
- Parser LLM adds ~1-3 seconds to response time
- Consider async processing for long queries
- Implement timeout handling

### Token Usage
- Monitor tokens used for result parsing
- Implement smart truncation for large results
- Consider cost implications for high-volume usage

### Caching
- Cache parsed responses for identical queries
- Use query + results hash as cache key
- Set reasonable TTL (e.g., 1 hour)

## Security Considerations

- Sanitize SQL results before sending to parser LLM
- Do not expose sensitive error messages
- Validate result sizes before processing
- Implement rate limiting to prevent abuse

## Success Metrics

- Response quality: User satisfaction with natural language answers
- Accuracy: Correctness of interpreted results
- Performance: Latency impact on overall request time
- Token efficiency: Tokens used per request
- Error rate: Failures in parser LLM processing

## Rollout Plan

1. Deploy to development environment
2. Test with sample queries
3. Gather internal feedback
4. Deploy to staging with monitoring
5. Gradual rollout to production
6. Monitor metrics and iterate

## Documentation Updates

- Update API documentation with `parsed_response` field
- Add examples to README
- Document configuration options
- Create troubleshooting guide
