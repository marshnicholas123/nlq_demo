import re
import json
from typing import Dict
from app.services.bedrock_client import bedrock_client
from app.database import get_db_connection
from opentelemetry import trace

# Get tracer for custom spans
tracer = trace.get_tracer(__name__)

class SimpleText2SQLService:
    def __init__(self):
        self.bedrock = bedrock_client
    
    def get_schema_context(self) -> str:
        """Extract database schema information"""
        schema = """
        Database Schema:
        
        Table: countries
        - id (VARCHAR(2), PRIMARY KEY): Country code
        - name (VARCHAR(255)): Country name
        
        Table: nuclear_power_plant_status_types
        - Id (INT, PRIMARY KEY): Status identifier
        - Type (VARCHAR(50)): Status name
        
        Table: nuclear_reactor_types
        - Id (INT, PRIMARY KEY): Reactor type identifier
        - Type (VARCHAR(20)): Reactor type code
        - Description (VARCHAR(255)): Full reactor type name
        
        Table: nuclear_power_plants
        - Id (INT, PRIMARY KEY): Plant identifier
        - Name (VARCHAR(255)): Plant name
        - Latitude (DECIMAL): Geographic latitude
        - Longitude (DECIMAL): Geographic longitude
        - CountryCode (VARCHAR(2), FOREIGN KEY → countries.id): Country
        - StatusId (INT, FOREIGN KEY → nuclear_power_plant_status_types.Id): Current status
        - ReactorTypeId (INT, FOREIGN KEY → nuclear_reactor_types.Id): Reactor technology
        - ReactorModel (VARCHAR(100)): Specific reactor model
        - ConstructionStartAt (DATE): Construction start date
        - OperationalFrom (DATE): Operational start date
        - OperationalTo (DATE): Shutdown date (NULL if operational)
        - Capacity (INT): Capacity in megawatts
        - Source (VARCHAR(50)): Data source
        - LastUpdatedAt (DATETIME): Last update timestamp
        
        Relationships:
        - nuclear_power_plants.CountryCode → countries.id
        - nuclear_power_plants.StatusId → nuclear_power_plant_status_types.Id
        - nuclear_power_plants.ReactorTypeId → nuclear_reactor_types.Id
        """
        return schema
    
    def generate_sql(self, user_query: str) -> Dict:
        """Generate SQL from natural language"""

        with tracer.start_as_current_span("simple_text2sql.generate_sql") as span:
            span.set_attribute("user_query", user_query)
            span.set_attribute("method", "simple")

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

            # Call Bedrock (automatically traced)
            sql_query = self.bedrock.invoke_model(
                prompt=user_prompt,
                system=system_prompt,
                operation_type="sql_generation"
            )

            # Clean up the response
            sql_query = self._extract_sql(sql_query)

            span.set_attribute("generated_sql", sql_query)

            return {
                "sql": sql_query,
                "method": "simple"
            }
    
    def _extract_sql(self, response: str) -> str:
        """Extract SQL from LLM response"""
        # Remove markdown code blocks
        pattern = r'```sql\n(.*?)\n```'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
    
    def execute_query(self, sql: str) -> Dict:
        """Execute SQL and return results"""
        with tracer.start_as_current_span("simple_text2sql.execute_query") as span:
            span.set_attribute("sql", sql)

            try:
                conn = get_db_connection()

                # Handle both SQLite and MySQL connections
                if hasattr(conn, 'row_factory'):  # SQLite connection
                    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
                    cursor = conn.cursor()
                else:  # MySQL connection
                    cursor = conn.cursor(dictionary=True)

                cursor.execute(sql)

                # Fetch results
                results = cursor.fetchall()

                cursor.close()
                conn.close()

                span.set_attribute("row_count", len(results))
                span.set_attribute("success", True)

                return {
                    "success": True,
                    "data": results,
                    "row_count": len(results)
                }
            except Exception as e:
                span.record_exception(e)
                span.set_attribute("error", True)
                span.set_attribute("error_message", str(e))

                return {
                    "success": False,
                    "error": str(e)
                }

    def parse_results_to_text(
        self,
        user_query: str,
        sql_query: str,
        execution_result: Dict
    ) -> str:
        """
        Parse SQL execution results into natural language response

        Args:
            user_query: Original user question in natural language
            sql_query: Generated SQL query that was executed
            execution_result: Dictionary containing query results

        Returns:
            Natural language response answering the user's question
        """
        # BedrockInstrumentor will automatically trace this LLM call
        with tracer.start_as_current_span("simple_text2sql.parse_results") as span:
            span.set_attribute("user_query", user_query)
            span.set_attribute("sql_query", sql_query)

            try:
                # Handle error cases
                if not execution_result.get("success"):
                    error_msg = execution_result.get("error", "Unknown error")
                    span.set_attribute("error", True)
                    return f"I encountered an error while executing the query: {error_msg}. Please check the database connection and query syntax."

                # Format results for the prompt
                data = execution_result.get("data", [])
                row_count = execution_result.get("row_count", 0)
                span.set_attribute("result_row_count", row_count)

                # Truncate large result sets
                max_rows = 100
                truncated = False
                if len(data) > max_rows:
                    data = data[:max_rows]
                    truncated = True

                # Format results as readable text
                if row_count == 0:
                    formatted_results = "No results found."
                else:
                    formatted_results = json.dumps(data, indent=2, default=str)

                # Create prompt
                system_prompt = """You are a helpful data analyst assistant. Your job is to analyze SQL query results and provide clear, concise answers to user questions in natural language.

Rules:
1. Provide direct answers based on the data shown
2. Use specific numbers, names, and facts from the results
3. If results are empty, clearly state that no data was found
4. Format numbers appropriately (e.g., add commas, units)
5. Keep responses concise but informative
6. Do not make assumptions beyond what the data shows"""

                user_prompt = f"""User Question: {user_query}

SQL Query Executed:
{sql_query}

Query Results ({row_count} row{'s' if row_count != 1 else ''}):
{formatted_results}

{"Note: Results are truncated to first 100 rows." if truncated else ""}

Please provide a natural language answer to the user's question based on these results."""

                # Generate response using Bedrock (automatically traced)
                response_text = self.bedrock.invoke_model(
                    prompt=user_prompt,
                    system=system_prompt,
                    max_tokens=1000,
                    operation_type="response_generation"
                )

                span.set_attribute("response_length", len(response_text))
                return response_text

            except Exception as e:
                # Return None if parser LLM fails, don't block the request
                span.record_exception(e)
                span.set_attribute("error", True)
                print(f"Error in parse_results_to_text: {str(e)}")
                return None