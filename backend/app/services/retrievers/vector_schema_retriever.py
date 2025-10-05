"""
Vector-based Schema Retriever Service

This service provides semantic retrieval of relevant schema metadata using
AWS Bedrock Cohere embeddings and cosine similarity search.
The embeddings are pre-built and loaded from disk for efficient runtime performance.
"""

import json
import pickle
import os
import boto3
import numpy as np
from typing import List, Dict, Any, Optional
from numpy.linalg import norm


class VectorSchemaRetriever:
    """
    Vector embedding-based retriever for schema metadata using AWS Bedrock Cohere.

    Uses cosine similarity between query embeddings and pre-computed schema embeddings
    to find semantically relevant schema information.

    Singleton pattern ensures embeddings are loaded only once per application lifecycle.
    """

    _instance: Optional['VectorSchemaRetriever'] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(VectorSchemaRetriever, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize retriever (loads embeddings on first call)"""
        if not VectorSchemaRetriever._initialized:
            self.embeddings: Optional[np.ndarray] = None
            self.table_names: List[str] = []
            self.metadata: List[Dict[str, Any]] = []
            self.model: str = ""
            self.dimension: int = 0
            self.bedrock_client = None
            self._load_embeddings()
            self._init_bedrock_client()
            VectorSchemaRetriever._initialized = True

    def _get_data_dir(self) -> str:
        """Get path to data directory containing embedding files"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate up from retrievers -> services -> app to get to app/data
        data_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'data')
        return data_dir

    def _init_bedrock_client(self):
        """Initialize AWS Bedrock client for query embedding"""
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )

    def _load_embeddings(self):
        """Load pre-built embeddings from disk"""
        data_dir = self._get_data_dir()
        embeddings_path = os.path.join(data_dir, 'data_schema_vector_embeddings.pkl')

        # Check if embeddings file exists
        if not os.path.exists(embeddings_path):
            raise FileNotFoundError(
                f"Vector embeddings file not found at {embeddings_path}. "
                "Please run 'python scripts/build_cohere_embeddings.py' to build the embeddings."
            )

        # Load embeddings
        with open(embeddings_path, 'rb') as f:
            embeddings_data = pickle.load(f)

        self.embeddings = embeddings_data['embeddings']
        self.table_names = embeddings_data['table_names']
        self.metadata = embeddings_data['metadata']
        self.model = embeddings_data['model']
        self.dimension = embeddings_data['dimension']

        print(f"✓ Vector Retriever loaded: {len(self.metadata)} schemas with {self.dimension}-dim embeddings")

    def _embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a query using AWS Bedrock Cohere model

        Args:
            query: User query string

        Returns:
            Embedding vector as numpy array
        """
        body = json.dumps({
            "texts": [query],
            "input_type": "search_query",
            "truncate": "END"
        })

        response = self.bedrock_client.invoke_model(
            modelId=self.model,
            body=body,
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response['body'].read())
        embedding = response_body['embeddings'][0]

        return np.array(embedding)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0 to 1)
        """
        return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve most semantically relevant schemas for a query using vector similarity

        Args:
            query: User query string
            top_k: Number of top schemas to return (default: 5)

        Returns:
            List of top-k most relevant schema dictionaries with similarity scores

        Example:
            >>> retriever = VectorSchemaRetriever()
            >>> schemas = retriever.retrieve("countries with nuclear plants", top_k=3)
            >>> for schema in schemas:
            ...     print(f"Table: {schema['table_name']}, Score: {schema['similarity_score']:.3f}")
        """
        if self.embeddings is None or self.bedrock_client is None:
            raise RuntimeError("Vector retriever not properly initialized")

        # Generate query embedding
        query_embedding = self._embed_query(query)

        # Calculate cosine similarities with all schema embeddings
        similarities = []
        for i, schema_embedding in enumerate(self.embeddings):
            similarity = self._cosine_similarity(query_embedding, schema_embedding)
            similarities.append({
                'index': i,
                'similarity': float(similarity)
            })

        # Sort by similarity (descending) and get top-k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = similarities[:top_k]

        # Build result documents with metadata
        results = []
        for result in top_results:
            idx = result['index']
            results.append({
                **self.metadata[idx],
                'similarity_score': result['similarity']
            })

        return results

    def retrieve_by_threshold(
        self,
        query: str,
        similarity_threshold: float = 0.7,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve schemas above a similarity threshold

        Args:
            query: User query string
            similarity_threshold: Minimum similarity score (0 to 1, default: 0.7)
            max_results: Maximum number of results to return (default: 10)

        Returns:
            List of schema dictionaries with similarity above threshold
        """
        all_results = self.retrieve(query, top_k=len(self.metadata))

        # Filter by threshold and limit results
        filtered_results = [
            result for result in all_results
            if result['similarity_score'] >= similarity_threshold
        ][:max_results]

        return filtered_results

    def get_schema_by_table(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get schema metadata for a specific table

        Args:
            table_name: Name of the table

        Returns:
            Schema metadata dictionary or None if not found
        """
        for i, tname in enumerate(self.table_names):
            if tname == table_name:
                return self.metadata[i]
        return None

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """
        Get all schema metadata

        Returns:
            List of all schema dictionaries
        """
        return self.metadata

    def is_initialized(self) -> bool:
        """
        Check if retriever is properly initialized

        Returns:
            True if embeddings are loaded and ready
        """
        return (
            self.embeddings is not None and
            len(self.metadata) > 0 and
            self.bedrock_client is not None
        )


# Singleton instance for easy access
vector_schema_retriever = VectorSchemaRetriever()
