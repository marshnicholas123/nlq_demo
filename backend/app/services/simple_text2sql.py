import re
from typing import Dict
from app.services.bedrock_client import bedrock_client
from app.database import get_db_connection

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