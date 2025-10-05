"""
Test Schema Retriever Service

This script tests the SchemaRetriever to ensure it properly loads the index
and retrieves relevant schema documents.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.retrievers import SchemaRetriever


def test_retriever_initialization():
    """Test that retriever initializes correctly"""
    print("=" * 80)
    print("Test 1: Retriever Initialization")
    print("=" * 80)

    retriever = SchemaRetriever()

    assert retriever.is_initialized(), "Retriever should be initialized"
    assert len(retriever.get_all_documents()) > 0, "Should have documents loaded"

    print(f"✓ Retriever initialized successfully")
    print(f"✓ Loaded {len(retriever.get_all_documents())} documents")
    print()


def test_retrieval():
    """Test document retrieval with various queries"""
    print("=" * 80)
    print("Test 2: Document Retrieval")
    print("=" * 80)

    retriever = SchemaRetriever()

    # Test queries
    test_queries = [
        "Which countries have nuclear power plants?",
        "What is the total capacity of operational plants?",
        "List all reactor types",
        "Show me nuclear power plant status information"
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        docs = retriever.retrieve(query, top_k=3)

        print(f"  Retrieved {len(docs)} documents:")
        for i, doc in enumerate(docs, 1):
            print(f"    {i}. Table: {doc['table']}, Section: {doc['section']}, Score: {doc.get('score', 0):.4f}")

    print("\n✓ Retrieval test completed")
    print()


def test_table_specific_retrieval():
    """Test retrieving documents for specific tables"""
    print("=" * 80)
    print("Test 3: Table-Specific Retrieval")
    print("=" * 80)

    retriever = SchemaRetriever()

    tables = ['countries', 'nuclear_power_plants', 'nuclear_reactor_types', 'nuclear_power_plant_status_types']

    for table in tables:
        docs = retriever.get_documents_by_table(table)
        print(f"  {table}: {len(docs)} document(s)")

    print("\n✓ Table-specific retrieval test completed")
    print()


def test_schema_content():
    """Test that schema content is properly formatted"""
    print("=" * 80)
    print("Test 4: Schema Content Validation")
    print("=" * 80)

    retriever = SchemaRetriever()

    # Get a document and check its structure
    docs = retriever.retrieve("nuclear power plants", top_k=1)

    if docs:
        doc = docs[0]
        print(f"\nSample document structure:")
        print(f"  Table: {doc['table']}")
        print(f"  Section: {doc['section']}")
        print(f"  Content length: {len(doc['content'])} characters")
        print(f"  Has metadata: {'metadata' in doc}")
        print(f"  Score: {doc.get('score', 0):.4f}")

        # Check if content contains expected schema elements
        content = doc['content']
        assert 'Column Name' in content, "Content should contain 'Column Name'"
        assert 'Data Type' in content, "Content should contain 'Data Type'"
        assert 'Description' in content, "Content should contain 'Description'"

        print("\n✓ Schema content is properly formatted")
    else:
        print("\n✗ No documents retrieved")

    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("Schema Retriever Test Suite")
    print("=" * 80 + "\n")

    try:
        test_retriever_initialization()
        test_retrieval()
        test_table_specific_retrieval()
        test_schema_content()

        print("=" * 80)
        print("All Tests Passed! ✓")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
