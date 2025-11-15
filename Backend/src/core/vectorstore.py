"""
Module for managing Pinecone vector store for similarity search.
"""

from typing import List, Dict, Tuple, Optional
import uuid
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import EMBEDDING_DIMENSION, PINECONE_API_KEY, PINECONE_REGION, PINECONE_INDEX_NAME
from core.embeddings import Embedder

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("Warning: pinecone package not installed. Install it with: pip install pinecone-client")


class VectorStore:
    """
    Class for managing Pinecone vector store and similarity search.
    """
    
    def __init__(self, dimension: int = EMBEDDING_DIMENSION, index_path: Optional[str] = None):
        """
        Initialize the VectorStore.
        
        Args:
            dimension: Dimension of the embedding vectors
            index_path: Deprecated parameter (kept for backwards compatibility, not used with Pinecone)
        """
        if not PINECONE_AVAILABLE:
            raise ImportError("pinecone-client is required. Install it with: pip install pinecone-client")
        
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        self.dimension = dimension
        self.index_name = PINECONE_INDEX_NAME
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Initialize or connect to index (this will recreate if dimension mismatch)
        self._ensure_index_exists()
        
        # Wait a moment if index was just recreated
        time.sleep(1)
        
        # Now connect to the index
        self.index = self.pc.Index(self.index_name)
        
        # Embedder for new documents
        self.embedder = None
    
    def _ensure_index_exists(self):
        """Create the Pinecone index if it doesn't exist, or recreate if dimension mismatch."""
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            print(f"Creating Pinecone index: {self.index_name} with dimension {self.dimension}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=PINECONE_REGION
                )
            )
            print(f"Index {self.index_name} created successfully")
        else:
            # Check if dimension matches
            try:
                index_info = self.pc.describe_index(self.index_name)
                existing_dimension = index_info.dimension
                
                if existing_dimension != self.dimension:
                    print(f"⚠️  WARNING: Index '{self.index_name}' has dimension {existing_dimension}, but expected {self.dimension}")
                    print(f"⚠️  This will cause errors when adding vectors. Recreating index...")
                    
                    # Delete the old index
                    self.pc.delete_index(self.index_name)
                    print(f"Deleted old index: {self.index_name}")
                    
                    # Wait a bit for deletion to complete
                    time.sleep(2)
                    
                    # Create new index with correct dimension
                    print(f"Creating new Pinecone index: {self.index_name} with dimension {self.dimension}")
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=self.dimension,
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud="aws",
                            region=PINECONE_REGION
                        )
                    )
                    print(f"✅ Index {self.index_name} recreated successfully with dimension {self.dimension}")
                else:
                    print(f"Using existing Pinecone index: {self.index_name} (dimension: {self.dimension})")
            except Exception as e:
                print(f"⚠️  Could not verify index dimension: {e}")
                print(f"Using existing Pinecone index: {self.index_name}")
    
    def _initialize_embedder(self):
        """Initialize embedder if not already initialized."""
        if self.embedder is None:
            self.embedder = Embedder()
    
    def add_documents(self, chunks: Dict[str, List[str]], embeddings: Optional[Dict[str, List[List[float]]]] = None):
        """
        Add documents to the vector store.
        
        Args:
            chunks: Dictionary with {file_path: [chunks]}
            embeddings: Optional pre-computed embeddings dictionary
        """
        if not chunks:
            return
        
        if embeddings is None:
            self._initialize_embedder()
            embeddings = self.embedder.embed_chunks(chunks)
        
        # Prepare vectors for Pinecone
        vectors_to_upsert = []
        
        for file_path, chunk_list in chunks.items():
            if file_path in embeddings:
                file_embeddings = embeddings[file_path]
                
                for i, chunk in enumerate(chunk_list):
                    if i < len(file_embeddings):
                        embedding = file_embeddings[i]
                        
                        # Validate embedding dimensions
                        if len(embedding) != self.dimension:
                            print(f"Warning: Embedding dimension mismatch. Expected {self.dimension}, got {len(embedding)}. Skipping chunk.")
                            continue
                        
                        # Generate unique ID for this vector
                        vector_id = str(uuid.uuid4())
                        
                        # Prepare metadata (ensure text is not too long for Pinecone metadata limits)
                        # Pinecone metadata has a limit, so truncate if necessary
                        max_metadata_length = 10000  # Conservative limit
                        chunk_text = chunk[:max_metadata_length] if len(chunk) > max_metadata_length else chunk
                        
                        metadata = {
                            'text': chunk_text,
                            'file_path': file_path,
                            'chunk_index': i
                        }
                        
                        # Prepare vector
                        vector_data = {
                            'id': vector_id,
                            'values': embedding,
                            'metadata': metadata
                        }
                        
                        vectors_to_upsert.append(vector_data)
        
        if not vectors_to_upsert:
            print("Warning: No vectors to add to Pinecone index")
            return
        
        # Upsert vectors to Pinecone in batches (Pinecone recommends batches of 100)
        batch_size = 100
        total_added = 0
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            try:
                self.index.upsert(vectors=batch)
                total_added += len(batch)
            except Exception as e:
                print(f"Error upserting batch {i // batch_size + 1}: {e}")
                raise
        
        print(f"Successfully added {total_added} vectors to Pinecone index {self.index_name}")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query: Query text
            k: Number of results to return (max 10000 for Pinecone)
            
        Returns:
            List of dictionaries with 'text', 'file_path', 'chunk_index', and 'distance'
        """
        if not query or not query.strip():
            return []
        
        # Validate k parameter
        k = max(1, min(k, 10000))  # Pinecone limit is 10000
        
        self._initialize_embedder()
        
        # Generate query embedding
        try:
            query_embedding = self.embedder.embed_text(query)
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return []
        
        # Validate embedding dimensions
        if len(query_embedding) != self.dimension:
            print(f"Error: Query embedding dimension mismatch. Expected {self.dimension}, got {len(query_embedding)}")
            return []
        
        # Search in Pinecone
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=k,
                include_metadata=True
            )
        except Exception as e:
            print(f"Error searching Pinecone: {e}")
            return []
        
        # Format results
        formatted_results = []
        if results.matches:
            for match in results.matches:
                metadata = match.metadata or {}
                formatted_results.append({
                    'text': metadata.get('text', ''),
                    'file_path': metadata.get('file_path', 'Unknown'),
                    'chunk_index': metadata.get('chunk_index', 'N/A'),
                    'distance': 1.0 - match.score if match.score is not None else 1.0,  # Convert cosine similarity to distance
                    'score': match.score if match.score is not None else 0.0  # Also include similarity score
                })
        
        return formatted_results
    
    def save(self):
        """
        Save is not needed for Pinecone as it's cloud-based.
        This method is kept for backwards compatibility.
        """
        print("Note: Pinecone automatically persists data. No explicit save needed.")
        pass
    
    def load(self) -> bool:
        """
        Load is not needed for Pinecone as data is automatically available.
        This method is kept for backwards compatibility.
        
        Returns:
            True if index exists and is accessible
        """
        try:
            # Verify index exists and is accessible
            stats = self.index.describe_index_stats()
            return True
        except Exception as e:
            print(f"Error accessing Pinecone index: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics
        """
        try:
            stats = self.index.describe_index_stats()
            total_vectors = stats.total_vector_count
            
            # Try to get unique file paths by querying metadata
            # Note: This is an approximation using a sample query
            unique_files = set()
            try:
                # Query a small sample to estimate unique files
                sample_results = self.index.query(
                    vector=[0.0] * self.dimension,  # Dummy vector
                    top_k=min(100, total_vectors),
                    include_metadata=True
                )
                if sample_results.matches:
                    for match in sample_results.matches:
                        if match.metadata and 'file_path' in match.metadata:
                            unique_files.add(match.metadata['file_path'])
            except Exception:
                # If query fails, we'll just report N/A
                pass
            
            return {
                'total_vectors': total_vectors,
                'dimension': self.dimension,
                'total_documents': len(unique_files) if unique_files else 'N/A (requires query)',
                'total_chunks': total_vectors,
                'index_name': self.index_name
            }
        except Exception as e:
            print(f"Error getting Pinecone stats: {e}")
            return {
                'total_vectors': 0,
                'dimension': self.dimension,
                'total_documents': 'Error',
                'total_chunks': 0,
                'index_name': self.index_name,
                'error': str(e)
            }
    
    def clear(self):
        """Clear all vectors from the index."""
        try:
            # Delete all vectors by deleting the index and recreating it
            self.pc.delete_index(self.index_name)
            
            # Wait for index deletion to complete (Pinecone may take a moment)
            max_wait = 30  # seconds
            wait_time = 0
            while wait_time < max_wait:
                existing_indexes = [idx.name for idx in self.pc.list_indexes()]
                if self.index_name not in existing_indexes:
                    break
                time.sleep(1)
                wait_time += 1
            
            # Recreate the index
            self._ensure_index_exists()
            self.index = self.pc.Index(self.index_name)
            print(f"Cleared all vectors from index {self.index_name}")
        except Exception as e:
            print(f"Error clearing Pinecone index: {e}")
