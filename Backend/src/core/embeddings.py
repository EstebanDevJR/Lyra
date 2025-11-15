"""
Module for creating embeddings from text using OpenAI.
These embeddings are used with Pinecone vector store for semantic search.
Uses OpenAI's text-embedding-3-small model (1536 dimensions).
"""

from typing import List, Dict, Union
from langchain_openai import OpenAIEmbeddings
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import EMBEDDING_MODEL, OPENAI_API_KEY


class Embedder:
    """
    Class for generating embeddings from text using OpenAI.
    
    These embeddings are used with Pinecone vector store for semantic search.
    By default uses OpenAI's text-embedding-3-small model (1536 dimensions).
    """
    
    def __init__(self, model: str = EMBEDDING_MODEL, api_key: str = None):
        """
        Initialize the Embedder.
        
        Args:
            model: Name of the embedding model to use
            api_key: OpenAI API key (if None, uses OPENAI_API_KEY env var)
        """
        self.model = model
        self.api_key = api_key or OPENAI_API_KEY
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.embeddings = OpenAIEmbeddings(
            model=self.model,
            openai_api_key=self.api_key
        )
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            embedding = self.embeddings.embed_query(text)
            if not embedding or len(embedding) == 0:
                raise ValueError("Empty embedding returned from OpenAI")
            return embedding
        except Exception as e:
            raise ValueError(f"Error generating embedding: {str(e)}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        
        if not valid_texts:
            return []
        
        embeddings = self.embeddings.embed_documents(valid_texts)
        return embeddings
    
    def embed_chunks(self, chunks: Dict[str, List[str]]) -> Dict[str, List[List[float]]]:
        """
        Generate embeddings for chunks from multiple files.
        
        Args:
            chunks: Dictionary with {file_path: [chunks]}
            
        Returns:
            Dictionary with {file_path: [embeddings]}
        """
        embedded_results = {}
        
        for file_path, chunk_list in chunks.items():
            if isinstance(chunk_list, list) and chunk_list:
                # Embed all chunks for this file
                embeddings = self.embed_documents(chunk_list)
                embedded_results[file_path] = embeddings
            else:
                embedded_results[file_path] = []
        
        return embedded_results
    
    def embed_single_chunk(self, chunk: str) -> List[float]:
        """
        Generate embedding for a single chunk.
        
        Args:
            chunk: Single text chunk
            
        Returns:
            Embedding vector
        """
        return self.embed_text(chunk)
