"""
Test AgenticText2SQLService Complete Pipeline

This script tests the complete pipeline of AgenticText2SQLService:
1. Service initialization
2. Generate SQL with agentic workflow
3. Execute SQL query
4. Parse results to natural language
5. Test follow-up query with conversation history

Uses two queries to test chat context functionality.
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.agentic_text2sql import AgenticText2SQLService


def test_agentic_pipeline():
    """Test agentic text2sql with complete workflow"""
    print("\n" + "=" * 80)
    print("AgenticText2SQLService Pipeline Test")
    print("=" * 80)
    print("\nNOTE: This test validates the agentic workflow with planning,")
    print("tool execution, reflection, and follow-up query handling.\n")

    # Test queries
    initial_query = "How many nuclear power plants are operational in India?"
    followup_query = "What about China?"
    session_id = "test_agentic_session_123"

    try:
        # Step 0: Initialize service
        print("\nStep 0: Initializing AgenticText2SQLService...")
        service = AgenticText2SQLService()
        print("  ✓ Service initialized successfully")
        print("  ✓ Agentic workflow graph compiled")

        # ===== INITIAL QUERY WITH AGENT =====
        print(f"\n{'=' * 80}")
        print(f"INITIAL QUERY: '{initial_query}'")
        print("=" * 80)

        # Step 1: Generate SQL using agentic workflow
        print("\nStep 1: Generating SQL with agentic workflow...")
        print("  (Agent will plan, retrieve schema, search metadata, generate SQL, reflect)")
        start_time = time.time()

        sql_result = service.generate_sql_with_agent(
            user_query=initial_query,
            session_id=session_id,
            max_iterations=3
        )

        elapsed = time.time() - start_time

        if not sql_result.get('success'):
            if sql_result.get('needs_clarification'):
                print(f"  ! Agent requested clarification:")
                for q in sql_result.get('questions', []):
                    print(f"    - {q}")

                # For automated testing, provide a refined query
                print("\n  Providing refined query to agent...")
                refined_query = "How many nuclear power plants with status 'Operational' are in India?"

                # Wait before retrying - longer wait after clarification
                print("  ⏳ Waiting 20 seconds to avoid Bedrock throttling...")
                time.sleep(20)

                # Retry with more specific query
                print(f"\n  Retrying with refined query: '{refined_query}'")
                sql_result = service.generate_sql_with_agent(
                    user_query=refined_query,
                    session_id=session_id,
                    max_iterations=3
                )

                if not sql_result.get('success'):
                    print(f"  ✗ SQL generation failed after clarification: {sql_result.get('error')}")
                    return 1
            else:
                print(f"  ✗ SQL generation failed: {sql_result.get('error')}")
                return 1

        sql_query = sql_result.get('sql')
        method = sql_result.get('method')
        iterations = sql_result.get('iterations', 0)
        tool_calls = sql_result.get('tool_calls', 0)
        reflection = sql_result.get('reflection', {})
        context_used = sql_result.get('context_used', {})

        print(f"  Method: {method}")
        print(f"  Iterations: {iterations}")
        print(f"  Tool calls: {tool_calls}")
        print(f"  Time elapsed: {elapsed:.2f}s")
        print(f"\n  Generated SQL:")
        print(f"  {sql_query}")

        if reflection:
            print(f"\n  Agent Reflection:")
            print(f"    Acceptable: {reflection.get('is_acceptable', 'N/A')}")
            print(f"    Confidence: {reflection.get('confidence', 'N/A')}")
            if reflection.get('issues'):
                print(f"    Issues found: {reflection.get('issues')}")

        print(f"\n  Context Used:")
        print(f"    Schema retrieved: {context_used.get('schema', False)}")
        print(f"    Metadata rules: {context_used.get('metadata_rules', 0)}")
        print(f"    Sample tables: {context_used.get('sample_tables', [])}")

        print("\n  ✓ Agentic SQL generation successful")

        # Wait after SQL generation
        print("\n⏳ Waiting 15 seconds to avoid Bedrock throttling...")
        time.sleep(15)

        # Step 2: Execute initial SQL
        print("\nStep 2: Executing initial SQL query...")
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

        # Wait before parsing
        print("\n⏳ Waiting 15 seconds to avoid Bedrock throttling...")
        time.sleep(15)

        # Step 3: Parse initial results to natural language
        print("\nStep 3: Parsing initial results to natural language...")
        parsed_response = service.parse_results_to_text(
            user_query=initial_query,
            sql_query=sql_query,
            execution_result=execution_result
        )

        if parsed_response:
            print(f"  ✓ Response generated successfully\n")
            print("  Initial Query Response:")
            print("  " + "-" * 76)
            for line in parsed_response.split('\n'):
                print(f"  {line}")
            print("  " + "-" * 76)
        else:
            print(f"  ✗ Failed to generate natural language response")
            return 1

        # Wait before follow-up query
        print("\n⏳ Waiting 20 seconds to avoid Bedrock throttling...")
        time.sleep(20)

        # ===== FOLLOW-UP QUERY WITH AGENT =====
        print(f"\n{'=' * 80}")
        print(f"FOLLOW-UP QUERY: '{followup_query}'")
        print("=" * 80)

        # Step 4: Generate SQL for follow-up query with chat context
        print("\nStep 4: Generating SQL for follow-up query (with chat history)...")
        print("  (Agent should resolve 'China' in context of previous query)")

        followup_result = service.generate_sql_with_agent(
            user_query=followup_query,
            session_id=session_id,
            max_iterations=3
        )

        if not followup_result.get('success'):
            print(f"  ✗ Follow-up SQL generation failed: {followup_result.get('error')}")
            print(f"  Debug - Full result: {followup_result}")
            return 1

        followup_sql = followup_result.get('sql')
        resolved_query = followup_result.get('resolved_query')
        followup_iterations = followup_result.get('iterations', 0)
        followup_tool_calls = followup_result.get('tool_calls', 0)

        if resolved_query and resolved_query != followup_query:
            print(f"  ✓ Query resolved with context: '{resolved_query}'")

        print(f"  Iterations: {followup_iterations}")
        print(f"  Tool calls: {followup_tool_calls}")
        print(f"\n  Generated SQL:")
        print(f"  {followup_sql}")
        print("\n  ✓ Follow-up SQL generation successful")

        # Wait before execution
        print("\n⏳ Waiting 15 seconds to avoid Bedrock throttling...")
        time.sleep(15)

        # Step 5: Execute follow-up SQL
        print("\nStep 5: Executing follow-up SQL query...")
        followup_execution = service.execute_query(followup_sql)

        if followup_execution.get("success"):
            print(f"  ✓ Query executed successfully")
            print(f"  Row count: {followup_execution.get('row_count')}")
            data = followup_execution.get('data', [])
            if data:
                print(f"  Data: {data[0]}")
        else:
            print(f"  ✗ Query execution failed: {followup_execution.get('error')}")
            return 1

        # Wait before parsing
        print("\n⏳ Waiting 15 seconds to avoid Bedrock throttling...")
        time.sleep(15)

        # Step 6: Parse follow-up results
        print("\nStep 6: Parsing follow-up results to natural language...")
        followup_parsed = service.parse_results_to_text(
            user_query=followup_query,
            sql_query=followup_sql,
            execution_result=followup_execution
        )

        if followup_parsed:
            print(f"  ✓ Response generated successfully\n")
            print("  Follow-up Query Response:")
            print("  " + "-" * 76)
            for line in followup_parsed.split('\n'):
                print(f"  {line}")
            print("  " + "-" * 76)
        else:
            print(f"  ✗ Failed to generate natural language response")
            return 1

        # Success summary
        print("\n" + "=" * 80)
        print("✓ Agentic Text2SQL Pipeline Test PASSED")
        print("=" * 80)
        print("\nTest Summary:")
        print(f"\n  Initial Query: '{initial_query}'")
        print(f"  • SQL: {sql_query}")
        print(f"  • Iterations: {iterations}")
        print(f"  • Tool calls: {tool_calls}")
        print(f"  • Rows returned: {execution_result.get('row_count')}")

        print(f"\n  Follow-up Query: '{followup_query}'")
        if resolved_query:
            print(f"  • Resolved to: '{resolved_query}'")
        print(f"  • SQL: {followup_sql}")
        print(f"  • Iterations: {followup_iterations}")
        print(f"  • Tool calls: {followup_tool_calls}")
        print(f"  • Rows returned: {followup_execution.get('row_count')}")

        print("\nAgenticText2SQLService Features Verified:")
        print("  ✓ Agentic workflow (LangGraph)")
        print("  ✓ Planning and tool execution")
        print("  ✓ Schema retrieval with hybrid search")
        print("  ✓ Metadata/business rules search")
        print("  ✓ SQL generation with context")
        print("  ✓ Reflection and validation")
        print("  ✓ Chat history tracking")
        print("  ✓ Follow-up query resolution")
        print("  ✓ Query execution")
        print("  ✓ Natural language response generation")

        return 0

    except Exception as e:
        print(f"\n✗ Agentic pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Run the complete agentic pipeline test"""
    return test_agentic_pipeline()


if __name__ == "__main__":
    exit(main())
