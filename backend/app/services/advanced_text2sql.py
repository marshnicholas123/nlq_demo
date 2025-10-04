from rank_bm25 import BM25Okapi
import re
from typing import List, Dict
from app.services.simple_text2sql import SimpleText2SQLService
from app.services.bedrock_client import bedrock_client
from app.database import get_db_connection
from opentelemetry import trace

# Get tracer for custom spans
tracer = trace.get_tracer(__name__)

class AdvancedText2SQLService(SimpleText2SQLService):
    def __init__(self):
        super().__init__()
        self.bedrock = bedrock_client
        self.metadata_index = None
        self._initialize_bm25_index()
    
    def _initialize_bm25_index(self):
        """Build BM25 index from metadata documents"""
        metadata_docs = self._load_metadata_documents()
        
        # Tokenize documents
        tokenized_docs = [doc['content'].lower().split() for doc in metadata_docs]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(tokenized_docs)
        self.metadata_docs = metadata_docs
    
    def _load_metadata_documents(self) -> List[Dict]:
        """Load and chunk metadata documents"""
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
            "table": "nuclear_power_plant_status_types",
            "section": "operational_definition",
            "content": """StatusId = 3 means Operational (currently generating electricity).
            StatusId = 2 means Under Construction (future capacity).
            StatusId = 5 means Shutdown (permanently closed).
            Always filter by StatusId = 3 for current capacity calculations."""
        })
        
        docs.append({
            "table": "nuclear_power_plant_status_types",
            "section": "capacity_analysis",
            "content": """For capacity expansion analysis, use StatusId IN (1, 2) for planned and under construction.
            For retired capacity, use StatusId = 5.
            464 operational plants, 55 under construction, 174 shutdown globally."""
        })
        
        # Reactor types metadata
        docs.append({
            "table": "nuclear_reactor_types",
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
            Join with countries table: JOIN countries c ON npp.CountryCode = c.id.
            Use Latitude and Longitude for mapping.
            Geographic analysis example: GROUP BY CountryCode, ORDER BY COUNT(*) DESC"""
        })
        
        docs.append({
            "table": "nuclear_power_plants",
            "section": "temporal_analysis",
            "content": """OperationalFrom indicates when plant started.
            OperationalTo indicates shutdown date (NULL if still operational).
            ConstructionStartAt shows construction beginning.
            To find new plants: WHERE OperationalFrom >= DATE('now', '-5 years').
            To calculate age: (julianday('now') - julianday(OperationalFrom)) / 365"""
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
            SQL: SELECT c.name, COUNT(npp.Id) as plant_count, SUM(npp.Capacity) as total_capacity
            FROM nuclear_power_plants npp JOIN countries c ON npp.CountryCode = c.id
            WHERE npp.StatusId = 3 GROUP BY c.id, c.name ORDER BY plant_count DESC LIMIT 10;"""
        })
        
        return docs
    
    def retrieve_relevant_context(self, query: str, top_k: int = 5) -> List[Dict]:
        """Use BM25 to retrieve relevant metadata sections"""
        with tracer.start_as_current_span("advanced_text2sql.bm25_retrieval") as span:
            span.set_attribute("query", query)
            span.set_attribute("top_k", top_k)

            tokenized_query = query.lower().split()
            scores = self.bm25.get_scores(tokenized_query)

            # Get top-k results
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

            relevant_docs = [self.metadata_docs[i] for i in top_indices if scores[i] > 0]

            span.set_attribute("retrieved_docs_count", len(relevant_docs))
            span.set_attribute("retrieved_sections", [doc['section'] for doc in relevant_docs])

            return relevant_docs
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> str:
        """Get sample rows from table"""
        with tracer.start_as_current_span("advanced_text2sql.get_sample_data") as span:
            span.set_attribute("table_name", table_name)
            span.set_attribute("limit", limit)

            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                results = cursor.fetchall()

                if not results:
                    span.set_attribute("rows_fetched", 0)
                    return ""

                # Format as string
                sample_str = f"\nSample data from {table_name}:\n"
                for i, row in enumerate(results, 1):
                    sample_str += f"Row {i}: {row}\n"

                cursor.close()
                conn.close()

                span.set_attribute("rows_fetched", len(results))
                return sample_str
            except Exception as e:
                span.record_exception(e)
                span.set_attribute("error", True)
                return f"Error fetching sample data: {str(e)}"
    
    def generate_sql(self, user_query: str) -> Dict:
        """Generate SQL with enhanced context"""

        with tracer.start_as_current_span("advanced_text2sql.generate_sql") as span:
            span.set_attribute("user_query", user_query)
            span.set_attribute("method", "advanced")

            # 1. Retrieve relevant metadata using BM25
            relevant_context = self.retrieve_relevant_context(user_query, top_k=5)

            # 2. Get schema
            schema_context = self.get_schema_context()

            # 3. Get sample data for relevant tables
            tables_mentioned = self._identify_relevant_tables(user_query, relevant_context)
            span.set_attribute("tables_mentioned", tables_mentioned)

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

            # Call Bedrock (automatically traced)
            sql_query = self.bedrock.invoke_model(
                prompt=user_prompt,
                system=system_prompt
            )

            sql_query = self._extract_sql(sql_query)

            span.set_attribute("generated_sql", sql_query)
            span.set_attribute("context_sections_used", [doc['section'] for doc in relevant_context])

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
            tables.add('nuclear_power_plant_status_types')
        
        if any(word in query_lower for word in ['reactor', 'technology', 'pwr', 'bwr', 'type']):
            tables.add('nuclear_reactor_types')
        
        return list(tables)