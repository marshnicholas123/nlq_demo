"""
Test Vector Schema Retriever

Tests the VectorSchemaRetriever with real AWS Bedrock Cohere embeddings
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.retrievers.vector_schema_retriever import vector_schema_retriever


def test_retriever_initialization():
    """Test that retriever initializes correctly"""
    print("\n=== Testing Retriever Initialization ===")

    assert vector_schema_retriever.is_initialized(), "Retriever should be initialized"
    print(f"✓ Retriever initialized successfully")
    print(f"  - Model: {vector_schema_retriever.model}")
    print(f"  - Dimension: {vector_schema_retriever.dimension}")
    print(f"  - Total schemas: {len(vector_schema_retriever.metadata)}")
    print(f"  - Tables: {', '.join(vector_schema_retriever.table_names)}")


def test_basic_retrieval():
    """Test basic retrieval with various queries"""
    print("\n=== Testing Basic Retrieval ===")

    test_queries = [
        ("How many power plants are there in Mexico?", 4),
        ("reactor types and specifications", 2),
        ("power plant operational status", 3),
        ("nuclear facilities by country", 3),
    ]

    for query, top_k in test_queries:
        print(f"\nQuery: '{query}' (top_k={top_k})")
        results = vector_schema_retriever.retrieve(query, top_k=top_k)

        print(f"  Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"    {i}. Table: {result['table_name']}")
            print(f"       Similarity: {result['similarity_score']:.4f}")


def test_threshold_retrieval():
    """Test retrieval with similarity threshold"""
    print("\n=== Testing Threshold-based Retrieval ===")

    query = "nuclear reactor types and their characteristics"
    threshold = 0.3

    print(f"Query: '{query}'")
    print(f"Threshold: {threshold}")

    results = vector_schema_retriever.retrieve_by_threshold(
        query,
        similarity_threshold=threshold,
        max_results=10
    )

    print(f"\nFound {len(results)} results above threshold:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. Table: {result['table_name']}")
        print(f"     Similarity: {result['similarity_score']:.4f}")


def test_get_schema_by_table():
    """Test retrieving schema by table name"""
    print("\n=== Testing Get Schema by Table ===")

    tables = vector_schema_retriever.table_names

    for table_name in tables[:2]:  # Test first 2 tables
        schema = vector_schema_retriever.get_schema_by_table(table_name)
        print(f"\nTable: {table_name}")
        if schema:
            print(f"  ✓ Schema found")
            print(f"  Content preview: {schema['content'][:100]}...")
        else:
            print(f"  ✗ Schema not found")


def test_comparison_with_different_queries():
    """Test how different queries rank the same schemas"""
    print("\n=== Testing Query Variation Impact ===")

    queries = [
        "power plants",
        "nuclear power facilities",
        "atomic energy reactors",
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = vector_schema_retriever.retrieve(query, top_k=2)
        print("  Top 2 results:")
        for i, result in enumerate(results, 1):
            print(f"    {i}. {result['table_name']} (score: {result['similarity_score']:.4f})")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Vector Schema Retriever Test Suite")
    print("=" * 60)

    try:
        test_retriever_initialization()
        test_basic_retrieval()
        test_threshold_retrieval()
        test_get_schema_by_table()
        test_comparison_with_different_queries()

        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()
