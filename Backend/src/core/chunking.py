"""
Module for splitting text into chunks for processing.
"""

from typing import List, Dict
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    # Fallback for older langchain versions
    from langchain.text_splitter import RecursiveCharacterTextSplitter
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import CHUNK_SIZE, CHUNK_OVERLAP


class Chunker:
    """
    Class for splitting text documents into smaller chunks.
    """
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """
        Initialize the Chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            
        Raises:
            ValueError: If chunk_size or chunk_overlap are invalid
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split a single text into chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        chunks = self.text_splitter.split_text(text)
        return chunks
    
    def chunk_dict(self, results: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Split multiple texts from a dictionary into chunks.
        
        Args:
            results: Dictionary with {file_path: text}
            
        Returns:
            Dictionary with {file_path: [chunks]}
        """
        chunked_results = {}
        
        for file_path, text in results.items():
            if isinstance(text, str):
                chunks = self.chunk_text(text)
                chunked_results[file_path] = chunks
            elif isinstance(text, list):
                # Already chunked
                chunked_results[file_path] = text
            else:
                chunked_results[file_path] = []
        
        return chunked_results
    
    def chunk_documents(self, documents: List[str]) -> List[str]:
        """
        Split a list of documents into chunks.
        
        Args:
            documents: List of document texts
            
        Returns:
            Flattened list of all chunks
        """
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_text(doc)
            all_chunks.extend(chunks)
        
        return all_chunks
