#!/usr/bin/env python3
"""
Script to build vector embeddings for database schema metadata using AWS Cohere Embedding Model.

This script:
1. Loads schema metadata from scripts/schema_metadata.json
2. Uses AWS Bedrock Cohere embedding model to generate vector embeddings
3. Saves the embeddings as a pickle file in backend/app/data/
"""

import json
import pickle
import os
from pathlib import Path
import boto3
from typing import List, Dict, Any
import numpy as np


def load_schema_metadata(metadata_path: str) -> List[Dict[str, Any]]:
    """Load schema metadata from JSON file."""
    with open(metadata_path, 'r') as f:
        return json.load(f)


def get_bedrock_client():
    """Initialize AWS Bedrock client."""
    return boto3.client(
        service_name='bedrock-runtime',
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )


def generate_embeddings(texts: List[str], client) -> List[List[float]]:
    """
    Generate embeddings using AWS Bedrock Cohere embedding model.

    Args:
        texts: List of text strings to embed
        client: Boto3 Bedrock client

    Returns:
        List of embedding vectors
    """
    model_id = "cohere.embed-english-v3"
    embeddings = []

    for text in texts:
        body = json.dumps({
            "texts": [text],
            "input_type": "search_document",
            "truncate": "END"
        })

        response = client.invoke_model(
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response['body'].read())
        embedding = response_body['embeddings'][0]
        embeddings.append(embedding)

    return embeddings


def main():
    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    metadata_path = script_dir / "schema_metadata.json"
    output_path = project_root / "backend" / "app" / "data" / "data_schema_vector_embeddings.pkl"

    print(f"Loading schema metadata from: {metadata_path}")
    schema_metadata = load_schema_metadata(str(metadata_path))

    # Extract texts to embed (using the description field)
    texts = [item['description'] for item in schema_metadata]
    table_names = [item['table_name'] for item in schema_metadata]

    print(f"Generating embeddings for {len(texts)} schema documents...")

    # Initialize Bedrock client
    client = get_bedrock_client()

    # Generate embeddings
    embeddings = generate_embeddings(texts, client)

    # Create embeddings data structure
    embeddings_data = {
        'embeddings': np.array(embeddings),
        'table_names': table_names,
        'metadata': schema_metadata,
        'model': 'cohere.embed-english-v3',
        'dimension': len(embeddings[0])
    }

    # Save to pickle file
    print(f"Saving embeddings to: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'wb') as f:
        pickle.dump(embeddings_data, f)

    print(f"✓ Successfully created embeddings file with {len(embeddings)} vectors")
    print(f"  Embedding dimension: {len(embeddings[0])}")
    print(f"  Output file: {output_path}")


if __name__ == "__main__":
    main()
