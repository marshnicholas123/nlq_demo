# Text2SQL Backend API

FastAPI backend for converting natural language queries to SQL for nuclear power plant database.

## Features

- **4 Progressive Text2SQL Approaches**:
  1. Simple: Schema-based generation
  2. Advanced: BM25 retrieval with metadata
  3. Chat: Conversation context awareness
  4. Agentic: Tool-based iterative refinement

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run the application
uvicorn app.main:app --reload
```

## API Endpoints

### Text2SQL Methods

- `POST /api/v1/text2sql/simple` - Simple schema-based conversion
- `POST /api/v1/text2sql/advanced` - Advanced with metadata retrieval
- `POST /api/v1/text2sql/chat` - Chat with conversation context
- `POST /api/v1/text2sql/agentic` - Agentic with tool usage

### Utilities

- `POST /api/v1/execute` - Execute raw SQL
- `DELETE /api/v1/chat/{session_id}` - Clear chat history
- `GET /api/v1/tools` - List available agent tools

## Configuration

Configure via environment variables in `.env`:

- `DATABASE_URL` - Database connection string
- `AWS_REGION` - AWS region for Bedrock
- `BEDROCK_MODEL_ID` - Claude model ID
- AWS credentials for Bedrock access

## Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API documentation
# Visit http://localhost:8000/docs
```