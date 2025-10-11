import pickle
from typing import List, Dict, Tuple
from pathlib import Path
import boto3
from rank_bm25 import BM25Okapi
import numpy as np
from dataclasses import dataclass
import re
import os


@dataclass
class RetrievalResult:
    """Container for retrieval results"""
    content: str
    score: float
    source: str
    metadata: Dict
    method: str  # 'bm25', 'semantic', or 'hybrid'


class HybridRetriever:
    """
    Hybrid retrieval system combining BM25 (keyword) and semantic (embedding) search.
    
    Loads pre-generated embeddings from .pkl file instead of generating them.
    
    Uses:
    - BM25: Fast keyword matching for exact terms and patterns
    - Semantic: Vector similarity search using pre-computed embeddings
    - Hybrid: Combines both with configurable weights
    """
    
    def __init__(
        self,
        embeddings_path: str = None,
        bedrock_region: str = "us-east-1",
        embedding_model: str = "cohere.embed-english-v3",
        bm25_weight: float = 0.6,
        semantic_weight: float = 0.4
    ):
        """
        Initialize hybrid retriever with pre-computed embeddings

        Args:
            embeddings_path: Path to .pkl file with documents and embeddings
            bedrock_region: AWS region for Bedrock (for query embeddings)
            embedding_model: Bedrock embedding model ID (must match embeddings)
            bm25_weight: Weight for BM25 scores (0-1)
            semantic_weight: Weight for semantic scores (0-1)
        """
        # Default to embeddings directory relative to backend/app/data folder (same location as database.py)
        if embeddings_path is None:
            # __file__ is backend/app/services/retrievers/business_rules_hybrid_retriever.py
            # Go up 3 levels to reach backend/app, then navigate to data folder
            backend_app_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            embeddings_path = os.path.join(backend_app_dir, "data", "business_rules_embeddings.pkl")

        self.embeddings_path = Path(embeddings_path)
        self.embedding_model = embedding_model
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        
        # Initialize Bedrock client for query embeddings
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=bedrock_region
        )
        
        # Storage for loaded data
        self.documents = []
        self.embeddings = None
        self.bm25_index = None
        self.tokenized_corpus = []
        
        # Load embeddings and build indices
        self._load_embeddings()
        self._build_bm25_index()
    
    def _load_embeddings(self):
        """Load documents and embeddings from pickle file"""
        if not self.embeddings_path.exists():
            raise FileNotFoundError(
                f"Embeddings file not found: {self.embeddings_path}\n"
                f"Run MetadataEmbedder first to generate embeddings."
            )
        
        print(f"Loading embeddings from {self.embeddings_path}...")
        
        with open(self.embeddings_path, 'rb') as f:
            data = pickle.load(f)
        
        # Load documents
        self.documents = data['documents']
        
        # Load embeddings (convert to numpy if needed)
        self.embeddings = np.array(data['embeddings'])
        
        # Validate
        if len(self.documents) != len(self.embeddings):
            raise ValueError(
                f"Mismatch: {len(self.documents)} documents but {len(self.embeddings)} embeddings"
            )
        
        metadata = data.get('metadata', {})
        print(f"✓ Loaded {len(self.documents)} documents with {metadata.get('embedding_dim', 'unknown')}D embeddings")
        print(f"  Source: {metadata.get('source_dir', 'unknown')}")
        print(f"  Model: {metadata.get('embedding_model', 'unknown')}")
    
    def _build_bm25_index(self):
        """Build BM25 index from documents"""
        print("Building BM25 index...")
        
        # Tokenize all documents
        self.tokenized_corpus = [
            self._tokenize(doc['content']) 
            for doc in self.documents
        ]
        
        # Build BM25 index
        self.bm25_index = BM25Okapi(self.tokenized_corpus)
        
        print(f"✓ BM25 index built with {len(self.tokenized_corpus)} documents")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens (lowercase words)
        """
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def _generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for query text using Bedrock

        Args:
            query: Query text

        Returns:
            Embedding vector as numpy array
        """
        import json

        try:
            # Prepare request body based on model
            if "cohere" in self.embedding_model:
                # Cohere has a 2048 character limit, truncate if needed
                truncated_query = query[:2048] if len(query) > 2048 else query
                body = json.dumps({
                    "texts": [truncated_query],
                    "input_type": "search_query"
                })
            else:  # Titan or other models
                body = json.dumps({
                    "inputText": query
                })

            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.embedding_model,
                body=body,
                contentType='application/json',
                accept='application/json'
            )

            # Parse response based on model
            response_body = json.loads(response['body'].read())

            if "cohere" in self.embedding_model:
                embedding = response_body.get('embeddings', [[]])[0]
            else:  # Titan
                embedding = response_body.get('embedding', [])

            return np.array(embedding, dtype=np.float32)

        except Exception as e:
            print(f"Error generating query embedding: {str(e)}")
            raise
    
    def retrieve_bm25(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve documents using BM25 keyword matching
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects
        """
        # Tokenize query
        tokenized_query = self._tokenize(query)
        
        # Get BM25 scores
        scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        # Build results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                doc = self.documents[idx]
                results.append(RetrievalResult(
                    content=doc['content'],
                    score=float(scores[idx]),
                    source=doc['source'],
                    metadata=doc['metadata'],
                    method='bm25'
                ))
        
        return results
    
    def retrieve_semantic(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieve documents using semantic similarity (cosine similarity)
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects
        """
        # Generate query embedding
        query_embedding = self._generate_query_embedding(query)
        
        # Calculate cosine similarity with all document embeddings
        similarities = self._cosine_similarity(query_embedding, self.embeddings)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Build results
        results = []
        for idx in top_indices:
            doc = self.documents[idx]
            results.append(RetrievalResult(
                content=doc['content'],
                score=float(similarities[idx]),
                source=doc['source'],
                metadata=doc['metadata'],
                method='semantic'
            ))
        
        return results
    
    def _cosine_similarity(self, query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarity between query and document vectors
        
        Args:
            query_vec: Query embedding (1D array)
            doc_vecs: Document embeddings (2D array: num_docs × embedding_dim)
            
        Returns:
            Similarity scores (1D array)
        """
        # Normalize vectors
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        doc_norms = doc_vecs / (np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-10)
        
        # Compute cosine similarity
        similarities = np.dot(doc_norms, query_norm)
        
        return similarities
    
    def retrieve_hybrid(
        self, 
        query: str, 
        top_k: int = 5,
        bm25_k: int = 10,
        semantic_k: int = 10
    ) -> List[RetrievalResult]:
        """
        Retrieve documents using hybrid approach (BM25 + Semantic)
        
        Args:
            query: Search query
            top_k: Number of final results to return
            bm25_k: Number of results from BM25
            semantic_k: Number of results from semantic search
            
        Returns:
            List of RetrievalResult objects, ranked by combined score
        """
        # Get results from both methods
        bm25_results = self.retrieve_bm25(query, top_k=bm25_k)
        semantic_results = self.retrieve_semantic(query, top_k=semantic_k)
        
        # Normalize scores to 0-1 range
        bm25_results = self._normalize_scores(bm25_results)
        semantic_results = self._normalize_scores(semantic_results)
        
        # Combine results with weighted scores
        combined = {}
        
        # Add BM25 results
        for result in bm25_results:
            key = self._get_result_key(result)
            combined[key] = {
                'result': result,
                'bm25_score': result.score * self.bm25_weight,
                'semantic_score': 0.0
            }
        
        # Add/merge semantic results
        for result in semantic_results:
            key = self._get_result_key(result)
            if key in combined:
                combined[key]['semantic_score'] = result.score * self.semantic_weight
            else:
                combined[key] = {
                    'result': result,
                    'bm25_score': 0.0,
                    'semantic_score': result.score * self.semantic_weight
                }
        
        # Calculate final scores and sort
        final_results = []
        for key, data in combined.items():
            final_score = data['bm25_score'] + data['semantic_score']
            result = data['result']
            
            # Create new result with combined score
            final_results.append(RetrievalResult(
                content=result.content,
                score=final_score,
                source=result.source,
                metadata={
                    **result.metadata,
                    'bm25_score': data['bm25_score'],
                    'semantic_score': data['semantic_score']
                },
                method='hybrid'
            ))
        
        # Sort by final score and return top-k
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results[:top_k]
    
    def _normalize_scores(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Normalize scores to 0-1 range using min-max scaling"""
        if not results:
            return results
        
        scores = [r.score for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All scores are the same
            return results
        
        # Normalize
        normalized_results = []
        for result in results:
            normalized_score = (result.score - min_score) / (max_score - min_score)
            normalized_results.append(RetrievalResult(
                content=result.content,
                score=normalized_score,
                source=result.source,
                metadata=result.metadata,
                method=result.method
            ))
        
        return normalized_results
    
    def _get_result_key(self, result: RetrievalResult) -> str:
        """Generate unique key for deduplication"""
        # Use first 100 chars of content + source as key
        content_hash = result.content[:100]
        return f"{result.source}:{content_hash}"
    
    def retrieve(
        self, 
        query: str, 
        method: str = 'hybrid',
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        Main retrieval method
        
        Args:
            query: Search query
            method: 'bm25', 'semantic', or 'hybrid'
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects
        """
        if method == 'bm25':
            return self.retrieve_bm25(query, top_k)
        elif method == 'semantic':
            return self.retrieve_semantic(query, top_k)
        elif method == 'hybrid':
            return self.retrieve_hybrid(query, top_k)
        else:
            raise ValueError(f"Unknown retrieval method: {method}")
    
    def format_context(self, results: List[RetrievalResult]) -> str:
        """
        Format retrieval results into context string for LLM
        
        Args:
            results: List of retrieval results
            
        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant context found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Context {i}] (Score: {result.score:.3f}, Method: {result.method})\n"
                f"Source: {result.source} - {result.metadata.get('section', 'unknown')}\n"
                f"{result.content}\n"
            )
        
        return "\n---\n\n".join(context_parts)

