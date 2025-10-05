"""
Schema Retriever Service

This service provides fast retrieval of relevant schema metadata using BM25 algorithm.
The BM25 index is pre-built and loaded from disk for efficient runtime performance.
"""

import json
import pickle
import os
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi


class SchemaRetriever:
    """
    BM25-based retriever for schema metadata.

    Singleton pattern ensures index is loaded only once per application lifecycle.
    """

    _instance: Optional['SchemaRetriever'] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(SchemaRetriever, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize retriever (loads index on first call)"""
        if not SchemaRetriever._initialized:
            self.bm25_index: Optional[BM25Okapi] = None
            self.documents: List[Dict[str, Any]] = []
            self._load_index()
            SchemaRetriever._initialized = True

    def _get_data_dir(self) -> str:
        """Get path to data directory containing BM25 index files"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate up from retrievers -> services -> app to get to app/data
        data_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'data')
        return data_dir

    def _load_index(self):
        """Load pre-built BM25 index and document corpus from disk"""
        data_dir = self._get_data_dir()

        index_path = os.path.join(data_dir, 'bm25_index.pkl')
        docs_path = os.path.join(data_dir, 'metadata_docs.json')

        # Check if index files exist
        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            raise FileNotFoundError(
                f"BM25 index files not found in {data_dir}. "
                "Please run 'python scripts/build_bm25_index.py' to build the index."
            )

        # Load BM25 index
        with open(index_path, 'rb') as f:
            self.bm25_index = pickle.load(f)

        # Load document corpus
        with open(docs_path, 'r') as f:
            self.documents = json.load(f)

        print(f"✓ BM25 Retriever loaded: {len(self.documents)} documents indexed")

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant documents for a query using BM25

        Args:
            query: User query string
            top_k: Number of top documents to return (default: 5)

        Returns:
            List of top-k most relevant document dictionaries, sorted by relevance

        Example:
            >>> retriever = SchemaRetriever()
            >>> docs = retriever.retrieve("countries with nuclear plants", top_k=3)
            >>> for doc in docs:
            ...     print(f"Table: {doc['table']}, Section: {doc['section']}")
        """
        if not self.bm25_index:
            raise RuntimeError("BM25 index not loaded. Call _load_index() first.")

        # Tokenize query
        tokenized_query = query.lower().split()

        # Get BM25 scores
        scores = self.bm25_index.get_scores(tokenized_query)

        # Get top-k indices sorted by score
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        # Filter out documents with zero scores and return top-k
        relevant_docs = [
            {
                **self.documents[i],
                'score': float(scores[i])
            }
            for i in top_indices
            if scores[i] > 0
        ]

        return relevant_docs

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get all indexed documents

        Returns:
            List of all document dictionaries
        """
        return self.documents

    def get_documents_by_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all documents related to a specific table

        Args:
            table_name: Name of the table

        Returns:
            List of document dictionaries for the specified table
        """
        return [doc for doc in self.documents if doc['table'] == table_name]

    def is_initialized(self) -> bool:
        """
        Check if retriever is properly initialized

        Returns:
            True if index is loaded and ready
        """
        return self.bm25_index is not None and len(self.documents) > 0


# Singleton instance for easy access
schema_retriever = SchemaRetriever()
