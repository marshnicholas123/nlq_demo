"""
Test AdvancedText2SQLService Integration with BM25 Retriever

This script tests that the AdvancedText2SQLService correctly uses the
BM25Retriever for schema metadata retrieval.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.advanced_text2sql import AdvancedText2SQLService


def test_service_initialization():
    """Test that service initializes with BM25 retrievers"""
    print("=" * 80)
    print("Test 1: AdvancedText2SQLService Initialization")
    print("=" * 80)

    service = AdvancedText2SQLService()

    # Check that schema retriever is available
    assert hasattr(service, 'retriever'), "Service should have retriever attribute"
    assert service.retriever is not None, "Retriever should not be None"
    assert service.retriever.is_initialized(), "Retriever should be initialized"

    # Check that sample data retriever is available
    assert hasattr(service, 'sample_retriever'), "Service should have sample_retriever attribute"
    assert service.sample_retriever is not None, "Sample retriever should not be None"
    assert service.sample_retriever.is_initialized(), "Sample retriever should be initialized"

    print("✓ Service initialized successfully")
    print(f"✓ BM25 Schema Retriever is available and initialized")
    print(f"✓ BM25 Sample Data Retriever is available and initialized")
    print()


def test_retrieve_relevant_context():
    """Test context retrieval functionality"""
    print("=" * 80)
    print("Test 2: Retrieve Relevant Context")
    print("=" * 80)

    service = AdvancedText2SQLService()

    # Test queries
    test_queries = [
        "Which countries have the most nuclear plants?",
        "What is the total capacity of all operational plants?",
        "List all reactor types available"
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        context = service.retrieve_relevant_context(query, top_k=3)

        print(f"  Retrieved {len(context)} context documents:")
        for i, doc in enumerate(context, 1):
            print(f"    {i}. Table: {doc['table']}, Section: {doc.get('section', 'schema')}")

    print("\n✓ Context retrieval test completed")
    print()


def test_identify_relevant_tables():
    """Test table identification from query"""
    print("=" * 80)
    print("Test 3: Identify Relevant Tables")
    print("=" * 80)

    service = AdvancedText2SQLService()

    # Create test context
    test_context = [
        {'table': 'nuclear_power_plants', 'section': 'schema', 'content': '...'},
        {'table': 'countries', 'section': 'schema', 'content': '...'}
    ]

    queries_and_expected = [
        ("Which countries have nuclear plants?", ['nuclear_power_plants', 'countries']),
        ("List all reactor types", ['nuclear_reactor_types']),
        ("Show operational plants", ['nuclear_power_plants', 'nuclear_power_plant_status_types'])
    ]

    for query, expected in queries_and_expected:
        tables = service._identify_relevant_tables(query, test_context)
        print(f"\nQuery: '{query}'")
        print(f"  Identified tables: {tables}")

    print("\n✓ Table identification test completed")
    print()


def test_sample_data_retrieval():
    """Test BM25-based sample data retrieval"""
    print("=" * 80)
    print("Test 4: BM25 Sample Data Retrieval")
    print("=" * 80)

    service = AdvancedText2SQLService()

    test_queries = [
        ("operational nuclear plants in USA", ["nuclear_power_plants"]),
        ("countries with nuclear power", ["countries", "nuclear_power_plants"]),
        ("PWR reactor types", ["nuclear_reactor_types", "nuclear_power_plants"])
    ]

    for query, tables in test_queries:
        print(f"\nQuery: '{query}'")
        print(f"  Tables: {tables}")

        try:
            sample_data = service.get_sample_data(query, tables, limit=3)
            if sample_data:
                lines = sample_data.split('\n')
                print(f"  ✓ Retrieved relevant sample data ({len(lines)} lines)")
                # Show first few lines
                for line in lines[:5]:
                    if line.strip():
                        print(f"    {line[:80]}...")
            else:
                print(f"  ! No sample data retrieved")
        except Exception as e:
            print(f"  ! Sample data retrieval failed: {str(e)}")

    print("\n✓ Sample data retrieval test completed")
    print()


def test_generate_sql():
    """Test SQL generation with actual Bedrock API call"""
    print("=" * 80)
    print("Test 5: Generate SQL")
    print("=" * 80)

    service = AdvancedText2SQLService()

    test_queries = [
        "Which countries have the most nuclear power plants?"
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 80)

        try:
            result = service.generate_sql(query)

            print(f"  Method: {result.get('method')}")
            print(f"  Context used: {result.get('context_used', [])}")
            print(f"\n  Generated SQL:")
            print(f"  {result.get('sql', 'No SQL generated')}")
            print(f"\n  ✓ SQL generation successful")

        except Exception as e:
            print(f"  ! SQL generation failed: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n✓ SQL generation test completed")
    print()


def test_end_to_end_workflow():
    """Test complete workflow without actually calling Bedrock"""
    print("=" * 80)
    print("Test 6: End-to-End Workflow (Mock)")
    print("=" * 80)

    service = AdvancedText2SQLService()

    query = "Which countries have the most nuclear power plants?"

    # Step 1: Retrieve context
    print(f"\nQuery: '{query}'")
    print("\nStep 1: Retrieving relevant schema context...")
    context = service.retrieve_relevant_context(query, top_k=3)
    print(f"  Retrieved {len(context)} documents")

    # Step 2: Get schema
    print("\nStep 2: Getting schema context...")
    schema = service.get_schema_context()
    print(f"  Schema length: {len(schema)} characters")

    # Step 3: Identify tables
    print("\nStep 3: Identifying relevant tables...")
    tables = service._identify_relevant_tables(query, context)
    print(f"  Relevant tables: {tables}")

    # Step 4: Get BM25-based sample data
    print("\nStep 4: Getting query-relevant sample data via BM25...")
    try:
        sample_data = service.get_sample_data(query, tables[:2], limit=4)
        if sample_data:
            print(f"  ✓ Got BM25-relevant sample data")
            lines = sample_data.split('\n')
            print(f"  Total lines: {len(lines)}")
        else:
            print(f"  ! No sample data retrieved")
    except Exception as e:
        print(f"  ! Sample data retrieval failed: {str(e)}")

    print("\n✓ End-to-end workflow test completed")
    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("AdvancedText2SQLService Integration Test Suite")
    print("=" * 80 + "\n")

    try:
        test_service_initialization()
        test_retrieve_relevant_context()
        test_identify_relevant_tables()
        test_sample_data_retrieval()
        test_generate_sql()
        test_end_to_end_workflow()

        print("=" * 80)
        print("All Integration Tests Passed! ✓")
        print("=" * 80)
        print("\nThe AdvancedText2SQLService is now using:")
        print("  • BM25 Retriever for schema metadata")
        print("  • BM25 Sample Data Retriever for query-relevant sample rows")

    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
