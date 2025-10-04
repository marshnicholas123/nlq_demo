import re
import json
from typing import Dict
from app.services.bedrock_client import bedrock_client
from app.database import get_db_connection
from langchain_aws import ChatBedrock
from langchain.prompts import ChatPromptTemplate
from app.config import settings

class SimpleText2SQLService:
    def __init__(self):
        self.bedrock = bedrock_client
        # Initialize LangChain ChatBedrock for parser LLM
        # When using ARN, we need to specify the provider
        if settings.bedrock_model_id.startswith('arn:'):
            # Extract provider from ARN (e.g., anthropic from the model ARN)
            self.parser_llm = ChatBedrock(
                model_id=settings.bedrock_model_id,
                region_name=settings.aws_region,
                model_kwargs={"temperature": 0.3, "max_tokens": 1000},
                provider="anthropic"  # Required for ARN-based model IDs
            )
        else:
            self.parser_llm = ChatBedrock(
                model_id=settings.bedrock_model_id,
                region_name=settings.aws_region,
                model_kwargs={"temperature": 0.3, "max_tokens": 1000}
            )
    
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
        
        # Clean up the response
        sql_query = self._extract_sql(sql_query)
        
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

    def parse_results_to_text(
        self,
        user_query: str,
        sql_query: str,
        execution_result: Dict
    ) -> str:
        """
        Parse SQL execution results into natural language response using LangChain

        Args:
            user_query: Original user question in natural language
            sql_query: Generated SQL query that was executed
            execution_result: Dictionary containing query results

        Returns:
            Natural language response answering the user's question
        """
        try:
            # Handle error cases
            if not execution_result.get("success"):
                error_msg = execution_result.get("error", "Unknown error")
                return f"I encountered an error while executing the query: {error_msg}. Please check the database connection and query syntax."

            # Format results for the prompt
            data = execution_result.get("data", [])
            row_count = execution_result.get("row_count", 0)

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
                # Escape curly braces in JSON to avoid template variable issues
                formatted_results = json.dumps(data, indent=2, default=str)
                # Double curly braces to escape them in f-strings
                formatted_results = formatted_results.replace('{', '{{').replace('}', '}}')

            # Create prompt template
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

            # Create chat prompt template - use static messages since we've already formatted the prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", "{system_msg}"),
                ("human", "{user_msg}")
            ])

            # Generate response using LangChain
            chain = prompt | self.parser_llm
            response = chain.invoke({"system_msg": system_prompt, "user_msg": user_prompt})

            # Extract text from response
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)

        except Exception as e:
            # Return None if parser LLM fails, don't block the request
            print(f"Error in parse_results_to_text: {str(e)}")
            return None