# Text2SQL Workflows: Using Metadata for Query Generation

This document outlines the 4 different approaches for converting natural language to SQL, progressively adding sophistication.

---

## Tab 1: Simple Text2SQL

### Workflow Overview
```
User Query → Extract Schema Only → Prompt LLM → Generate SQL → Execute → Return Results
```

### Architecture
```
┌─────────────────┐
│  User Query     │
│ "Show me all    │
│  operational    │
│  plants in US"  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Schema Extractor                   │
│  - Get table definitions            │
│  - Get column names & types         │
│  - Get foreign key relationships    │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Prompt Builder                     │
│  System: "You are a SQL expert"     │
│  Context: Schema definitions        │
│  User: Natural language query       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  LLM (Claude via Bedrock)           │
│  - Understands schema structure     │
│  - Generates SQL query              │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  SQL Executor                       │
│  - Run query against MySQL          │
│  - Handle errors                    │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Response Formatter                 │
│  - Convert results to JSON          │
│  - Return to frontend               │
└─────────────────────────────────────┘
```

### Implementation

```python
# backend/app/services/simple_text2sql.py

class SimpleText2SQLService:
    def __init__(self, bedrock_client, db_connection):
        self.bedrock = bedrock_client
        self.db = db_connection
    
    def get_schema_context(self) -> str:
        """Extract database schema information"""
        schema = """
        Database Schema:
        
        Table: countries
        - Id (VARCHAR(2), PRIMARY KEY): Country code
        - Name (VARCHAR(255)): Country name
        
        Table: nuclear_power_plant_status_type
        - Id (INT, PRIMARY KEY): Status identifier
        - Type (VARCHAR(50)): Status name
        
        Table: nuclear_reactor_type
        - Id (INT, PRIMARY KEY): Reactor type identifier
        - Type (VARCHAR(20)): Reactor type code
        - Description (VARCHAR(255)): Full reactor type name
        
        Table: nuclear_power_plants
        - Id (INT, PRIMARY KEY): Plant identifier
        - Name (VARCHAR(255)): Plant name
        - Latitude (DECIMAL): Geographic latitude
        - Longitude (DECIMAL): Geographic longitude
        - CountryCode (VARCHAR(2), FOREIGN KEY → countries.Id): Country
        - StatusId (INT, FOREIGN KEY → nuclear_power_plant_status_type.Id): Current status
        - ReactorTypeId (INT, FOREIGN KEY → nuclear_reactor_type.Id): Reactor technology
        - ReactorModel (VARCHAR(100)): Specific reactor model
        - ConstructionStartAt (DATE): Construction start date
        - OperationalFrom (DATE): Operational start date
        - OperationalTo (DATE): Shutdown date (NULL if operational)
        - Capacity (INT): Capacity in megawatts
        - Source (VARCHAR(50)): Data source
        - LastUpdatedAt (DATETIME): Last update timestamp
        
        Relationships:
        - nuclear_power_plants.CountryCode → countries.Id
        - nuclear_power_plants.StatusId → nuclear_power_plant_status_type.Id
        - nuclear_power_plants.ReactorTypeId → nuclear_reactor_type.Id
        """
        return schema
    
    def generate_sql(self, user_query: str) -> dict:
        """Generate SQL from natural language"""
        
        schema_context = self.get_schema_context()
        
        system_prompt = """You are an expert SQL query generator. Generate valid MySQL queries based on the provided schema and user question.

Rules:
1. Return ONLY the SQL query, no explanations
2. Use proper JOIN syntax when accessing related tables
3. Use appropriate WHERE clauses for filtering
4. Limit results to 100 rows by default unless specified
5. Always use table aliases for clarity"""

        user_prompt = f"""Schema:
{schema_context}

User Question: {user_query}

Generate a SQL query to answer this question."""

        # Call Bedrock
        sql_query = self.bedrock.invoke_model(
            prompt=user_prompt,
            system=system_prompt
        )
        
        # Clean up the response (remove markdown, extra text)
        sql_query = self._extract_sql(sql_query)
        
        return {
            "sql": sql_query,
            "method": "simple"
        }
    
    def _extract_sql(self, response: str) -> str:
        """Extract SQL from LLM response"""
        # Remove markdown code blocks
        import re
        pattern = r'```sql\n(.*?)\n```'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
    
    def execute_query(self, sql: str) -> dict:
        """Execute SQL and return results"""
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            
            return {
                "success": True,
                "data": results,
                "row_count": len(results)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

---

## Tab 2: Advanced Text2SQL (Schema + Sample Data + BM25 Retrieval)

### Workflow Overview
```
User Query → BM25 Search Metadata → Retrieve Relevant Context → 
Extract Schema + Sample Data → Prompt LLM → Generate SQL → Execute → Return
```

### Architecture
```
┌─────────────────┐
│  User Query     │
│ "Which countries│
│ are expanding   │
│ nuclear capacity│
│ fastest?"       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  BM25 Retrieval Engine              │
│  - Tokenize user query              │
│  - Search metadata documents        │
│  - Rank by relevance                │
│  - Return top 3-5 relevant sections │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Context Aggregator                 │
│  1. Schema definitions              │
│  2. Sample data (top 5 rows)        │
│  3. Retrieved metadata sections     │
│  4. Business rules                  │
│  5. Example queries from metadata   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Enhanced Prompt Builder            │
│  - Rich context with examples       │
│  - Business terminology mapping     │
│  - Common query patterns            │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  LLM (Claude via Bedrock)           │
│  - Better understanding of intent   │
│  - More accurate SQL generation     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  SQL Executor + Formatter           │
└─────────────────────────────────────┘
```

### Implementation

```python
# backend/app/services/advanced_text2sql.py

from rank_bm25 import BM25Okapi
import re
from typing import List, Dict

class AdvancedText2SQLService:
    def __init__(self, bedrock_client, db_connection):
        self.bedrock = bedrock_client
        self.db = db_connection
        self.metadata_index = None
        self._initialize_bm25_index()
    
    def _initialize_bm25_index(self):
        """Build BM25 index from metadata documents"""
        # Load metadata documents
        metadata_docs = self._load_metadata_documents()
        
        # Tokenize documents
        tokenized_docs = [doc['content'].lower().split() for doc in metadata_docs]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(tokenized_docs)
        self.metadata_docs = metadata_docs
    
    def _load_metadata_documents(self) -> List[Dict]:
        """Load and chunk metadata documents"""
        # In production, this would read from S3 or local files
        # For now, we'll structure it as sections
        
        docs = []
        
        # Countries metadata
        docs.append({
            "table": "countries",
            "section": "overview",
            "content": """Countries table contains ISO 3166-1 alpha-2 country codes.
            Top nuclear nations: US (137 plants), China (91), France (72), Japan (71), Russia (56).
            Use CountryCode for joining with nuclear_power_plants."""
        })
        
        # Status types metadata
        docs.append({
            "table": "nuclear_power_plant_status_type",
            "section": "operational_definition",
            "content": """StatusId = 3 means Operational (currently generating electricity).
            StatusId = 2 means Under Construction (future capacity).
            StatusId = 5 means Shutdown (permanently closed).
            Always filter by StatusId = 3 for current capacity calculations."""
        })
        
        docs.append({
            "table": "nuclear_power_plant_status_type",
            "section": "capacity_analysis",
            "content": """For capacity expansion analysis, use StatusId IN (1, 2) for planned and under construction.
            For retired capacity, use StatusId = 5.
            464 operational plants, 55 under construction, 174 shutdown globally."""
        })
        
        # Reactor types metadata
        docs.append({
            "table": "nuclear_reactor_type",
            "section": "common_types",
            "content": """PWR (Pressurised Water Reactor) is most common worldwide.
            BWR (Boiling Water Reactor) is second most common.
            VVER is Russian PWR variant used in Eastern Europe.
            Advanced reactors include APWR, EPR, ABWR."""
        })
        
        # Nuclear plants metadata
        docs.append({
            "table": "nuclear_power_plants",
            "section": "capacity_queries",
            "content": """To calculate total capacity: SUM(Capacity) WHERE StatusId = 3.
            Average plant size is about 970 MW.
            Capacity ranges from 3 MW to 1,660 MW.
            Always check for NULL in Capacity field."""
        })
        
        docs.append({
            "table": "nuclear_power_plants",
            "section": "geographic_analysis",
            "content": """Use CountryCode to group by country.
            Join with countries table: JOIN countries c ON npp.CountryCode = c.Id.
            Use Latitude and Longitude for mapping.
            Geographic analysis example: GROUP BY CountryCode, ORDER BY COUNT(*) DESC"""
        })
        
        docs.append({
            "table": "nuclear_power_plants",
            "section": "temporal_analysis",
            "content": """OperationalFrom indicates when plant started.
            OperationalTo indicates shutdown date (NULL if still operational).
            ConstructionStartAt shows construction beginning.
            To find new plants: WHERE OperationalFrom >= DATE_SUB(CURDATE(), INTERVAL 5 YEAR).
            To calculate age: YEAR(CURDATE()) - YEAR(OperationalFrom)"""
        })
        
        docs.append({
            "table": "nuclear_power_plants",
            "section": "expansion_queries",
            "content": """Countries expanding nuclear capacity have StatusId = 2 (Under Construction).
            Example query for expansion: SELECT CountryCode, COUNT(*) as under_construction, 
            SUM(Capacity) as future_capacity FROM nuclear_power_plants WHERE StatusId = 2 
            GROUP BY CountryCode ORDER BY future_capacity DESC.
            China has the most plants under construction."""
        })
        
        # Add example queries
        docs.append({
            "table": "nuclear_power_plants",
            "section": "example_top_countries",
            "content": """Example: "Which countries have the most nuclear plants?"
            SQL: SELECT c.Name, COUNT(npp.Id) as plant_count, SUM(npp.Capacity) as total_capacity
            FROM nuclear_power_plants npp JOIN countries c ON npp.CountryCode = c.Id
            WHERE npp.StatusId = 3 GROUP BY c.Id, c.Name ORDER BY plant_count DESC LIMIT 10;"""
        })
        
        return docs
    
    def retrieve_relevant_context(self, query: str, top_k: int = 5) -> List[Dict]:
        """Use BM25 to retrieve relevant metadata sections"""
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        relevant_docs = [self.metadata_docs[i] for i in top_indices if scores[i] > 0]
        
        return relevant_docs
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> str:
        """Get sample rows from table"""
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            results = cursor.fetchall()
            cursor.close()
            
            if not results:
                return ""
            
            # Format as string
            sample_str = f"\nSample data from {table_name}:\n"
            for i, row in enumerate(results, 1):
                sample_str += f"Row {i}: {row}\n"
            
            return sample_str
        except Exception as e:
            return f"Error fetching sample data: {str(e)}"
    
    def generate_sql(self, user_query: str) -> dict:
        """Generate SQL with enhanced context"""
        
        # 1. Retrieve relevant metadata using BM25
        relevant_context = self.retrieve_relevant_context(user_query, top_k=5)
        
        # 2. Get schema
        schema_context = self._get_schema_context()
        
        # 3. Get sample data for relevant tables
        # Determine which tables are likely needed
        tables_mentioned = self._identify_relevant_tables(user_query, relevant_context)
        sample_data = ""
        for table in tables_mentioned:
            sample_data += self.get_sample_data(table, limit=3)
        
        # 4. Build context string from retrieved documents
        metadata_context = "\n\n".join([
            f"Context from {doc['table']} - {doc['section']}:\n{doc['content']}"
            for doc in relevant_context
        ])
        
        # 5. Build enhanced prompt
        system_prompt = """You are an expert SQL query generator specialized in nuclear power plant databases.

Generate valid MySQL queries based on the provided schema, sample data, and business context.

Rules:
1. Return ONLY the SQL query, no explanations
2. Use proper JOIN syntax when accessing related tables
3. Apply business rules from the context (e.g., StatusId = 3 for operational plants)
4. Use appropriate aggregations (SUM, COUNT, AVG) when calculating metrics
5. Always include table aliases for clarity
6. Filter NULL values when appropriate
7. Limit results unless asking for aggregates"""

        user_prompt = f"""Database Schema:
{schema_context}

{sample_data}

Business Context and Best Practices:
{metadata_context}

User Question: {user_query}

Generate a SQL query to answer this question accurately."""

        # Call Bedrock
        sql_query = self.bedrock.invoke_model(
            prompt=user_prompt,
            system=system_prompt
        )
        
        sql_query = self._extract_sql(sql_query)
        
        return {
            "sql": sql_query,
            "method": "advanced",
            "context_used": [doc['section'] for doc in relevant_context]
        }
    
    def _identify_relevant_tables(self, query: str, context: List[Dict]) -> List[str]:
        """Identify which tables are relevant to the query"""
        tables = set()
        
        # Extract from context
        for doc in context:
            tables.add(doc['table'])
        
        # Always include main table for nuclear plants queries
        query_lower = query.lower()
        if any(word in query_lower for word in ['plant', 'reactor', 'capacity', 'operational']):
            tables.add('nuclear_power_plants')
        
        if any(word in query_lower for word in ['country', 'countries', 'nation']):
            tables.add('countries')
        
        if any(word in query_lower for word in ['status', 'operational', 'shutdown', 'construction']):
            tables.add('nuclear_power_plant_status_type')
        
        if any(word in query_lower for word in ['reactor', 'technology', 'pwr', 'bwr', 'type']):
            tables.add('nuclear_reactor_type')
        
        return list(tables)
    
    def _get_schema_context(self) -> str:
        """Get full schema (same as SimpleText2SQL)"""
        # Reuse from simple service
        return SimpleText2SQLService.get_schema_context(self)
    
    def _extract_sql(self, response: str) -> str:
        """Extract SQL from LLM response"""
        import re
        pattern = r'```sql\n(.*?)\n```'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
    
    def execute_query(self, sql: str) -> dict:
        """Execute SQL (same as simple)"""
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            
            return {
                "success": True,
                "data": results,
                "row_count": len(results)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

---

## Tab 3: Advanced Text2SQL + Chat (with Conversation Context)

### Workflow Overview
```
User Query → Retrieve Chat History → BM25 Search → Build Context with History →
Generate SQL → Execute → Store in History → Return
```

### Architecture
```
┌─────────────────┐
│  User Query     │
│ (with session)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Chat History Manager               │
│  - Load previous Q&A from session   │
│  - Extract context and clarifications│
│  - Identify follow-up patterns      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Query Resolver                     │
│  - Resolve pronouns (it, they, them)│
│  - Resolve implicit context         │
│  - Build complete query from history│
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  BM25 Retrieval + Context Building  │
│  (Same as Tab 2)                    │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Enhanced Prompt with Chat Context  │
│  - Previous queries                 │
│  - Previous SQL                     │
│  - Conversation flow                │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  LLM with Conversation Awareness    │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Store in Chat History              │
│  - Query, SQL, Results summary      │
└─────────────────────────────────────┘
```

### Implementation

```python
# backend/app/services/chat_text2sql.py

from typing import List, Dict, Optional
from datetime import datetime

class ChatText2SQLService(AdvancedText2SQLService):
    """Extends Advanced with conversation context"""
    
    def __init__(self, bedrock_client, db_connection):
        super().__init__(bedrock_client, db_connection)
        # In production, use Redis or database for session storage
        self.chat_sessions = {}
    
    def generate_sql_with_context(
        self, 
        user_query: str, 
        session_id: str
    ) -> dict:
        """Generate SQL with conversation context"""
        
        # 1. Get or create chat history
        chat_history = self._get_chat_history(session_id)
        
        # 2. Resolve query with history (handle follow-ups)
        resolved_query = self._resolve_query_with_history(user_query, chat_history)
        
        # 3. Retrieve metadata context (BM25)
        relevant_context = self.retrieve_relevant_context(resolved_query, top_k=5)
        
        # 4. Get schema and sample data
        schema_context = self._get_schema_context()
        tables_mentioned = self._identify_relevant_tables(resolved_query, relevant_context)
        sample_data = ""
        for table in tables_mentioned:
            sample_data += self.get_sample_data(table, limit=3)
        
        # 5. Build metadata context
        metadata_context = "\n\n".join([
            f"Context from {doc['table']} - {doc['section']}:\n{doc['content']}"
            for doc in relevant_context
        ])
        
        # 6. Build conversation context
        conversation_context = self._build_conversation_context(chat_history)
        
        # 7. Enhanced prompt with chat history
        system_prompt = """You are an expert SQL query generator with conversation memory.

You can handle follow-up questions that reference previous queries. Use the conversation 
history to understand context and resolve ambiguous references.

Rules:
1. Return ONLY the SQL query, no explanations
2. Consider previous queries when interpreting follow-ups
3. If user asks "show me more details", expand on the previous query
4. If user says "for China" or "in the US", add that filter to previous context
5. Use proper JOIN syntax and business rules from context
6. Apply StatusId = 3 filter for "operational" or "current" queries"""

        user_prompt = f"""Database Schema:
{schema_context}

{sample_data}

Business Context:
{metadata_context}

{conversation_context}

Current User Question: {user_query}

Generate a SQL query to answer this question."""

        # Call Bedrock
        sql_query = self.bedrock.invoke_model(
            prompt=user_prompt,
            system=system_prompt
        )
        
        sql_query = self._extract_sql(sql_query)
        
        # 8. Store in history before executing
        self._add_to_history(session_id, {
            "user_query": user_query,
            "resolved_query": resolved_query,
            "sql": sql_query,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "sql": sql_query,
            "method": "chat",
            "session_id": session_id,
            "resolved_query": resolved_query if resolved_query != user_query else None,
            "context_used": [doc['section'] for doc in relevant_context]
        }
    
    def _get_chat_history(self, session_id: str) -> List[Dict]:
        """Retrieve chat history for session"""
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = []
        return self.chat_sessions[session_id]
    
    def _add_to_history(self, session_id: str, entry: Dict):
        """Add entry to chat history"""
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = []
        self.chat_sessions[session_id].append(entry)
        
        # Keep only last 10 entries
        if len(self.chat_sessions[session_id]) > 10:
            self.chat_sessions[session_id] = self.chat_sessions[session_id][-10:]
    
    def _resolve_query_with_history(
        self, 
        current_query: str, 
        history: List[Dict]
    ) -> str:
        """Resolve ambiguous queries using history"""
        
        if not history:
            return current_query
        
        # Check for follow-up patterns
        follow_up_patterns = [
            "what about", "how about", "and for", "in", "show me",
            "can you", "what are", "list", "tell me"
        ]
        
        current_lower = current_query.lower()
        is_follow_up = any(pattern in current_lower for pattern in follow_up_patterns)
        
        if is_follow_up and len(current_query.split()) < 10:
            # Likely a follow-up, add context from last query
            last_entry = history[-1]
            resolved = f"{last_entry['user_query']}. Additionally: {current_query}"
            return resolved
        
        return current_query
    
    def _build_conversation_context(self, history: List[Dict]) -> str:
        """Build conversation context string"""
        if not history:
            return "Conversation History: None (this is the first question)"
        
        context = "Conversation History:\n"
        for i, entry in enumerate(history[-5:], 1):  # Last 5 entries
            context += f"\nTurn {i}:\n"
            context += f"  User asked: {entry['user_query']}\n"
            context += f"  Generated SQL: {entry['sql'][:200]}{'...' if len(entry['sql']) > 200 else ''}\n"
        
        return context
    
    def clear_history(self, session_id: str):
        """Clear chat history for session"""
        if session_id in self.chat_sessions:
            self.chat_sessions[session_id] = []
```

---

## Tab 4: Agentic Text2SQL (Using Tools and Agents)

### Workflow Overview
```
User Query → Agent Plans → Execute Tools → Validate → Refine → Return
         ↓
    Schema Tool
    Sample Data Tool
    Metadata Search Tool
    SQL Execution Tool
    Result Validation Tool
```

### Architecture
```
┌─────────────────┐
│  User Query     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Agent Controller                   │
│  - Analyzes query complexity        │
│  - Plans tool execution sequence    │
│  - Manages tool results             │
└────────┬────────────────────────────┘
         │
         ▼
    ┌────┴────┐
    │  Tools  │
    └────┬────┘
         │
         ├──────────┬──────────┬──────────┬──────────┐
         ▼          ▼          ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │Schema  │ │Sample  │ │Metadata│ │Execute │ │Validate│
    │Inspector│ │Fetcher │ │Search  │ │SQL     │ │Results │
    └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
        │          │          │          │          │
        └──────────┴──────────┴──────────┴──────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │  Agent Loop    │
                   │  - Reviews tool│
                   │    outputs     │
                   │  - Decides next│
                   │    action      │
                   │  - Refines SQL │
                   │  - Validates   │
                   └────────────────┘
```

### Tool Definitions

```python
# backend/app/services/agentic_text2sql.py

from typing import List, Dict, Callable
import json

class Tool:
    """Base tool class"""
    def __init__(self, name: str, description: str, function: Callable):
        self.name = name
        self.description = description
        self.function = function
    
    def execute(self, **kwargs) -> Dict:
        """Execute the tool"""
        try:
            result = self.function(**kwargs)
            return {
                "success": True,
                "tool": self.name,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "tool": self.name,
                "error": str(e)
            }


class AgenticText2SQLService:
    """Agentic Text2SQL using tools and planning"""
    
    def __init__(self, bedrock_client, db_connection):
        self.bedrock = bedrock_client
        self.db = db_connection
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self) -> Dict[str, Tool]:
        """Initialize available tools"""
        
        tools = {}
        
        # Tool 1: Schema Inspector
        tools['get_schema'] = Tool(
            name="get_schema",
            description="Retrieves database schema information including tables, columns, data types, and relationships",
            function=self._get_schema
        )
        
        # Tool 2: Sample Data Fetcher
        tools['get_sample_data'] = Tool(
            name="get_sample_data",
            description="Fetches sample rows from specified table to understand data format and values",
            function=self._get_sample_data
        )
        
        # Tool 3: Metadata Search (using Bedrock Knowledge Base)
        tools['search_metadata'] = Tool(
            name="search_metadata",
            description="Searches metadata documentation for business rules, query patterns, and best practices",
            function=self._search_metadata
        )
        
        # Tool 4: SQL Executor
        tools['execute_sql'] = Tool(
            name="execute_sql",
            description="Executes a SQL query against the database and returns results",
            function=self._