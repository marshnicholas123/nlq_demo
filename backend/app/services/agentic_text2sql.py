from typing import List, Dict, Callable
import json
from app.services.advanced_text2sql import AdvancedText2SQLService
from app.services.bedrock_client import bedrock_client

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

class AgenticText2SQLService(AdvancedText2SQLService):
    """Agentic Text2SQL using tools and planning"""
    
    def __init__(self):
        super().__init__()
        self.bedrock = bedrock_client
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
            function=self._get_sample_data_tool
        )
        
        # Tool 3: Metadata Search
        tools['search_metadata'] = Tool(
            name="search_metadata",
            description="Searches metadata documentation for business rules, query patterns, and best practices",
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
    
    def generate_sql_with_agent(self, user_query: str, max_iterations: int = 3) -> Dict:
        """Generate SQL using agentic approach with tools"""
        
        agent_state = {
            "user_query": user_query,
            "iteration": 0,
            "schema": None,
            "sample_data": {},
            "metadata_context": [],
            "sql_query": None,
            "execution_result": None,
            "validation_result": None,
            "tool_calls": []
        }
        
        for iteration in range(max_iterations):
            agent_state["iteration"] = iteration + 1
            
            # Plan next action based on current state
            next_action = self._plan_next_action(agent_state)
            
            if next_action["action"] == "execute_tool":
                # Execute the planned tool
                tool_result = self._execute_tool(next_action["tool"], next_action["params"])
                agent_state["tool_calls"].append(tool_result)
                
                # Update agent state based on tool result
                self._update_agent_state(agent_state, tool_result)
                
            elif next_action["action"] == "generate_sql":
                # Generate SQL based on collected context
                sql_result = self._generate_sql_from_context(agent_state)
                agent_state["sql_query"] = sql_result["sql"]
                
            elif next_action["action"] == "complete":
                # Agent is satisfied with the result
                break
        
        return {
            "sql": agent_state["sql_query"],
            "method": "agentic",
            "iterations": agent_state["iteration"],
            "tool_calls": len(agent_state["tool_calls"]),
            "execution_result": agent_state["execution_result"],
            "validation_result": agent_state["validation_result"]
        }
    
    def _plan_next_action(self, state: Dict) -> Dict:
        """Plan the next action based on current agent state"""
        
        # If no schema, get schema first
        if state["schema"] is None:
            return {"action": "execute_tool", "tool": "get_schema", "params": {}}
        
        # If no metadata context, search for relevant context
        if not state["metadata_context"]:
            return {
                "action": "execute_tool", 
                "tool": "search_metadata", 
                "params": {"query": state["user_query"]}
            }
        
        # If no SQL generated yet, generate it
        if state["sql_query"] is None:
            return {"action": "generate_sql"}
        
        # If SQL exists but not executed, execute it
        if state["execution_result"] is None:
            return {
                "action": "execute_tool",
                "tool": "execute_sql",
                "params": {"sql": state["sql_query"]}
            }
        
        # If executed but not validated, validate
        if state["validation_result"] is None:
            return {
                "action": "execute_tool",
                "tool": "validate_results",
                "params": {
                    "query": state["user_query"],
                    "sql": state["sql_query"],
                    "results": state["execution_result"]
                }
            }
        
        # All steps complete
        return {"action": "complete"}
    
    def _execute_tool(self, tool_name: str, params: Dict) -> Dict:
        """Execute a specific tool"""
        if tool_name in self.tools:
            return self.tools[tool_name].execute(**params)
        else:
            return {"success": False, "error": f"Tool {tool_name} not found"}
    
    def _update_agent_state(self, state: Dict, tool_result: Dict):
        """Update agent state based on tool execution result"""
        if not tool_result["success"]:
            return
        
        tool_name = tool_result["tool"]
        result = tool_result["result"]
        
        if tool_name == "get_schema":
            state["schema"] = result
        elif tool_name == "search_metadata":
            state["metadata_context"] = result
        elif tool_name == "execute_sql":
            state["execution_result"] = result
        elif tool_name == "validate_results":
            state["validation_result"] = result
        elif tool_name == "get_sample_data":
            table_name = tool_result.get("table_name", "unknown")
            state["sample_data"][table_name] = result
    
    def _generate_sql_from_context(self, state: Dict) -> Dict:
        """Generate SQL using collected context"""
        # Use the advanced text2sql approach with collected context
        return {"sql": self.generate_sql(state["user_query"])["sql"]}
    
    # Tool implementation methods
    def _get_schema(self) -> str:
        """Tool: Get database schema"""
        return self.get_schema_context()
    
    def _get_sample_data_tool(self, table_name: str, limit: int = 5) -> str:
        """Tool: Get sample data from table"""
        return self.get_sample_data(table_name, limit)
    
    def _search_metadata_tool(self, query: str, top_k: int = 5) -> List[Dict]:
        """Tool: Search metadata for relevant context"""
        return self.retrieve_relevant_context(query, top_k)
    
    def _execute_sql_tool(self, sql: str) -> Dict:
        """Tool: Execute SQL query"""
        return self.execute_query(sql)
    
    def _validate_results_tool(self, query: str, sql: str, results: Dict) -> Dict:
        """Tool: Validate query results"""
        # Simple validation - could be enhanced with more sophisticated checks
        validation = {
            "query_executed": results.get("success", False),
            "has_results": results.get("row_count", 0) > 0,
            "error_present": "error" in results
        }
        
        validation["overall_valid"] = (
            validation["query_executed"] and 
            not validation["error_present"]
        )
        
        return validation