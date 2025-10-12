from typing import List, Dict, Callable, Optional, TypedDict, Annotated
import json
import time
from datetime import datetime
from app.services.advanced_text2sql import AdvancedText2SQLService
from app.services.bedrock_client import bedrock_client
from opentelemetry import trace
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

# Get tracer for custom spans
tracer = trace.get_tracer(__name__)


class AgentState(TypedDict):
    """State for the agentic workflow"""
    # Core query info
    user_query: str
    session_id: str
    resolved_query: str

    # Conversation context (use operator.add to append to list)
    chat_history: Annotated[List[Dict], operator.add]

    # Iteration tracking
    iteration: int
    max_iterations: int

    # Retrieved context
    schema: Optional[str]
    sample_data: Dict[str, str]
    metadata_context: Annotated[List[Dict], operator.add]

    # Generated artifacts
    sql_query: Optional[str]
    execution_result: Optional[Dict]
    validation_result: Optional[Dict]
    parsed_response: Optional[str]

    # Reflection and clarification
    reflection_result: Optional[Dict]
    clarification_needed: bool
    clarification_questions: Annotated[List[str], operator.add]

    # Tool tracking (use operator.add to append to list)
    tool_calls: Annotated[List[Dict], operator.add]

    # Flow control
    next_action: str
    is_complete: bool
    error: Optional[str]


class Tool:
    """Base tool class"""
    def __init__(self, name: str, description: str, function: Callable):
        self.name = name
        self.description = description
        self.function = function

    def execute(self, **kwargs) -> Dict:
        """Execute the tool"""
        with tracer.start_as_current_span(f"agentic_text2sql.tool.{self.name}") as span:
            span.set_attribute("tool_name", self.name)
            span.set_attribute("tool_params", str(kwargs))

            try:
                result = self.function(**kwargs)
                span.set_attribute("success", True)
                return {
                    "success": True,
                    "tool": self.name,
                    "result": result
                }
            except Exception as e:
                span.record_exception(e)
                span.set_attribute("error", True)
                return {
                    "success": False,
                    "tool": self.name,
                    "error": str(e)
                }


class AgenticText2SQLService(AdvancedText2SQLService):
    """Agentic Text2SQL with conversation context, reflection, and clarification"""

    def __init__(self):
        super().__init__()
        self.bedrock = bedrock_client
        self.tools = self._initialize_tools()
        # Session storage (use Redis or database in production)
        self.chat_sessions = {}
        self.workflow = self._build_workflow()

    def _initialize_tools(self) -> Dict[str, Tool]:
        """Initialize available tools"""

        tools = {}

        # Tool 1: Schema Inspector (with hybrid retrieval)
        tools['get_schema'] = Tool(
            name="get_schema",
            description="Retrieves database schema using hybrid vector + BM25 retrieval",
            function=self._get_schema_hybrid
        )

        # Tool 2: Sample Data Fetcher (with BM25 retrieval)
        tools['get_sample_data'] = Tool(
            name="get_sample_data",
            description="Fetches query-relevant sample rows from specified tables using BM25 retrieval. Requires query and table_names parameters.",
            function=self._get_sample_data_tool
        )

        # Tool 3: Metadata Search (with business rules)
        tools['search_metadata'] = Tool(
            name="search_metadata",
            description="Searches for business rules and best practices using hybrid retrieval",
            function=self._search_metadata_tool
        )

        # Tool 4: SQL Executor
        tools['execute_sql'] = Tool(
            name="execute_sql",
            description="Executes a SQL query against the database and returns results",
            function=self._execute_sql_tool
        )

        # Tool 5: Result Validator
        tools['validate_results'] = Tool(
            name="validate_results",
            description="Validates SQL query results for correctness and completeness",
            function=self._validate_results_tool
        )

        return tools

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for agentic behavior"""

        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("detect_clarification", self._detect_clarification_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("execute_tools", self._execute_tools_node)
        workflow.add_node("generate_sql", self._generate_sql_node)
        workflow.add_node("reflect", self._reflect_node)
        workflow.add_node("complete", self._complete_node)

        # Define edges
        workflow.set_entry_point("detect_clarification")

        workflow.add_conditional_edges(
            "detect_clarification",
            self._should_clarify,
            {
                "clarify": "complete",  # Return clarification to user
                "proceed": "plan"
            }
        )

        workflow.add_conditional_edges(
            "plan",
            self._should_generate_sql,
            {
                "generate": "generate_sql",
                "execute_tools": "execute_tools",
                "complete": "complete"
            }
        )

        workflow.add_edge("execute_tools", "plan")  # Loop back for more tools if needed

        workflow.add_edge("generate_sql", "reflect")

        workflow.add_conditional_edges(
            "reflect",
            self._should_refine,
            {
                "refine": "plan",  # Go back and try again
                "complete": "complete"  # Complete if acceptable
            }
        )
        workflow.add_edge("complete", END)

        return workflow.compile()

    def generate_sql_with_agent(
        self,
        user_query: str,
        session_id: str,
        max_iterations: int = 3
    ) -> Dict:
        """Generate SQL using agentic approach with conversation context"""

        with tracer.start_as_current_span("agentic_text2sql.generate_sql_with_agent") as span:
            span.set_attribute("user_query", user_query)
            span.set_attribute("session_id", session_id)
            span.set_attribute("method", "agentic_hybrid")
            span.set_attribute("max_iterations", max_iterations)

            # Get conversation history
            chat_history = self._get_chat_history(session_id)
            span.set_attribute("chat_history_length", len(chat_history))

            # Resolve query with history
            resolved_query = self._resolve_query_with_history(user_query, chat_history)
            is_followup = resolved_query != user_query
            span.set_attribute("is_followup_query", is_followup)
            if is_followup:
                span.set_attribute("resolved_query", resolved_query)

            # Initialize agent state
            initial_state: AgentState = {
                "user_query": user_query,
                "session_id": session_id,
                "resolved_query": resolved_query,
                "chat_history": chat_history,
                "iteration": 0,
                "max_iterations": max_iterations,
                "schema": None,
                "sample_data": {},
                "metadata_context": [],
                "sql_query": None,
                "execution_result": None,
                "validation_result": None,
                "parsed_response": None,
                "reflection_result": None,
                "clarification_needed": False,
                "clarification_questions": [],
                "tool_calls": [],
                "next_action": "detect_clarification",
                "is_complete": False,
                "error": None
            }

            # Run workflow
            try:
                final_state = self.workflow.invoke(initial_state)

                span.set_attribute("total_iterations", final_state.get("iteration", 0))
                span.set_attribute("total_tool_calls", len(final_state.get("tool_calls", [])))
                span.set_attribute("generated_sql", final_state.get("sql_query"))
                span.set_attribute("clarification_needed", final_state.get("clarification_needed", False))

                # Add to history if SQL was generated
                if final_state.get("sql_query") and not final_state.get("clarification_needed"):
                    self._add_to_history(session_id, {
                        "user_query": user_query,
                        "resolved_query": resolved_query,
                        "sql": final_state["sql_query"],
                        "timestamp": datetime.now().isoformat()
                    })

                return self._format_response(final_state)

            except Exception as e:
                span.record_exception(e)
                span.set_attribute("error", True)
                return {
                    "success": False,
                    "error": str(e),
                    "method": "agentic_hybrid"
                }

    # ===== Workflow Nodes =====

    def _detect_clarification_node(self, state: AgentState) -> Dict:
        """Detect if query needs clarification with access to schema and metadata"""
        with tracer.start_as_current_span("agentic_text2sql.detect_clarification") as span:
            query = state["resolved_query"]
            span.set_attribute("query", query)

            # Gather context: schema and metadata
            schema_context = None
            metadata_context = []

            try:
                # Get schema context with query-relevant retrieval
                schema_result = self.tools['get_schema'].execute(query=query)
                if schema_result.get("success"):
                    schema_context = schema_result.get("result")
                    span.set_attribute("schema_retrieved", True)

                # Search for relevant metadata
                metadata_result = self.tools['search_metadata'].execute(query=query, top_k=5)
                if metadata_result.get("success"):
                    metadata_context = metadata_result.get("result", [])
                    span.set_attribute("metadata_retrieved", len(metadata_context))

            except Exception as e:
                span.record_exception(e)
                span.set_attribute("context_retrieval_error", str(e))

            # Format context for LLM
            schema_str = schema_context if schema_context else "Schema not available"
            metadata_str = "\n".join([
                f"- {doc.get('content', '')[:200]}..." for doc in metadata_context[:3]
            ]) if metadata_context else "No business rules found"

            # Use LLM to detect ambiguity with context
            clarification_prompt = f"""Analyze this database query for ambiguity, given the available schema and business context:

Query: {query}

Available Schema:
{schema_str[:1000]}...

Available Business Rules/Context:
{metadata_str}

Determine if this query needs clarification before generating SQL. Consider:
1. Is the intent clear and unambiguous given the schema?
2. Are there multiple valid interpretations?
3. Is critical context missing (date ranges, specific entities, metrics)?
4. Are there vague terms that could mean different things?
5. Can you identify the relevant tables/columns from the schema?
6. Do the business rules provide sufficient context?

Respond in JSON format:
{{
    "needs_clarification": true/false,
    "reason": "explanation of why clarification is/isn't needed",
    "questions": ["clarifying question 1", "clarifying question 2"],
    "available_context": "summary of what context is available to answer the query"
}}

Only request clarification if absolutely necessary - if the schema and business rules provide sufficient context, proceed without clarification. Return ONLY the JSON."""

            try:
                response = self.bedrock.invoke_model(
                    prompt=clarification_prompt,
                    system="You are a query analysis expert. Detect ambiguous queries that need clarification, but only when the available schema and business context are insufficient.",
                    operation_type="clarification_detection"
                )

                # Parse response
                result = json.loads(response)

                clarification_needed = result.get("needs_clarification", False)
                questions = result.get("questions", [])

                span.set_attribute("needs_clarification", clarification_needed)
                span.set_attribute("questions_count", len(questions))

                # Update state with retrieved context
                updates = {
                    "clarification_needed": clarification_needed,
                    "clarification_questions": questions,
                    "schema": schema_context,  # Store schema for later use
                    "metadata_context": metadata_context,  # Store metadata for later use
                    "tool_calls": [
                        {"tool": "get_schema", "success": bool(schema_context)},
                        {"tool": "search_metadata", "success": bool(metadata_context)}
                    ]
                }

                return updates

            except Exception as e:
                span.record_exception(e)
                # If detection fails, proceed without clarification but keep retrieved context
                return {
                    "clarification_needed": False,
                    "clarification_questions": [],
                    "schema": schema_context,
                    "metadata_context": metadata_context,
                    "tool_calls": [
                        {"tool": "get_schema", "success": bool(schema_context)},
                        {"tool": "search_metadata", "success": bool(metadata_context)}
                    ]
                }

    def _plan_node(self, state: AgentState) -> Dict:
        """Plan the next action based on current state"""
        with tracer.start_as_current_span("agentic_text2sql.plan") as span:
            iteration = state["iteration"] + 1
            span.set_attribute("iteration", iteration)

            updates = {"iteration": iteration}

            # Check iteration limit
            if iteration > state["max_iterations"]:
                updates["next_action"] = "complete"
                updates["is_complete"] = True
                span.set_attribute("reason", "max_iterations_reached")
                return updates

            # If no schema, get schema first
            if state["schema"] is None:
                updates["next_action"] = "get_schema"
                span.set_attribute("next_action", "get_schema")
                return updates

            # If no metadata context, search for relevant context
            if not state["metadata_context"]:
                updates["next_action"] = "search_metadata"
                span.set_attribute("next_action", "search_metadata")
                return updates

            # If no SQL generated yet, generate it
            if state["sql_query"] is None:
                updates["next_action"] = "generate_sql"
                span.set_attribute("next_action", "generate_sql")
                return updates

            # If SQL exists but not executed, execute it
            if state["execution_result"] is None:
                updates["next_action"] = "execute_sql"
                span.set_attribute("next_action", "execute_sql")
                return updates

            # If executed but not validated, validate
            if state["validation_result"] is None:
                updates["next_action"] = "validate_results"
                span.set_attribute("next_action", "validate_results")
                return updates

            # All steps complete
            updates["next_action"] = "complete"
            updates["is_complete"] = True
            span.set_attribute("next_action", "complete")
            return updates

    def _execute_tools_node(self, state: AgentState) -> Dict:
        """Execute the planned tool"""
        with tracer.start_as_current_span("agentic_text2sql.execute_tools") as span:
            action = state["next_action"]
            span.set_attribute("tool", action)

            # Map actions to tools and parameters
            tool_mapping = {
                "get_schema": ("get_schema", {"query": state["resolved_query"]}),
                "search_metadata": ("search_metadata", {"query": state["resolved_query"]}),
                "execute_sql": ("execute_sql", {"sql": state["sql_query"]}),
                "validate_results": ("validate_results", {
                    "query": state["resolved_query"],
                    "sql": state["sql_query"],
                    "results": state["execution_result"]
                })
            }

            updates = {}
            if action in tool_mapping:
                tool_name, params = tool_mapping[action]
                tool_result = self._execute_tool(tool_name, params)
                updates["tool_calls"] = [tool_result]
                span.set_attribute("tool_success", tool_result.get("success", False))

                # Update state based on tool result
                result = tool_result.get("result")
                if tool_name == "get_schema":
                    updates["schema"] = result
                elif tool_name == "search_metadata":
                    updates["metadata_context"] = result if result else []
                elif tool_name == "execute_sql":
                    updates["execution_result"] = result
                elif tool_name == "validate_results":
                    updates["validation_result"] = result

            return updates

    def _generate_sql_node(self, state: AgentState) -> Dict:
        """Generate SQL using collected context"""
        with tracer.start_as_current_span("agentic_text2sql.generate_sql") as span:
            # Build conversation context
            conversation_context = self._build_conversation_context(state["chat_history"])

            # Format metadata context
            metadata_str = "\n".join([
                doc.get("content", "") for doc in state["metadata_context"]
            ])

            # Build enhanced prompt
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

            sample_data_str = "\n".join([
                f"{table}: {data}" for table, data in state["sample_data"].items()
            ])

            user_prompt = f"""Database Schema:
{state["schema"]}

Sample Data:
{sample_data_str}

Business Context and Best Practices:
{metadata_str}

{conversation_context}

User Question: {state["user_query"]}

Generate a SQL query to answer this question accurately."""

            try:
                sql_query = self.bedrock.invoke_model(
                    prompt=user_prompt,
                    system=system_prompt,
                    operation_type="sql_generation"
                )

                sql = self._extract_sql(sql_query)
                span.set_attribute("generated_sql", sql)
                return {"sql_query": sql}

            except Exception as e:
                span.record_exception(e)
                return {
                    "error": str(e),
                    "is_complete": True
                }

    def _reflect_node(self, state: AgentState) -> Dict:
        """Reflect on generated SQL - only replan if there are critical errors"""
        with tracer.start_as_current_span("agentic_text2sql.reflect") as span:
            sql = state["sql_query"]
            execution_result = state.get("execution_result")
            validation_result = state.get("validation_result")

            span.set_attribute("sql", sql)

            # Simple reflection: only regenerate if there's a critical error
            should_refine = False
            issues = []

            # Check for execution errors
            if execution_result and not execution_result.get("success"):
                error_msg = execution_result.get("error", "")
                # Only regenerate for syntax errors, not data issues
                if any(err in error_msg.lower() for err in ["syntax", "parse", "invalid sql", "unknown column", "unknown table"]):
                    should_refine = True
                    issues.append(f"SQL execution error: {error_msg}")

            # Check for empty results (potential issue)
            if validation_result and not validation_result.get("has_results"):
                issues.append("Query returned no results")
                # Don't regenerate for empty results - might be correct

            reflection = {
                "is_acceptable": not should_refine,
                "should_refine": should_refine,
                "issues": issues
            }

            span.set_attribute("is_acceptable", reflection["is_acceptable"])
            span.set_attribute("should_refine", should_refine)
            span.set_attribute("issues_count", len(issues))

            return {"reflection_result": reflection}

    def _complete_node(self, state: AgentState) -> Dict:
        """Mark workflow as complete"""
        return {"is_complete": True}

    # ===== Conditional Edge Functions =====

    def _should_clarify(self, state: AgentState) -> str:
        """Decide if clarification is needed"""
        if state.get("clarification_needed", False):
            return "clarify"
        return "proceed"

    def _should_generate_sql(self, state: AgentState) -> str:
        """Decide if ready to generate SQL"""
        action = state.get("next_action", "")

        if action == "generate_sql":
            return "generate"
        elif action == "complete":
            return "complete"
        else:
            return "execute_tools"

    def _should_refine(self, state: AgentState) -> str:
        """Decide if SQL should be refined"""
        reflection = state.get("reflection_result", {})

        # Only refine if explicitly needed and haven't exceeded iterations
        if (reflection.get("should_refine", False) and
            state["iteration"] < state["max_iterations"]):
            # Reset SQL to trigger regeneration
            state["sql_query"] = None
            state["execution_result"] = None
            state["validation_result"] = None
            return "refine"

        return "complete"

    # ===== Helper Methods =====

    def _execute_tool(self, tool_name: str, params: Dict) -> Dict:
        """Execute a specific tool"""
        if tool_name in self.tools:
            return self.tools[tool_name].execute(**params)
        else:
            return {"success": False, "error": f"Tool {tool_name} not found"}

    def _get_chat_history(self, session_id: str) -> List[Dict]:
        """Retrieve conversation history for a session"""
        return self.chat_sessions.get(session_id, [])

    def _add_to_history(self, session_id: str, entry: Dict):
        """Add entry to conversation history"""
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = []
        self.chat_sessions[session_id].append(entry)

        # Keep only last 10 exchanges
        if len(self.chat_sessions[session_id]) > 10:
            self.chat_sessions[session_id] = self.chat_sessions[session_id][-10:]

    def _resolve_query_with_history(self, user_query: str, chat_history: List[Dict]) -> str:
        """Resolve follow-up queries using conversation history"""
        if not chat_history:
            return user_query

        # Use LLM to resolve the query
        history_str = "\n".join([
            f"Q: {entry.get('user_query', '')}\nSQL: {entry.get('sql', '')}"
            for entry in chat_history[-3:]  # Last 3 exchanges
        ])

        resolve_prompt = f"""Given this conversation history:

{history_str}

User's new query: {user_query}

If this is a follow-up query that references previous context (e.g., "what about...", "show me more", "filter that by..."),
rewrite it as a standalone query that includes all necessary context.

If it's already a standalone query, return it unchanged.

Return ONLY the resolved query, nothing else."""

        try:
            resolved = self.bedrock.invoke_model(
                prompt=resolve_prompt,
                system="You are a query resolution assistant. Resolve follow-up queries into standalone queries.",
                operation_type="query_resolution"
            )
            return resolved.strip()
        except:
            return user_query

    def _build_conversation_context(self, chat_history: List[Dict]) -> str:
        """Build conversation context for SQL generation"""
        if not chat_history:
            return ""

        history_str = "\n".join([
            f"Previous Query: {entry.get('user_query', '')}\nGenerated SQL: {entry.get('sql', '')}"
            for entry in chat_history[-2:]  # Last 2 exchanges
        ])

        return f"\nConversation History:\n{history_str}\n"

    def _format_response(self, state: AgentState) -> Dict:
        """Format the final response"""
        # If clarification needed, return clarification response
        if state.get("clarification_needed"):
            return {
                "success": False,
                "needs_clarification": True,
                "questions": state.get("clarification_questions", []),
                "method": "agentic_hybrid"
            }

        # Normal response
        return {
            "success": True,
            "sql": state["sql_query"],
            "method": "agentic_hybrid",
            "session_id": state["session_id"],
            "resolved_query": state["resolved_query"] if state["resolved_query"] != state["user_query"] else None,
            "iterations": state["iteration"],
            "tool_calls": len(state["tool_calls"]),
            "execution_result": state["execution_result"],
            "validation_result": state["validation_result"],
            "parsed_response": state.get("parsed_response"),
            "reflection": state.get("reflection_result"),
            "context_used": {
                "schema": bool(state["schema"]),
                "metadata_rules": len(state["metadata_context"]),
                "sample_tables": list(state["sample_data"].keys())
            }
        }

    # ===== Tool Implementation Methods =====

    def _get_schema_hybrid(self, query: str = None) -> str:
        """Tool: Get database schema using hybrid retrieval (Vector + BM25)"""
        with tracer.start_as_current_span("agentic_text2sql.get_schema_hybrid") as span:
            # If no query provided, return all schemas
            if not query:
                span.set_attribute("query_provided", False)
                return self._get_schema()

            span.set_attribute("query", query)
            span.set_attribute("retrieval_method", "hybrid_vector_bm25")

            try:
                # 1. Retrieve using vector embeddings (top 2)
                vector_docs = self.vector_retriever.retrieve(query, top_k=2)
                span.set_attribute("vector_docs_count", len(vector_docs))

                # 2. Retrieve using BM25 (top 3)
                bm25_docs = self.retriever.retrieve(query, top_k=3)
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

                # Extract table names
                final_tables = [doc.get('table') or doc.get('table_name', '') for doc in top_3_docs]
                span.set_attribute("final_tables", final_tables)

                # 5. Build schema context string
                schema_context = "\n\n".join([
                    f"{doc['content']}"
                    for doc in top_3_docs
                ])

                span.set_attribute("schema_length", len(schema_context))
                return schema_context

            except Exception as e:
                span.record_exception(e)
                span.set_attribute("error", True)
                # Fallback to basic schema if hybrid retrieval fails
                return self._get_schema()

    def _get_schema(self) -> str:
        """Get full database schema"""
        with tracer.start_as_current_span("agentic_text2sql.get_schema"):
            # Implementation would retrieve schema from database
            # For now, return placeholder
            return "Schema information"

    def _get_sample_data_tool(self, query: str, table_names: List[str], limit: int = 4) -> str:
        """Tool: Get query-relevant sample data using BM25 retrieval"""
        with tracer.start_as_current_span("agentic_text2sql.get_sample_data_tool") as span:
            span.set_attribute("query", query)
            span.set_attribute("table_names", table_names)
            span.set_attribute("limit", limit)

            try:
                # Use inherited get_sample_data method from AdvancedText2SQLService
                sample_data_str = self.get_sample_data(
                    query=query,
                    table_names=table_names,
                    limit=limit
                )
                span.set_attribute("success", True)
                span.set_attribute("sample_data_length", len(sample_data_str))
                return sample_data_str
            except Exception as e:
                span.record_exception(e)
                span.set_attribute("error", True)
                return f"Error fetching sample data: {str(e)}"

    def _search_metadata_tool(self, query: str, top_k: int = 3) -> List[Dict]:
        """Tool: Search metadata and business rules"""
        with tracer.start_as_current_span("agentic_text2sql.search_metadata") as span:
            span.set_attribute("query", query)
            span.set_attribute("top_k", top_k)

            try:
                results = self.business_rules_retriever.retrieve(
                    query=query,
                    method='hybrid',
                    top_k=top_k
                )
                # Convert RetrievalResult objects to dictionaries
                return [
                    {
                        "content": r.content,
                        "score": r.score,
                        "source": r.source,
                        "metadata": r.metadata,
                        "method": r.method
                    }
                    for r in results
                ]
            except Exception as e:
                span.record_exception(e)
                return []

    def _execute_sql_tool(self, sql: str) -> Dict:
        """Tool: Execute SQL query"""
        with tracer.start_as_current_span("agentic_text2sql.execute_sql_tool") as span:
            span.set_attribute("sql", sql)
            try:
                result = self.execute_query(sql)
                span.set_attribute("success", result.get("success", False))
                return result
            except Exception as e:
                span.record_exception(e)
                return {"success": False, "error": str(e)}

    def _validate_results_tool(self, query: str, sql: str, results: Dict) -> Dict:
        """Tool: Validate SQL results"""
        with tracer.start_as_current_span("agentic_text2sql.validate_results") as span:
            span.set_attribute("query", query)
            span.set_attribute("sql", sql)

            # Simple validation logic
            validation = {
                "is_valid": True,
                "has_results": bool(results.get("data")),
                "row_count": len(results.get("data", [])),
                "issues": []
            }

            if not validation["has_results"]:
                validation["issues"].append("No results returned")

            span.set_attribute("is_valid", validation["is_valid"])
            span.set_attribute("row_count", validation["row_count"])

            return validation
