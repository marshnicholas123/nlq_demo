import re
from typing import List, Dict
from app.services.simple_text2sql import SimpleText2SQLService
from app.services.bedrock_client import bedrock_client
from app.services.retrievers import schema_retriever, sample_data_retriever, vector_schema_retriever
from app.database import get_db_connection
from opentelemetry import trace

# Get tracer for custom spans
tracer = trace.get_tracer(__name__)

class AdvancedText2SQLService(SimpleText2SQLService):
    """
    Advanced Text-to-SQL service with BM25 retrieval for enhanced context.

    Inherits execute_query() and parse_results_to_text() from SimpleText2SQLService.
    Adds BM25-based retrieval for schema metadata and sample data to improve SQL generation.
    """
    def __init__(self):
        super().__init__()
        self.bedrock = bedrock_client
        self.retriever = schema_retriever
        self.sample_retriever = sample_data_retriever
        self.vector_retriever = vector_schema_retriever

    def retrieve_table_schemas(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve relevant table schemas using BM25"""
        with tracer.start_as_current_span("advanced_text2sql.retrieve_schemas") as span:
            span.set_attribute("query", query)
            span.set_attribute("top_k", top_k)

            # Use BM25Retriever service
            relevant_docs = self.retriever.retrieve(query, top_k=top_k)

            span.set_attribute("retrieved_docs_count", len(relevant_docs))
            span.set_attribute("retrieved_sections", [doc.get('section', 'schema') for doc in relevant_docs])

            return relevant_docs
    
    def get_sample_data(self, query: str, table_names: List[str], limit: int = 4) -> str:
        """
        Get query-relevant sample rows using BM25 retrieval

        Args:
            query: User's natural language query
            table_names: List of relevant table names
            limit: Number of rows to retrieve per table (default: 4)

        Returns:
            Formatted string with relevant sample data
        """
        with tracer.start_as_current_span("advanced_text2sql.get_sample_data") as span:
            span.set_attribute("query", query)
            span.set_attribute("table_names", table_names)
            span.set_attribute("limit", limit)

            try:
                # Retrieve relevant sample data using BM25
                results = self.sample_retriever.retrieve_multi_table(
                    query=query,
                    table_names=table_names,
                    top_k=limit
                )

                if not results:
                    span.set_attribute("total_rows_fetched", 0)
                    return ""

                # Format as string
                sample_str = "\nRelevant Sample Data:\n"
                total_rows = 0

                for table_name, rows in results.items():
                    sample_str += f"\n{table_name} (top {len(rows)} relevant rows):\n"
                    for i, row_data in enumerate(rows, 1):
                        raw_data = row_data['raw_data']
                        sample_str += f"  Row {i}: {raw_data}\n"
                        total_rows += 1

                span.set_attribute("total_rows_fetched", total_rows)
                span.set_attribute("tables_with_samples", list(results.keys()))

                return sample_str

            except Exception as e:
                span.record_exception(e)
                span.set_attribute("error", True)
                return f"Error fetching sample data: {str(e)}"

    def generate_sql(self, user_query: str) -> Dict:
        """Generate SQL with enhanced context using hybrid retrieval (Vector + BM25)"""

        with tracer.start_as_current_span("advanced_text2sql.generate_sql") as span:
            span.set_attribute("user_query", user_query)
            span.set_attribute("method", "advanced_hybrid")

            # 1. Retrieve relevant table schemas using vector embeddings (top 2)
            vector_docs = self.vector_retriever.retrieve(user_query, top_k=2)
            span.set_attribute("vector_docs_count", len(vector_docs))

            # 2. Retrieve relevant table schemas using BM25 (top 3)
            bm25_docs = self.retrieve_table_schemas(user_query, top_k=3)
            span.set_attribute("bm25_docs_count", len(bm25_docs))

            # 3. Combine and deduplicate by table name
            combined_docs = []
            seen_tables = set()

            # Add BM25 results first (prioritize keyword matches)
            for doc in bm25_docs:
                table_name = doc.get('table', '').lower()
                if table_name and table_name not in seen_tables:
                    combined_docs.append(doc)
                    seen_tables.add(table_name)

            # Add vector results for semantic matching
            for doc in vector_docs:
                # Vector retriever uses 'table_name' key instead of 'table'
                table_name = doc.get('table_name', '').lower()
                if table_name and table_name not in seen_tables:
                    combined_docs.append(doc)
                    seen_tables.add(table_name)

            # 4. Select top 3 from combined results
            top_3_docs = combined_docs[:3]
            span.set_attribute("final_docs_count", len(top_3_docs))

            # Extract table names (handle both 'table' and 'table_name' keys)
            final_tables = [doc.get('table') or doc.get('table_name', '') for doc in top_3_docs]
            span.set_attribute("final_tables", final_tables)

            # 5. Build schema context from top 3 documents
            schema_context = "\n\n".join([
                f"{doc['content']}"
                for doc in top_3_docs
            ])

            # 6. Extract table names from top 3 schema documents for sample data
            tables_mentioned = []
            for doc in top_3_docs:
                table_name = (doc.get('table') or doc.get('table_name', '')).lower()
                if table_name and table_name not in tables_mentioned:
                    tables_mentioned.append(table_name)
            span.set_attribute("tables_mentioned", tables_mentioned)

            # 7. Get sample data for only the top 3 tables using BM25 retrieval
            sample_data = self.get_sample_data(user_query, tables_mentioned, limit=4)

            # 5. Metadata context (empty for now)
            metadata_context = ""

            # 6. Build enhanced prompt
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
                system=system_prompt,
                operation_type="sql_generation"
            )

            sql_query = self._extract_sql(sql_query)

            span.set_attribute("generated_sql", sql_query)
            span.set_attribute("context_sections_used", [doc.get('section', 'schema') for doc in top_3_docs])
            span.set_attribute("retrieval_method", "hybrid_vector_bm25")

            return {
                "sql": sql_query,
                "method": "advanced_hybrid",
                "context_used": [doc.get('section', 'schema') for doc in top_3_docs],
                "retrieval_stats": {
                    "vector_results": len(vector_docs),
                    "bm25_results": len(bm25_docs),
                    "final_top_k": len(top_3_docs)
                }
            }
    
