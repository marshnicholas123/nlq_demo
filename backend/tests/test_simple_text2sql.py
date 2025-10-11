"""
Test SimpleText2SQLService Complete Pipeline

This script tests the complete pipeline of SimpleText2SQLService:
1. Service initialization
2. Generate SQL
3. Execute SQL query
4. Parse results to natural language

Uses a single query to avoid API throttling issues.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.simple_text2sql import SimpleText2SQLService


def test_complete_pipeline():
    """Test complete pipeline with a single query: generate SQL -> execute -> parse results"""
    print("\n" + "=" * 80)
    print("SimpleText2SQLService Complete Pipeline Test")
    print("=" * 80)

    # Single test query to avoid throttling
    query = "How many nuclear power plants are in India?"

    print(f"\nTest Query: '{query}'")
    print("=" * 80)

    try:
        # Step 0: Initialize service
        print("\nStep 0: Initializing SimpleText2SQLService...")
        service = SimpleText2SQLService()
        print("  ✓ Service initialized successfully")

        # Step 1: Generate SQL
        print("\nStep 1: Generating SQL...")
        sql_result = service.generate_sql(query)
        sql_query = sql_result.get('sql')
        method = sql_result.get('method')

        print(f"  Method: {method}")
        print(f"\n  Generated SQL:")
        print(f"  {sql_query}")
        print("\n  ✓ SQL generation successful")

        # Step 2: Execute SQL
        print("\nStep 2: Executing SQL query...")
        execution_result = service.execute_query(sql_query)

        if execution_result.get("success"):
            print(f"  ✓ Query executed successfully")
            print(f"  Row count: {execution_result.get('row_count')}")
            data = execution_result.get('data', [])
            if data:
                print(f"  Data: {data[0]}")
        else:
            print(f"  ✗ Query execution failed: {execution_result.get('error')}")
            return 1

        # Step 3: Parse results to natural language
        print("\nStep 3: Parsing results to natural language...")
        parsed_response = service.parse_results_to_text(
            user_query=query,
            sql_query=sql_query,
            execution_result=execution_result
        )

        if parsed_response:
            print(f"  ✓ Response generated successfully\n")
            print("  Final Natural Language Response:")
            print("  " + "-" * 76)
            # Format the response with proper indentation
            for line in parsed_response.split('\n'):
                print(f"  {line}")
            print("  " + "-" * 76)
        else:
            print(f"  ✗ Failed to generate natural language response")
            return 1

        # Success summary
        print("\n" + "=" * 80)
        print("✓ Complete Pipeline Test PASSED")
        print("=" * 80)
        print("\nPipeline Summary:")
        print(f"  • Query: '{query}'")
        print(f"  • SQL Generated: {sql_query}")
        print(f"  • Rows Returned: {execution_result.get('row_count')}")
        print(f"  • Natural Language Response: Generated successfully")
        print("\nSimpleText2SQLService Features Verified:")
        print("  ✓ SQL generation with basic schema")
        print("  ✓ Query execution")
        print("  ✓ Natural language response parsing")

        return 0

    except Exception as e:
        print(f"\n✗ Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Run the complete pipeline test"""
    return test_complete_pipeline()


if __name__ == "__main__":
    exit(main())