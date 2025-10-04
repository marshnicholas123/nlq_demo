# Phoenix Observability Guide

This application is instrumented with [Arize Phoenix](https://github.com/Arize-ai/phoenix) for comprehensive LLM tracing and observability.

## Overview

Phoenix provides complete visibility into:
- **LLM calls**: All AWS Bedrock Claude invocations for SQL generation and natural language result parsing (prompts, responses, latency, token usage)
- **Business logic**: BM25 retrieval, SQL generation, database operations, conversation tracking, agent tool execution
- **Performance**: End-to-end latency, token consumption, error rates

All 4 Text2SQL service variants are fully instrumented:
1. **Simple**: Schema-based SQL generation
2. **Advanced**: BM25 metadata retrieval + SQL generation
3. **Chat**: Conversation context + follow-up query handling
4. **Agentic**: Tool-based iterative refinement with validation

## Quick Start

### 1. Install Dependencies

Dependencies are already in `requirements.txt`. Install with:

```bash
pip install -r requirements.txt
```

Key Phoenix packages:
- `arize-phoenix>=4.0.0` - Core Phoenix library
- `openinference-instrumentation-bedrock>=0.1.0` - AWS Bedrock auto-instrumentation (for SQL generation and result parsing)
- `openinference-instrumentation-langchain>=0.1.0` - LangChain auto-instrumentation (legacy, may be removed in future)
- `opentelemetry-exporter-otlp>=1.20.0` - OpenTelemetry protocol support

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Phoenix Observability Settings (optional - defaults shown)
PHOENIX_ENABLED=true                    # Enable/disable Phoenix tracing
PHOENIX_PROJECT_NAME=text2sql-app       # Project name for trace organization
PHOENIX_ENDPOINT=                       # Leave empty for local, or set remote OTLP endpoint
PHOENIX_LAUNCH_APP=false                # Set to true to auto-launch Phoenix UI (local dev only)
```

### 3. Run Phoenix Locally (Recommended for Development)

In a separate terminal, launch the Phoenix server:

```bash
python -m phoenix.server.main serve
```

Phoenix UI will be available at: **http://127.0.0.1:6006**

Alternatively, set `PHOENIX_LAUNCH_APP=true` in your `.env` to auto-launch Phoenix when the API starts.

### 4. Start the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. View Traces

1. Open Phoenix UI at http://127.0.0.1:6006
2. Make API requests to any Text2SQL endpoint:
   - `POST /api/text2sql/simple`
   - `POST /api/text2sql/advanced`
   - `POST /api/text2sql/chat`
   - `POST /api/text2sql/agentic`
3. Watch traces appear in real-time in the Phoenix dashboard

## What Gets Traced

### Automatic Instrumentation (via OpenInference)

#### AWS Bedrock
All `client.invoke_model()` calls are automatically traced with:
- Model ID
- Input prompts and system messages
- Response text
- Token usage (input/output tokens)
- Latency
- Stop reason
- Errors and exceptions

This includes both:
- **SQL Generation**: Converting natural language queries to SQL
- **Result Parsing**: Converting SQL results to natural language responses

### Custom Spans

We've added custom OpenTelemetry spans for business logic visibility:

#### Simple Text2SQL (`simple_text2sql.py`)
- `simple_text2sql.generate_sql`: SQL generation workflow
- `simple_text2sql.execute_query`: Database query execution
- `simple_text2sql.parse_results`: LLM-based result parsing

**Attributes tracked:**
- User query
- Generated SQL
- Row count
- Success/error status
- Response length

#### Advanced Text2SQL (`advanced_text2sql.py`)
Inherits all Simple spans, plus:
- `advanced_text2sql.bm25_retrieval`: Metadata search using BM25
- `advanced_text2sql.get_sample_data`: Sample data fetching
- `advanced_text2sql.generate_sql`: Enhanced SQL generation

**Attributes tracked:**
- Retrieved document count
- Retrieved sections
- Tables mentioned
- Context sections used

#### Chat Text2SQL (`chat_text2sql.py`)
Inherits all Advanced spans, plus:
- `chat_text2sql.generate_sql_with_context`: Conversational SQL generation

**Attributes tracked:**
- Session ID
- Chat history length
- Is follow-up query
- Resolved query (if modified by context)

#### Agentic Text2SQL (`agentic_text2sql.py`)
Inherits all Advanced spans, plus:
- `agentic_text2sql.generate_sql_with_agent`: Agent orchestration
- `agentic_text2sql.iteration_{N}`: Each agent iteration
- `agentic_text2sql.tool.{tool_name}`: Individual tool executions

**Attributes tracked:**
- Total iterations
- Total tool calls
- Planned actions per iteration
- Tool parameters and results
- Agent completion status

Available tools traced:
- `get_schema`: Database schema retrieval
- `get_sample_data`: Sample data fetching
- `search_metadata`: BM25 metadata search
- `execute_sql`: SQL execution
- `validate_results`: Result validation

## Viewing Traces in Phoenix

### Trace Timeline View
- See the complete execution flow of each request
- Visualize parent-child relationships between spans
- Identify performance bottlenecks
- Track token consumption across LLM calls

### Span Details
Each span shows:
- Duration
- Attributes (all custom metadata we set)
- Input/output data (for LLM calls)
- Errors and exceptions
- Token counts

### Filtering and Search
- Filter by service (simple, advanced, chat, agentic)
- Search by user query
- Filter by error status
- Filter by session ID (for chat)

### Performance Analysis
- Latency percentiles (p50, p95, p99)
- Total token usage over time
- Error rates
- Slowest traces

## Advanced Configuration

### Using Remote Phoenix (Production)

To send traces to a remote Phoenix instance:

```bash
PHOENIX_ENABLED=true
PHOENIX_PROJECT_NAME=text2sql-production
PHOENIX_ENDPOINT=https://your-phoenix-instance.com/v1/traces
PHOENIX_LAUNCH_APP=false
```

### Disabling Phoenix

To disable tracing (e.g., for testing):

```bash
PHOENIX_ENABLED=false
```

The application will run normally without any observability overhead.

### Checking Phoenix Status

GET `/phoenix` endpoint returns:

```json
{
  "enabled": true,
  "initialized": true,
  "project_name": "text2sql-app",
  "endpoint": "local (http://127.0.0.1:6006)"
}
```

## Troubleshooting

### Phoenix Not Showing Traces

1. **Check Phoenix is running**:
   ```bash
   curl http://127.0.0.1:6006/healthz
   ```

2. **Check configuration**:
   - Visit `GET /phoenix` to see status
   - Ensure `PHOENIX_ENABLED=true`

3. **Check logs**:
   Application startup logs will show:
   ```
   INFO: Initializing Phoenix observability...
   INFO: Instrumenting AWS Bedrock...
   INFO: Phoenix observability initialized successfully
   ```

### Performance Impact

Phoenix adds minimal overhead:
- ~1-5ms per span creation
- Traces are sent asynchronously
- No blocking operations

For production, monitor:
- Trace export latency
- Memory usage (traces buffered before export)

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'openinference'`
**Solution**: Reinstall dependencies: `pip install -r requirements.txt`

**Issue**: Traces not appearing in Phoenix UI
**Solution**:
- Ensure Phoenix server is running on port 6006
- Check `PHOENIX_ENDPOINT` is correct or empty for local
- Verify firewall allows connections to Phoenix

**Issue**: High memory usage
**Solution**:
- Reduce trace retention in Phoenix settings
- Use remote Phoenix instance instead of local
- Set up trace sampling for high-traffic scenarios

## Best Practices

### Development
- Run Phoenix locally with `PHOENIX_LAUNCH_APP=true`
- Use the Phoenix UI to debug LLM prompts and responses
- Check trace attributes to understand agent decision-making

### Production
- Use a dedicated Phoenix instance or cloud service
- Set up alerting on error rates and latency
- Monitor token usage trends
- Use trace sampling if request volume is very high (>1000 req/min)

### Debugging LLM Issues

1. **Find problematic traces**: Filter by error status or high latency
2. **Inspect LLM spans**: View exact prompts and responses for both SQL generation and result parsing
3. **Check attributes**: See user queries, SQL generated, context used
4. **Follow execution flow**: Trace parent-child relationships to find root cause

### Token Optimization

1. **Track token usage**: Phoenix shows input/output tokens for all Bedrock LLM calls (SQL generation + result parsing)
2. **Compare methods**: See which Text2SQL variant uses more tokens
3. **Optimize prompts**: Reduce system prompt length if tokens are high
4. **Monitor trends**: Track token usage over time

## Integration with Other Tools

Phoenix exports traces using **OpenTelemetry Protocol (OTLP)**, making it compatible with:
- Jaeger
- Zipkin
- Grafana Tempo
- AWS X-Ray
- Google Cloud Trace
- Datadog APM

To send traces to these tools, set `PHOENIX_ENDPOINT` to their OTLP endpoint.

## Additional Resources

- [Phoenix Documentation](https://docs.arize.com/phoenix)
- [AWS Bedrock Tracing Guide](https://docs.arize.com/phoenix/tracing/integrations-tracing/bedrock)
- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/instrumentation/python/)

## Support

For issues with Phoenix:
- GitHub: https://github.com/Arize-ai/phoenix/issues
- Community Slack: https://arize-ai.slack.com

For issues with this application's instrumentation:
- Check application logs for Phoenix initialization errors
- Verify all environment variables are set correctly
- Review custom span code in service files
