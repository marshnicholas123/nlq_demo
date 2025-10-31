from typing import List, Dict, Optional
from datetime import datetime
from app.services.advanced_text2sql import AdvancedText2SQLService
from opentelemetry import trace

# Get tracer for custom spans
tracer = trace.get_tracer(__name__)

class ChatText2SQLService(AdvancedText2SQLService):
    """Extends Advanced with conversation context"""
    
    def __init__(self):
        super().__init__()
        # In production, use Redis or database for session storage
        self.chat_sessions = {}
    
    def generate_sql_with_context(
        self,
        user_query: str,
        session_id: str
    ) -> Dict:
        """Generate SQL with conversation context using hybrid retrieval"""

        with tracer.start_as_current_span("chat_text2sql.generate_sql_with_context") as span:
            span.set_attribute("user_query", user_query)
            span.set_attribute("session_id", session_id)
            span.set_attribute("method", "chat_hybrid")

            # 1. Get or create chat history
            chat_history = self._get_chat_history(session_id)
            span.set_attribute("chat_history_length", len(chat_history))

            # 2. Resolve query with history (handle follow-ups)
            resolved_query = self._resolve_query_with_history(user_query, chat_history)
            is_followup = resolved_query != user_query
            span.set_attribute("is_followup_query", is_followup)
            if is_followup:
                span.set_attribute("resolved_query", resolved_query)

            # 3. Retrieve relevant table schemas using vector embeddings (top 2)
            vector_docs = self.vector_retriever.retrieve(resolved_query, top_k=2)
            span.set_attribute("vector_docs_count", len(vector_docs))

            # 4. Retrieve relevant table schemas using BM25 (top 3)
            bm25_docs = self.retrieve_table_schemas(resolved_query, top_k=3)
            span.set_attribute("bm25_docs_count", len(bm25_docs))

            # 5. Combine and deduplicate by table name
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

            # 6. Select top 3 from combined results
            top_3_docs = combined_docs[:3]
            span.set_attribute("final_docs_count", len(top_3_docs))

            # Extract table names (handle both 'table' and 'table_name' keys)
            final_tables = [doc.get('table') or doc.get('table_name', '') for doc in top_3_docs]
            span.set_attribute("final_tables", final_tables)

            # 7. Build schema context from top 3 documents
            schema_context = "\n\n".join([
                f"{doc['content']}"
                for doc in top_3_docs
            ])

            # 8. Extract table names from top 3 schema documents for sample data
            tables_mentioned = []
            for doc in top_3_docs:
                table_name = (doc.get('table') or doc.get('table_name', '')).lower()
                if table_name and table_name not in tables_mentioned:
                    tables_mentioned.append(table_name)
            span.set_attribute("tables_mentioned", tables_mentioned)

            # 9. Get sample data for only the top 3 tables using BM25 retrieval
            sample_data = self.get_sample_data(resolved_query, tables_mentioned, limit=4)

            # 10. Get business rules and metadata context using hybrid retrieval
            try:
                business_rules_results = self.business_rules_retriever.retrieve(
                    query=resolved_query,
                    method='hybrid',
                    top_k=3
                )
                metadata_context = self.business_rules_retriever.format_context(business_rules_results)
                span.set_attribute("business_rules_count", len(business_rules_results))
            except Exception as e:
                span.record_exception(e)
                metadata_context = ""
                span.set_attribute("business_rules_error", str(e))

            # 11. Build conversation context
            conversation_context = self._build_conversation_context(chat_history)

            # 12. Enhanced prompt with chat history
            system_prompt = """You are an expert SQL query generator specialized in nuclear power plant databases.

Generate valid SQLite queries based on the provided schema, sample data, and business context.

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

{conversation_context}

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
            span.set_attribute("retrieval_method", "chat_hybrid_vector_bm25")

            # 13. Store in history before executing
            self._add_to_history(session_id, {
                "user_query": user_query,
                "resolved_query": resolved_query,
                "sql": sql_query,
                "timestamp": datetime.now().isoformat()
            })

            return {
                "sql": sql_query,
                "method": "chat_hybrid",
                "session_id": session_id,
                "resolved_query": resolved_query if resolved_query != user_query else None,
                "context_used": [doc.get('section', 'schema') for doc in top_3_docs],
                "retrieval_stats": {
                    "vector_results": len(vector_docs),
                    "bm25_results": len(bm25_docs),
                    "final_top_k": len(top_3_docs)
                }
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
        for i, entry in enumerate(history[-3:], 1):  # Last 3 entries
            context += f"\nTurn {i}:\n"
            context += f"  User asked: {entry['user_query']}\n"
            context += f"  Generated SQL: {entry['sql'][:100]}{'...' if len(entry['sql']) > 100 else ''}\n"

        return context
    
    def clear_history(self, session_id: str):
        """Clear chat history for session"""
        if session_id in self.chat_sessions:
            self.chat_sessions[session_id] = []