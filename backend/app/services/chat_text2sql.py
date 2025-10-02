from typing import List, Dict, Optional
from datetime import datetime
from app.services.advanced_text2sql import AdvancedText2SQLService

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
        """Generate SQL with conversation context"""
        
        # 1. Get or create chat history
        chat_history = self._get_chat_history(session_id)
        
        # 2. Resolve query with history (handle follow-ups)
        resolved_query = self._resolve_query_with_history(user_query, chat_history)
        
        # 3. Retrieve metadata context (BM25)
        relevant_context = self.retrieve_relevant_context(resolved_query, top_k=5)
        
        # 4. Get schema and sample data
        schema_context = self.get_schema_context()
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