"""
Test script for enhanced AgenticText2SQLService

Demonstrates:
1. Session management and conversation context
2. Follow-up query resolution
3. Reflection on SQL quality
4. Clarification detection
5. Tool-based approach with LangGraph orchestration
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.agentic_text2sql import AgenticText2SQLService
import uuid


def test_basic_query():
    """Test 1: Basic query with agentic approach"""
    print("\n" + "="*80)
    print("TEST 1: Basic Query with Agentic Approach")
    print("="*80)

    service = AgenticText2SQLService()
    session_id = str(uuid.uuid4())

    query = "How many nuclear power plants are operational?"
    print(f"\nQuery: {query}")

    result = service.generate_sql_with_agent(
        user_query=query,
        session_id=session_id,
        max_iterations=3
    )

    print(f"\nResult:")
    print(f"  Success: {result.get('success')}")
    print(f"  Method: {result.get('method')}")
    print(f"  SQL: {result.get('sql')}")
    print(f"  Iterations: {result.get('iterations')}")
    print(f"  Tool Calls: {result.get('tool_calls')}")
    print(f"  Reflection: {result.get('reflection')}")

    return service, session_id


def test_follow_up_query(service, session_id):
    """Test 2: Follow-up query using conversation context"""
    print("\n" + "="*80)
    print("TEST 2: Follow-up Query with Conversation Context")
    print("="*80)

    follow_up = "What about in the United States?"
    print(f"\nFollow-up Query: {follow_up}")

    result = service.generate_sql_with_agent(
        user_query=follow_up,
        session_id=session_id,
        max_iterations=3
    )

    print(f"\nResult:")
    print(f"  Resolved Query: {result.get('resolved_query')}")
    print(f"  SQL: {result.get('sql')}")
    print(f"  Used Context: {result.get('context_used')}")


def test_clarification_detection():
    """Test 3: Ambiguous query triggering clarification"""
    print("\n" + "="*80)
    print("TEST 3: Clarification Detection")
    print("="*80)

    service = AgenticText2SQLService()
    session_id = str(uuid.uuid4())

    ambiguous_query = "Show me the data"
    print(f"\nAmbiguous Query: {ambiguous_query}")

    result = service.generate_sql_with_agent(
        user_query=ambiguous_query,
        session_id=session_id,
        max_iterations=3
    )

    print(f"\nResult:")
    print(f"  Needs Clarification: {result.get('needs_clarification')}")
    if result.get('needs_clarification'):
        print(f"  Questions:")
        for i, q in enumerate(result.get('questions', []), 1):
            print(f"    {i}. {q}")


def test_conversation_history():
    """Test 4: Multiple turns building conversation history"""
    print("\n" + "="*80)
    print("TEST 4: Multi-turn Conversation History")
    print("="*80)

    service = AgenticText2SQLService()
    session_id = str(uuid.uuid4())

    queries = [
        "List nuclear power plants in France",
        "How many reactors do they have?",
        "What is the total capacity?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n--- Turn {i} ---")
        print(f"Query: {query}")

        result = service.generate_sql_with_agent(
            user_query=query,
            session_id=session_id,
            max_iterations=3
        )

        print(f"Resolved: {result.get('resolved_query') or 'N/A'}")
        print(f"SQL: {result.get('sql')}")

    # Check history
    history = service._get_chat_history(session_id)
    print(f"\n--- Session History Summary ---")
    print(f"Total entries: {len(history)}")


def test_reflection_mechanism():
    """Test 5: SQL reflection and quality validation"""
    print("\n" + "="*80)
    print("TEST 5: Reflection and Quality Validation")
    print("="*80)

    service = AgenticText2SQLService()
    session_id = str(uuid.uuid4())

    # Complex query that might need refinement
    query = "Show average reactor capacity by country with more than 5 plants"
    print(f"\nComplex Query: {query}")

    result = service.generate_sql_with_agent(
        user_query=query,
        session_id=session_id,
        max_iterations=5  # Allow more iterations for refinement
    )

    print(f"\nResult:")
    print(f"  SQL: {result.get('sql')}")
    print(f"  Iterations: {result.get('iterations')}")

    reflection = result.get('reflection', {})
    if reflection:
        print(f"\n  Reflection:")
        print(f"    Acceptable: {reflection.get('is_acceptable')}")
        print(f"    Confidence: {reflection.get('confidence')}")
        print(f"    Issues: {reflection.get('issues')}")
        print(f"    Should Refine: {reflection.get('should_refine')}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("ENHANCED AGENTIC TEXT2SQL SERVICE - TEST SUITE")
    print("="*80)

    try:
        # Test 1 & 2: Basic query and follow-up
        service, session_id = test_basic_query()
        test_follow_up_query(service, session_id)

        # Test 3: Clarification detection
        test_clarification_detection()

        # Test 4: Conversation history
        test_conversation_history()

        # Test 5: Reflection mechanism
        test_reflection_mechanism()

        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)

    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
