#!/usr/bin/env python3
"""
Build BM25 index from schema metadata for fast retrieval.

This script should be run once to build the BM25 index from the generated
schema metadata. The index is saved to disk and loaded by the application
at runtime.

Run this script whenever:
- Database schema changes
- Schema metadata is regenerated
- Initial setup of the application
"""

import json
import pickle
import os
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi


class BM25IndexBuilder:
    """Build and save BM25 index from schema metadata"""

    def __init__(self, metadata_path: str, output_dir: str):
        """
        Initialize BM25 index builder

        Args:
            metadata_path: Path to schema_metadata.json file
            output_dir: Directory to save BM25 index and documents
        """
        self.metadata_path = metadata_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def load_schema_metadata(self) -> List[Dict[str, Any]]:
        """
        Load schema metadata from JSON file

        Returns:
            List of schema document dictionaries
        """
        with open(self.metadata_path, 'r') as f:
            return json.load(f)

    def prepare_documents(self, schema_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare documents for BM25 indexing

        Args:
            schema_metadata: List of schema metadata from extraction script

        Returns:
            List of document dictionaries ready for indexing
        """
        documents = []

        for schema_doc in schema_metadata:
            table_name = schema_doc['table_name']
            content = schema_doc['content']

            # Create main schema document
            documents.append({
                'table': table_name,
                'section': 'schema',
                'content': content,
                'metadata': schema_doc.get('metadata', {})
            })

        return documents

    def build_bm25_index(self, documents: List[Dict[str, Any]]) -> BM25Okapi:
        """
        Build BM25 index from documents

        Args:
            documents: List of document dictionaries

        Returns:
            BM25Okapi index object
        """
        # Tokenize documents (simple whitespace tokenization)
        tokenized_docs = [doc['content'].lower().split() for doc in documents]

        # Create BM25 index
        bm25_index = BM25Okapi(tokenized_docs)

        return bm25_index

    def save_index(self, bm25_index: BM25Okapi, documents: List[Dict[str, Any]]):
        """
        Save BM25 index and documents to disk

        Args:
            bm25_index: BM25Okapi index object
            documents: List of document dictionaries
        """
        # Save BM25 index
        index_path = os.path.join(self.output_dir, 'bm25_index.pkl')
        with open(index_path, 'wb') as f:
            pickle.dump(bm25_index, f)
        print(f"✓ Saved BM25 index to: {index_path}")

        # Save documents corpus
        docs_path = os.path.join(self.output_dir, 'metadata_docs.json')
        with open(docs_path, 'w') as f:
            json.dump(documents, f, indent=2)
        print(f"✓ Saved metadata documents to: {docs_path}")

    def build(self):
        """Build complete BM25 index from schema metadata"""
        print("=" * 80)
        print("BM25 Index Builder")
        print("=" * 80)

        # Load schema metadata
        print(f"\n1. Loading schema metadata from: {self.metadata_path}")
        schema_metadata = self.load_schema_metadata()
        print(f"   Loaded {len(schema_metadata)} schema documents")

        # Prepare documents
        print("\n2. Preparing documents for indexing")
        documents = self.prepare_documents(schema_metadata)
        print(f"   Prepared {len(documents)} documents")

        # Build BM25 index
        print("\n3. Building BM25 index")
        bm25_index = self.build_bm25_index(documents)
        print(f"   Index built successfully")

        # Save to disk
        print(f"\n4. Saving index to: {self.output_dir}")
        self.save_index(bm25_index, documents)

        # Print summary
        print("\n" + "=" * 80)
        print("Index Build Complete!")
        print("=" * 80)
        print(f"Total documents indexed: {len(documents)}")
        print(f"Tables covered: {', '.join([d['table'] for d in documents])}")
        print("\nFiles created:")
        print(f"  - {os.path.join(self.output_dir, 'bm25_index.pkl')}")
        print(f"  - {os.path.join(self.output_dir, 'metadata_docs.json')}")
        print("\nThe BM25 retriever is now ready to use!")


def main():
    """Main execution function"""
    # Get paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Input: schema metadata from extract_schema_metadata.py
    metadata_path = os.path.join(script_dir, 'schema_metadata.json')

    # Output: BM25 index files for backend application
    output_dir = os.path.join(project_root, 'backend', 'app', 'data')

    # Validate input file exists
    if not os.path.exists(metadata_path):
        print(f"Error: Schema metadata file not found: {metadata_path}")
        print("\nPlease run extract_schema_metadata.py first to generate schema metadata:")
        print(f"  python {os.path.join(script_dir, 'extract_schema_metadata.py')}")
        return 1

    # Build index
    builder = BM25IndexBuilder(metadata_path, output_dir)
    builder.build()

    return 0


if __name__ == "__main__":
    exit(main())
