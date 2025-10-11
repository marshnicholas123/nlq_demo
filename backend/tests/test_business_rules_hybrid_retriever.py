"""
Test Business Rules Hybrid Retriever

Tests the HybridRetriever with BM25 and semantic search for business rules
"""

import sys
import os
import pytest

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.retrievers.business_rules_hybrid_retriever import HybridRetriever, RetrievalResult


@pytest.fixture
def retriever():
    """Fixture to initialize retriever for all tests"""
    return HybridRetriever(
        embeddings_path="backend/app/data/business_rules_embeddings.pkl",
        embedding_model="cohere.embed-english-v3"
    )


def test_retriever_initialization():
    """Test that retriever initializes correctly and loads embeddings"""
    print("\n" + "=" * 80)
    print("Test 1: Retriever Initialization")
    print("=" * 80)

    # Initialize with correct path
    retriever = HybridRetriever(
        embeddings_path="backend/app/data/business_rules_embeddings.pkl",
        embedding_model="cohere.embed-english-v3"
    )

    # Verify initialization
    assert retriever.documents is not None, "Documents should be loaded"
    assert len(retriever.documents) > 0, "Should have documents loaded"
    assert retriever.embeddings is not None, "Embeddings should be loaded"
    assert retriever.bm25_index is not None, "BM25 index should be built"

    print(f"✓ Retriever initialized successfully")
    print(f"  - Loaded {len(retriever.documents)} documents")
    print(f"  - Embedding dimension: {retriever.embeddings.shape[1]}")
    print(f"  - Embedding model: {retriever.embedding_model}")
    print(f"  - BM25 weight: {retriever.bm25_weight}")
    print(f"  - Semantic weight: {retriever.semantic_weight}")

    return retriever


def test_bm25_retrieval(retriever):
    """Test BM25 keyword-based retrieval"""
    print("\n" + "=" * 80)
    print("Test 2: BM25 Retrieval")
    print("=" * 80)

    test_queries = [
        "operational nuclear power plant",
        "under construction reactor",
        "capacity calculation",
        "decommissioned plants"
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = retriever.retrieve_bm25(query, top_k=3)

        print(f"  Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            assert isinstance(result, RetrievalResult), "Should return RetrievalResult objects"
            assert result.method == 'bm25', "Method should be 'bm25'"
            print(f"    {i}. Score: {result.score:.4f}")
            print(f"       Source: {result.source}")
            print(f"       Section: {result.metadata.get('section', 'N/A')}")
            print(f"       Content preview: {result.content[:80]}...")

    print("\n✓ BM25 retrieval test completed")


def test_semantic_retrieval(retriever):
    """Test semantic similarity-based retrieval"""
    print("\n" + "=" * 80)
    print("Test 3: Semantic Retrieval")
    print("=" * 80)

    test_queries = [
        "How do I count active reactors?",
        "What defines a plant as operational?",
        "Rules for calculating total capacity",
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = retriever.retrieve_semantic(query, top_k=3)

        print(f"  Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            assert isinstance(result, RetrievalResult), "Should return RetrievalResult objects"
            assert result.method == 'semantic', "Method should be 'semantic'"
            print(f"    {i}. Score: {result.score:.4f}")
            print(f"       Source: {result.source}")
            print(f"       Section: {result.metadata.get('section', 'N/A')}")
            print(f"       Content preview: {result.content[:80]}...")

    print("\n✓ Semantic retrieval test completed")


def test_hybrid_retrieval(retriever):
    """Test hybrid retrieval combining BM25 and semantic search"""
    print("\n" + "=" * 80)
    print("Test 4: Hybrid Retrieval")
    print("=" * 80)

    test_queries = [
        "operational status definition",
        "reactor capacity calculations",
        "under construction plants",
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = retriever.retrieve_hybrid(query, top_k=5)

        print(f"  Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            assert isinstance(result, RetrievalResult), "Should return RetrievalResult objects"
            assert result.method == 'hybrid', "Method should be 'hybrid'"
            assert 'bm25_score' in result.metadata, "Should have BM25 score in metadata"
            assert 'semantic_score' in result.metadata, "Should have semantic score in metadata"

            print(f"    {i}. Combined Score: {result.score:.4f}")
            print(f"       BM25: {result.metadata['bm25_score']:.4f} | Semantic: {result.metadata['semantic_score']:.4f}")
            print(f"       Source: {result.source}")
            print(f"       Section: {result.metadata.get('section', 'N/A')}")

    print("\n✓ Hybrid retrieval test completed")


def test_retrieve_method(retriever):
    """Test the main retrieve() method with different methods"""
    print("\n" + "=" * 80)
    print("Test 5: Main retrieve() Method")
    print("=" * 80)

    query = "operational nuclear reactors"
    methods = ['bm25', 'semantic', 'hybrid']

    for method in methods:
        print(f"\nMethod: {method}")
        results = retriever.retrieve(query, method=method, top_k=3)

        print(f"  Retrieved {len(results)} results")
        assert all(r.method == method for r in results), f"All results should use method '{method}'"

        for i, result in enumerate(results, 1):
            print(f"    {i}. Score: {result.score:.4f} | Source: {result.source}")

    # Test invalid method
    try:
        retriever.retrieve(query, method='invalid')
        assert False, "Should raise ValueError for invalid method"
    except ValueError as e:
        print(f"\n✓ Correctly raised error for invalid method: {e}")

    print("\n✓ Main retrieve() method test completed")


def test_format_context(retriever):
    """Test context formatting for LLM consumption"""
    print("\n" + "=" * 80)
    print("Test 6: Context Formatting")
    print("=" * 80)

    query = "operational plant definition"
    results = retriever.retrieve_hybrid(query, top_k=3)

    context = retriever.format_context(results)

    print(f"\nFormatted context length: {len(context)} characters")
    print(f"\nContext preview:")
    print(context[:500] + "...\n")

    # Verify context structure
    assert "[Context 1]" in context, "Should contain context markers"
    assert "Score:" in context, "Should contain scores"
    assert "Method:" in context, "Should contain method info"
    assert "Source:" in context, "Should contain source info"

    # Test with empty results
    empty_context = retriever.format_context([])
    assert "No relevant context found" in empty_context, "Should handle empty results"

    print("✓ Context formatting test completed")


def test_score_normalization(retriever):
    """Test that score normalization works correctly"""
    print("\n" + "=" * 80)
    print("Test 7: Score Normalization")
    print("=" * 80)

    query = "reactor types"

    # Get BM25 results
    bm25_results = retriever.retrieve_bm25(query, top_k=5)
    normalized = retriever._normalize_scores(bm25_results)

    if normalized:
        scores = [r.score for r in normalized]
        print(f"\nOriginal BM25 scores: {[r.score for r in bm25_results]}")
        print(f"Normalized scores: {scores}")

        # Check normalization range
        assert min(scores) >= 0.0, "Min score should be >= 0"
        assert max(scores) <= 1.0, "Max score should be <= 1"

        print("\n✓ Scores are properly normalized to [0, 1] range")

    print("\n✓ Score normalization test completed")


def test_result_deduplication(retriever):
    """Test that hybrid retrieval properly deduplicates results"""
    print("\n" + "=" * 80)
    print("Test 8: Result Deduplication")
    print("=" * 80)

    query = "operational status"

    # Get individual results
    bm25_results = retriever.retrieve_bm25(query, top_k=5)
    semantic_results = retriever.retrieve_semantic(query, top_k=5)

    # Get hybrid results
    hybrid_results = retriever.retrieve_hybrid(query, top_k=10)

    print(f"\nBM25 results: {len(bm25_results)}")
    print(f"Semantic results: {len(semantic_results)}")
    print(f"Hybrid results: {len(hybrid_results)}")

    # Hybrid should have <= sum of both (due to deduplication)
    assert len(hybrid_results) <= len(bm25_results) + len(semantic_results), \
        "Hybrid should deduplicate overlapping results"

    # Check for unique content
    content_keys = set()
    for result in hybrid_results:
        key = retriever._get_result_key(result)
        assert key not in content_keys, "Should not have duplicate results"
        content_keys.add(key)

    print("\n✓ Results are properly deduplicated")
    print("\n✓ Deduplication test completed")


def test_file_paths_validation():
    """Test that all referenced file paths are correct"""
    print("\n" + "=" * 80)
    print("Test 9: File Path Validation")
    print("=" * 80)

    import os
    from pathlib import Path

    # Check embeddings file exists
    embeddings_path = Path("backend/app/data/business_rules_embeddings.pkl")
    assert embeddings_path.exists(), f"Embeddings file not found: {embeddings_path}"
    print(f"✓ Embeddings file exists: {embeddings_path}")

    # Check source markdown file exists
    source_md = Path("table_meta/business_rule.md")
    assert source_md.exists(), f"Source markdown not found: {source_md}"
    print(f"✓ Source markdown exists: {source_md}")

    # Check data directory exists
    data_dir = Path("backend/app/data")
    assert data_dir.exists() and data_dir.is_dir(), f"Data directory not found: {data_dir}"
    print(f"✓ Data directory exists: {data_dir}")

    print("\n✓ All file paths are valid")


def run_all_tests():
    """Run all tests"""
    print("=" * 80)
    print("Business Rules Hybrid Retriever Test Suite")
    print("=" * 80)

    try:
        # Test 1: Initialization
        retriever = test_retriever_initialization()

        # Test 2-8: Various retrieval tests
        test_bm25_retrieval(retriever)
        test_semantic_retrieval(retriever)
        test_hybrid_retrieval(retriever)
        test_retrieve_method(retriever)
        test_format_context(retriever)
        test_score_normalization(retriever)
        test_result_deduplication(retriever)

        # Test 9: File paths
        test_file_paths_validation()

        print("\n" + "=" * 80)
        print("✓ All Tests Passed!")
        print("=" * 80)

        return 0

    except AssertionError as e:
        print(f"\n✗ Test assertion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
