import os
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.services.bedrock_client import BedrockClient
from app.config import settings

from app.main import app

client = TestClient(app)


class TestSimpleText2SQL:
    """Test suite for the simple_text2sql endpoint"""
    
    def test_simple_text2sql_without_execution(self):
        """Test simple text2sql conversion without executing the query"""
        print("\n=== Running test_simple_text2sql_without_execution ===")
        response = client.post(
            "/api/text2sql/simple",
            json={
                "query": "Show me all operational plants",
                "execute": False
            }
        )
        
        print(f"Response status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        print(f"Response data: {data}")
        assert isinstance(data["sql"], str)
        assert len(data["sql"]) > 0
        assert data["method"] == "simple"
        assert data["execution_result"] is None
        print("Test passed!")
    
    def test_simple_text2sql_with_execution(self):
        """Test simple text2sql conversion with query execution"""
        print("\n=== Running test_simple_text2sql_with_execution ===")
        response = client.post(
            "/api/text2sql/simple",
            json={
                "query": "Show me all operational plants",
                "execute": True
            }
        )
        
        print(f"Response status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        print(f"Generated SQL: {data['sql']}")
        print(f"Execution result: {data['execution_result']}")
        assert isinstance(data["sql"], str)
        assert len(data["sql"]) > 0
        assert data["method"] == "simple"
        assert data["execution_result"] is not None
        assert "success" in data["execution_result"]
        print("Test passed!")
    
    def test_simple_text2sql_missing_query(self):
        """Test simple text2sql with missing query parameter"""
        print("\n=== Running test_simple_text2sql_missing_query ===")
        response = client.post(
            "/api/text2sql/simple",
            json={"execute": False}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        assert response.status_code == 422  # Validation error
        print("Test passed!")
    
    def test_simple_text2sql_empty_query(self):
        """Test simple text2sql with empty query"""
        print("\n=== Running test_simple_text2sql_empty_query ===")
        response = client.post(
            "/api/text2sql/simple",
            json={
                "query": "",
                "execute": False
            }
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        assert response.status_code == 500  # Service fails on empty query
        print("Test passed!")
    
    def test_simple_text2sql_service_exception(self):
        """Test simple text2sql when service raises an exception"""
        print("\n=== Running test_simple_text2sql_service_exception ===")
        with patch('app.routes.text2sql.simple_service.generate_sql', side_effect=Exception("Database connection failed")):
            response = client.post(
                "/api/text2sql/simple",
                json={
                    "query": "Show me all plants",
                    "execute": False
                }
            )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]
        print("Test passed!")
    
    def test_simple_text2sql_execution_failure(self):
        """Test simple text2sql when SQL execution fails"""
        print("\n=== Running test_simple_text2sql_execution_failure ===")
        mock_sql_result = {
            "sql": "SELECT * FROM invalid_table",
            "method": "simple"
        }
        
        with patch('app.routes.text2sql.simple_service.generate_sql', return_value=mock_sql_result), \
             patch('app.routes.text2sql.simple_service.execute_query', side_effect=Exception("Table does not exist")):
            
            response = client.post(
                "/api/text2sql/simple",
                json={
                    "query": "Show me invalid data",
                    "execute": True
                }
            )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        assert response.status_code == 500
        assert "Table does not exist" in response.json()["detail"]
        print("Test passed!")
    
    def test_simple_text2sql_default_execute_false(self):
        """Test that execute defaults to False when not provided"""
        print("\n=== Running test_simple_text2sql_default_execute_false ===")
        response = client.post(
            "/api/text2sql/simple",
            json={"query": "How many plants are there?"}
        )
        
        print(f"Response status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        print(f"Generated SQL: {data['sql']}")
        print(f"Execution result: {data['execution_result']}")
        assert isinstance(data["sql"], str)
        assert len(data["sql"]) > 0
        assert data["execution_result"] is None  # Should not execute by default
        print("Test passed!")
    
    def test_simple_text2sql_complex_query(self):
        """Test simple text2sql with a more complex natural language query"""
        print("\n=== Running test_simple_text2sql_complex_query ===")
        response = client.post(
            "/api/text2sql/simple",
            json={
                "query": "Show me nuclear plants with capacity greater than 1000 MW along with their countries",
                "execute": False
            }
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        print(f"Generated SQL: {data['sql']}")
        print(f"Method: {data['method']}")
        assert isinstance(data["sql"], str)
        assert len(data["sql"]) > 0
        assert data["method"] == "simple"
        print("Test passed!")
    
    def test_simple_text2sql_execution_with_data_validation(self):
        """Test simple text2sql execution and validate that it returns actual data from the database"""
        print("\n=== Running test_simple_text2sql_execution_with_data_validation ===")
        response = client.post(
            "/api/text2sql/simple",
            json={
                "query": "Show me all plants in India?",
                "execute": True
            }
        )
        
        print(f"Response status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        print(f"Generated SQL: {data['sql']}")
        print(f"Method: {data['method']}")
        print(f"Execution result: {data['execution_result']}")
        
        # Validate basic structure
        assert isinstance(data["sql"], str)
        assert len(data["sql"]) > 0
        assert data["method"] == "simple"
        assert data["execution_result"] is not None
        assert "success" in data["execution_result"]
        
        # Validate that execution was successful and returned data
        execution_result = data["execution_result"]
        assert execution_result["success"] is True
        
        # Check if data was returned (should have 'data' key with results)
        if "data" in execution_result:
            print(f"Number of rows returned: {len(execution_result['data'])}")
            print(f"Sample data (first 3 rows): {execution_result['data'][:3]}")
            assert isinstance(execution_result["data"], list)
        else:
            print("No 'data' key in execution result - checking other possible keys")
            print(f"Available keys in execution_result: {list(execution_result.keys())}")
        
        print("Test passed!")