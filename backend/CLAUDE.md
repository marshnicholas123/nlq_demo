# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the backend API for a Text2SQL demonstration application that converts natural language queries into SQL queries for a nuclear power plant database. The system implements 4 progressive approaches for query generation, from simple schema-based generation to sophisticated agentic systems with tools and conversation context.

## Architecture

The backend is built with FastAPI and implements a service-oriented architecture with the following components:

### Core Application (`app/`)
- `main.py` - FastAPI application setup with CORS and routing
- `config.py` - Pydantic settings for environment configuration
- `database.py` - MySQL connection management

### Services (`app/services/`)
- `bedrock_client.py` - AWS Bedrock integration for Claude LLM
- `simple_text2sql.py` - Basic schema-to-SQL conversion
- `advanced_text2sql.py` - Enhanced with BM25 metadata retrieval
- `chat_text2sql.py` - Conversation context and follow-up handling
- `agentic_text2sql.py` - Tool-based agent with validation

### API Layer (`app/routes/`)
- `text2sql.py` - REST endpoints for all 4 text2sql approaches

### Data Models (`app/models/`)
- `schemas.py` - Pydantic models for request/response validation

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MySQL and AWS credentials

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Configuration
The application connects to MySQL using these environment variables:
- `MYSQL_HOST` - Database host (default: localhost)
- `MYSQL_PORT` - Database port (default: 3306)
- `MYSQL_DATABASE` - Database name
- `MYSQL_USER` - Database username
- `MYSQL_PASSWORD` - Database password

### AWS Bedrock Configuration
Required environment variables:
- `AWS_REGION` - AWS region for Bedrock
- `BEDROCK_MODEL_ID` - Claude model identifier
- `BEDROCK_KB_ID` - Knowledge base ID (for agentic approach)
- `AWS_ACCESS_KEY_ID` - AWS credentials
- `AWS_SECRET_ACCESS_KEY` - AWS credentials

## The 4 Text2SQL Variants

### 1. Simple Text2SQL (`/api/text2sql/simple`)
**Approach:** Schema-only prompting
- Extracts database schema information
- Uses basic prompt engineering with schema context
- Direct SQL generation without metadata
- Uses Bedrock (Claude) for both SQL generation and natural language result parsing

**Usage:**
```python
POST /api/text2sql/simple
{
    "query": "Show me all operational plants",
    "execute": true
}
```

### 2. Advanced Text2SQL (`/api/text2sql/advanced`)
**Approach:** Schema + Sample Data + BM25 Metadata Retrieval
- Builds BM25 index from structured metadata documents
- Retrieves relevant business rules and query patterns
- Includes sample data for better context understanding
- Enhanced prompting with aggregated context

**Key Features:**
- BM25 tokenization and ranking of metadata sections
- Sample data injection (top 3-5 rows per relevant table)
- Business rule application (e.g., StatusId = 3 for operational plants)

### 3. Chat Text2SQL (`/api/text2sql/chat`)
**Approach:** Advanced + Conversation Context
- Extends Advanced approach with session management
- Handles follow-up queries and pronoun resolution
- Maintains conversation history for context
- Query resolution using previous interactions

**Session Management:**
- In-memory storage (use Redis for production)
- Keeps last 10 conversation turns
- Resolves ambiguous references using history

### 4. Agentic Text2SQL (`/api/text2sql/agentic`)
**Approach:** Autonomous tool-based workflow
- Agent controller with planning and execution
- Multiple specialized tools for iterative refinement
- Self-validation and result checking
- Most sophisticated approach with highest accuracy

**Available Tools:**
- `get_schema` - Database structure retrieval
- `get_sample_data` - Sample row fetching
- `search_metadata` - Metadata document search
- `execute_sql` - Query execution
- `validate_results` - Result validation

## API Endpoints

### Core Text2SQL
- `POST /api/text2sql/simple` - Basic conversion
- `POST /api/text2sql/advanced` - Enhanced with metadata
- `POST /api/text2sql/chat` - With conversation context
- `POST /api/text2sql/agentic` - Tool-based agent

### Utilities
- `POST /api/execute` - Direct SQL execution
- `DELETE /api/chat/{session_id}` - Clear chat history
- `GET /api/tools` - List available agent tools
- `GET /health` - Health check endpoint

## Error Handling

All services include proper error handling:
- Database connection errors
- AWS Bedrock API errors
- SQL execution errors
- Validation errors

Errors are returned with appropriate HTTP status codes and descriptive messages.

## Development Notes

- The BM25 metadata index is built from structured documents in `_load_metadata_documents()`
- Sample data is fetched dynamically based on query context
- Chat sessions are stored in memory (consider Redis for production)
- All SQL generation uses MySQL syntax
- The agentic approach can iterate up to 3 times for refinement

## Production Considerations

- Use connection pooling for MySQL
- Implement Redis for chat session storage
- Add proper authentication and rate limiting
- Configure AWS IAM roles instead of access keys
- Set up monitoring and logging
- Consider caching for BM25 metadata index