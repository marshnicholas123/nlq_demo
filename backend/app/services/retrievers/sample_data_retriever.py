"""
Sample Data BM25 Retriever Service

This service provides fast retrieval of relevant sample data rows using BM25 algorithm.
The BM25 index is pre-built from database rows and loaded from disk for efficient runtime performance.
"""

import json
import pickle
import os
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi


class SampleDataRetriever:
    """
    BM25-based retriever for database sample data.

    Singleton pattern ensures index is loaded only once per application lifecycle.
    """

    _instance: Optional['SampleDataRetriever'] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(SampleDataRetriever, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize retriever (loads index on first call)"""
        if not SampleDataRetriever._initialized:
            self.bm25_index: Optional[BM25Okapi] = None
            self.sample_data: List[Dict[str, Any]] = []
            self._load_index()
            SampleDataRetriever._initialized = True

    def _get_data_dir(self) -> str:
        """Get path to data directory containing BM25 index files"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate up from retrievers -> services -> app to get to app/data
        data_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'data')
        return data_dir

    def _load_index(self):
        """Load pre-built BM25 index and sample data corpus from disk"""
        data_dir = self._get_data_dir()

        index_path = os.path.join(data_dir, 'sample_data_bm25_index.pkl')
        docs_path = os.path.join(data_dir, 'sample_data_docs.json')

        # Check if index files exist
        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            raise FileNotFoundError(
                f"Sample data BM25 index files not found in {data_dir}. "
                "Please run 'python scripts/build_sample_data_index.py' to build the index."
            )

        # Load BM25 index
        with open(index_path, 'rb') as f:
            self.bm25_index = pickle.load(f)

        # Load sample data corpus
        with open(docs_path, 'r') as f:
            self.sample_data = json.load(f)

        print(f"✓ Sample Data Retriever loaded: {len(self.sample_data)} rows indexed")

    def retrieve(self, query: str, table_name: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant sample data rows for a specific table

        Args:
            query: User query string
            table_name: Name of the table to retrieve rows from
            top_k: Number of top rows to return (default: 4)

        Returns:
            List of top-k most relevant sample data dictionaries for the table

        Example:
            >>> retriever = SampleDataRetriever()
            >>> rows = retriever.retrieve("operational nuclear plants in USA", "nuclear_power_plants", top_k=4)
            >>> for row in rows:
            ...     print(f"Row: {row['raw_data']}")
        """
        if not self.bm25_index:
            raise RuntimeError("BM25 index not loaded. Call _load_index() first.")

        # Filter sample data for the specific table
        table_indices = [
            i for i, data in enumerate(self.sample_data)
            if data['table_name'] == table_name
        ]

        if not table_indices:
            return []

        # Tokenize query
        tokenized_query = query.lower().split()

        # Get BM25 scores for all documents
        all_scores = self.bm25_index.get_scores(tokenized_query)

        # Filter scores for this table only and get top-k
        table_scores = [(i, all_scores[i]) for i in table_indices]
        table_scores.sort(key=lambda x: x[1], reverse=True)

        # Get top-k indices with scores > 0
        top_indices = [
            i for i, score in table_scores[:top_k]
            if score > 0
        ]

        # Return relevant sample data with scores
        relevant_rows = [
            {
                **self.sample_data[i],
                'score': float(all_scores[i])
            }
            for i in top_indices
        ]

        return relevant_rows

    def retrieve_multi_table(
        self,
        query: str,
        table_names: List[str],
        top_k: int = 4
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve relevant sample data rows across multiple tables

        Args:
            query: User query string
            table_names: List of table names to retrieve rows from
            top_k: Number of top rows to return per table (default: 4)

        Returns:
            Dictionary mapping table names to lists of relevant sample data

        Example:
            >>> retriever = SampleDataRetriever()
            >>> results = retriever.retrieve_multi_table(
            ...     "operational nuclear plants in USA",
            ...     ["nuclear_power_plants", "countries"],
            ...     top_k=4
            ... )
            >>> for table, rows in results.items():
            ...     print(f"{table}: {len(rows)} rows")
        """
        results = {}

        for table_name in table_names:
            rows = self.retrieve(query, table_name, top_k=top_k)

            # If no relevant rows found, fall back to first N rows from table
            if not rows:
                table_data = self.get_sample_data_by_table(table_name)
                if table_data:
                    rows = table_data[:top_k]
                    # Add score of 0 to indicate these are fallback results
                    for row in rows:
                        row['score'] = 0.0

            if rows:  # Include table if we have any data
                results[table_name] = rows

        return results

    def get_all_sample_data(self) -> List[Dict[str, Any]]:
        """
        Get all indexed sample data

        Returns:
            List of all sample data dictionaries
        """
        return self.sample_data

    def get_sample_data_by_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all sample data for a specific table

        Args:
            table_name: Name of the table

        Returns:
            List of sample data dictionaries for the specified table
        """
        return [data for data in self.sample_data if data['table_name'] == table_name]

    def is_initialized(self) -> bool:
        """
        Check if retriever is properly initialized

        Returns:
            True if index is loaded and ready
        """
        return self.bm25_index is not None and len(self.sample_data) > 0


# Singleton instance for easy access
sample_data_retriever = SampleDataRetriever()
