import os
import re
import pickle
from typing import List, Dict
from pathlib import Path
import boto3
import numpy as np
from dataclasses import dataclass
import json


@dataclass
class DocumentChunk:
    """Container for document chunks"""
    content: str
    title: str
    section: str
    source: str
    metadata: Dict


class MetadataEmbedder:
    """
    Generates embeddings for metadata documents and saves them locally.
    Run this once to create embeddings, then use HybridRetriever to load them.
    """
    
    def __init__(
        self, 
        metadata_dir: str = "table_meta/tables",
        output_dir: str = "backend/app/data",
        bedrock_region: str = "us-east-1",
        embedding_model: str = "cohere.embed-english-v3"
    ):
        """
        Initialize embedder
        
        Args:
            metadata_dir: Directory containing markdown files
            output_dir: Directory to save embeddings (.pkl files)
            bedrock_region: AWS region for Bedrock
            embedding_model: Bedrock embedding model ID
        """
        self.metadata_dir = Path(metadata_dir)
        self.output_dir = Path(output_dir)
        self.embedding_model = embedding_model
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=bedrock_region
        )
        
        self.documents = []
        self.embeddings = []
    
    def load_documents(self):
        """Load all markdown files and chunk them"""
        print(f"Loading documents from {self.metadata_dir}")

        # Load business_rule.md file from table_meta directory
        # metadata_dir defaults to "table_meta/tables", so parent gets us to "table_meta"
        business_rules_file = self.metadata_dir.parent / "business_rule.md"

        if business_rules_file.exists():
            md_files = [business_rules_file]
        else:
            md_files = []
            print(f"Warning: business_rule.md not found at {business_rules_file}")

        for md_file in md_files:
            print(f"  Loading {md_file.name}")
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Chunk the document by sections
            chunks = self._chunk_markdown(content, md_file.name)
            self.documents.extend(chunks)

        print(f"Loaded {len(self.documents)} document chunks from {len(md_files)} files")
    
    def _chunk_markdown(self, content: str, filename: str) -> List[DocumentChunk]:
        """
        Chunk markdown document by sections (## headers)
        
        Args:
            content: Markdown content
            filename: Source file name
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        
        # Split by ## headers (second-level headers)
        sections = re.split(r'\n## ', content)
        
        # First section is before first ## header (could be # title + overview)
        if sections[0].strip():
            # Extract title from # if present
            title_match = re.match(r'# (.+?)\n', sections[0])
            title = title_match.group(1) if title_match else "Overview"
            
            chunks.append(DocumentChunk(
                content=sections[0].strip(),
                title=title,
                section='overview',
                source=filename,
                metadata={
                    'file': filename,
                    'section': 'overview',
                    'chunk_type': 'overview'
                }
            ))
        
        # Process remaining sections
        for section in sections[1:]:
            # Extract section title (first line after ##)
            lines = section.split('\n', 1)
            section_title = lines[0].strip()
            section_content = lines[1].strip() if len(lines) > 1 else ""
            
            if section_content:
                chunks.append(DocumentChunk(
                    content=f"## {section_title}\n\n{section_content}",
                    title=section_title,
                    section=self._normalize_section_name(section_title),
                    source=filename,
                    metadata={
                        'file': filename,
                        'section': section_title,
                        'chunk_type': 'section'
                    }
                ))
        
        return chunks
    
    def _normalize_section_name(self, title: str) -> str:
        """Convert section title to normalized name"""
        return re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text using Bedrock

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array
        """
        try:
            # Prepare request body based on model
            if "cohere" in self.embedding_model:
                # Cohere has a 2048 character limit, truncate if needed
                truncated_text = text[:2048] if len(text) > 2048 else text
                body = json.dumps({
                    "texts": [truncated_text],
                    "input_type": "search_document"
                })
            else:  # Titan or other models
                body = json.dumps({
                    "inputText": text
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
            print(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_all_embeddings(self, batch_size: int = 10):
        """
        Generate embeddings for all documents
        
        Args:
            batch_size: Number of documents to process before saving checkpoint
        """
        if not self.documents:
            print("No documents loaded. Call load_documents() first.")
            return
        
        print(f"\nGenerating embeddings for {len(self.documents)} documents...")
        print(f"Using model: {self.embedding_model}")
        
        self.embeddings = []
        
        for i, doc in enumerate(self.documents, 1):
            try:
                # Generate embedding
                embedding = self.generate_embedding(doc.content)
                self.embeddings.append(embedding)
                
                # Progress indicator
                if i % 10 == 0:
                    print(f"  Processed {i}/{len(self.documents)} documents...")
                
                # Save checkpoint every batch_size documents
                if i % batch_size == 0:
                    self._save_checkpoint(i)
                    
            except Exception as e:
                print(f"  Error on document {i}: {str(e)}")
                # Store zero vector as placeholder
                self.embeddings.append(np.zeros(1024, dtype=np.float32))  # Titan v2 = 1024 dims
        
        print(f"✓ Generated {len(self.embeddings)} embeddings")
    
    def _save_checkpoint(self, index: int):
        """Save intermediate checkpoint"""
        checkpoint_file = self.output_dir / f"checkpoint_{index}.pkl"
        with open(checkpoint_file, 'wb') as f:
            pickle.dump({
                'documents': self.documents[:index],
                'embeddings': self.embeddings[:index]
            }, f)
        print(f"  Checkpoint saved: {checkpoint_file}")
    
    def save_embeddings(self, filename: str = "metadata_embeddings.pkl"):
        """
        Save documents and embeddings to pickle file
        
        Args:
            filename: Output filename (saved in output_dir)
        """
        if not self.embeddings:
            print("No embeddings to save. Generate embeddings first.")
            return
        
        output_path = self.output_dir / filename
        
        # Prepare data structure
        data = {
            'documents': [
                {
                    'content': doc.content,
                    'title': doc.title,
                    'section': doc.section,
                    'source': doc.source,
                    'metadata': doc.metadata
                }
                for doc in self.documents
            ],
            'embeddings': np.array(self.embeddings),
            'metadata': {
                'num_documents': len(self.documents),
                'embedding_dim': self.embeddings[0].shape[0] if self.embeddings else 0,
                'embedding_model': self.embedding_model,
                'source_dir': str(self.metadata_dir)
            }
        }
        
        # Save to pickle
        with open(output_path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"\n✓ Embeddings saved to: {output_path}")
        print(f"  - Documents: {len(self.documents)}")
        print(f"  - Embedding dimension: {data['metadata']['embedding_dim']}")
        print(f"  - File size: {output_path.stat().st_size / 1024:.2f} KB")
    
    def run_full_pipeline(self, output_filename: str = "business_rules_embeddings.pkl"):
        """
        Complete pipeline: load documents, generate embeddings, save
        
        Args:
            output_filename: Output pickle filename
        """
        print("="*80)
        print("METADATA EMBEDDING PIPELINE")
        print("="*80)
        
        # Step 1: Load documents
        self.load_documents()
        
        # Step 2: Generate embeddings
        self.generate_all_embeddings()
        
        # Step 3: Save to file
        self.save_embeddings(output_filename)
        
        print("\n✓ Pipeline completed successfully!")


if __name__ == "__main__":
    embedder = MetadataEmbedder()
    embedder.run_full_pipeline()