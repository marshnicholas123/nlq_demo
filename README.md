# Text2SQL Application

A comprehensive natural language to SQL query generation system with multiple service implementations and a modern Next.js frontend.

## Features

- **Multiple Service Implementations**:
  - **Simple Text2SQL**: Basic LLM-powered SQL generation
  - **Advanced Text2SQL**: Enhanced with hybrid retrieval (BM25 + Vector search) for business rules
  - **Agentic Text2SQL**: LangGraph-based agentic workflow with clarification detection
  - **Chat Text2SQL**: Conversational interface with session management and context awareness

- **Modern UI**: Next.js frontend with sequential execution, markdown rendering, and real-time results
- **Observability**: Optional Phoenix integration for monitoring and tracing
- **Flexible Database Support**: SQLite (default) with MySQL support available
- **Hybrid Retrieval**: BM25 and vector search for intelligent context retrieval

## Architecture

```
text2sql_ui/
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── services/      # Text2SQL service implementations
│   │   │   ├── simple_text2sql.py
│   │   │   ├── advanced_text2sql.py
│   │   │   ├── agentic_text2sql.py
│   │   │   ├── chat_text2sql.py
│   │   │   └── retrievers/
│   │   ├── api/           # API endpoints
│   │   ├── database.py    # Database connection
│   │   ├── config.py      # Configuration
│   │   └── bedrock_client.py
│   └── tests/
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Next.js pages
│   │   ├── types/         # TypeScript types
│   │   └── utils/         # Utility functions
├── scripts/               # Data loading and indexing scripts
└── data/                  # Sample data and schemas
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- AWS Account with Bedrock access
- AWS credentials configured

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd text2sql_ui
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your AWS credentials and configuration
```

### 3. Database Setup

```bash
# Load sample data (nuclear power plant database)
python scripts/load_data.py

# Build search indices
python scripts/build_bm25_index.py
python scripts/build_sample_data_index.py
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local if needed (default: http://localhost:8000/api)
```

## Running the Application

### Start Backend

```bash
# From project root, with venv activated
cd backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Start Frontend

```bash
# In a new terminal
cd frontend
npm run dev
```

The UI will be available at `http://localhost:3000`

## Environment Variables

### Backend (.env)

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
BEDROCK_MODEL_ID=your_bedrock_model_arn

# Database (SQLite by default, MySQL optional)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=nuclear_power
MYSQL_USER=root
MYSQL_PASSWORD=your_password

# Observability (optional)
PHOENIX_ENABLED=false
PHOENIX_PROJECT_NAME=text2sql-app
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Usage

1. Open the frontend at `http://localhost:3000`
2. Select which services to run (Simple, Advanced, Agentic, Chat)
3. Enter your natural language query (e.g., "Show me all nuclear plants in France")
4. View results with:
   - Generated SQL query
   - Natural language response (with markdown formatting)
   - Query results in table format
   - Metadata and execution statistics

### Example Queries

- "List all nuclear power plants in the United States"
- "What is the total capacity of reactors in France?"
- "Show me plants that started construction after 2000"
- "Which countries have the most nuclear reactors?"

## API Endpoints

- `POST /api/text2sql/simple` - Simple SQL generation
- `POST /api/text2sql/advanced` - Advanced with retrieval
- `POST /api/text2sql/agentic` - Agentic workflow
- `POST /api/text2sql/chat` - Conversational interface
- `GET /api/sessions/{session_id}` - Retrieve session history

## Development

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Development

```bash
cd frontend
npm run dev      # Development server
npm run build    # Production build
npm run lint     # Lint code
```

## Service Comparison

| Feature | Simple | Advanced | Agentic | Chat |
|---------|--------|----------|---------|------|
| LLM Generation | ✓ | ✓ | ✓ | ✓ |
| Business Rules | - | ✓ | ✓ | ✓ |
| Hybrid Retrieval | - | ✓ | ✓ | ✓ |
| Clarification | - | - | ✓ | ✓ |
| Session History | - | - | - | ✓ |
| Natural Language Parsing | - | - | - | ✓ |

## Observability

Optional Phoenix integration for monitoring:

```bash
# Enable in backend/.env
PHOENIX_ENABLED=true
PHOENIX_PROJECT_NAME=text2sql-app

# Phoenix will launch automatically with the backend
# Access UI at http://localhost:6006
```

## Security Notes

- Never commit `.env` files with real credentials
- AWS credentials are stored locally only
- Use IAM roles in production environments
- Database credentials should be rotated regularly

## Troubleshooting

### Backend won't start
- Check AWS credentials are valid
- Ensure database file exists (`nuclear_plants.db`)
- Verify all dependencies are installed

### Frontend can't connect
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify no CORS issues in browser console

### Queries failing
- Check Bedrock model permissions
- Verify database contains data
- Review API logs for errors

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests if applicable
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open a GitHub issue.
