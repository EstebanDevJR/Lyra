"""
Analyzer Agent: Analyzes document content and performs semantic search using the vector store.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.vectorstore import VectorStore
from core.chunking import Chunker

# Lazy imports to avoid circular dependencies
def _get_managers():
    """Get managers (lazy import to avoid circular dependencies)."""
    from agents.graph.resource_manager import get_resource_manager
    from agents.graph.context_manager import get_context_manager
    from agents.graph.error_handler import get_error_handler, RetryStrategy
    return get_resource_manager, get_context_manager, get_error_handler, RetryStrategy


def _get_vector_store() -> VectorStore:
    """Get or create the vector store instance using ResourceManager."""
    get_resource_manager, _, _, _ = _get_managers()
    return get_resource_manager().get_vector_store()


def analyzer_tool(query: str, k: int = 5, add_to_store: bool = False, 
                  document_text: Optional[str] = None) -> str:
    """
    Tool function for analyzing document content and performing semantic search.
    Uses ResourceManager, ContextManager, and ErrorHandler for improved reliability.
    
    Args:
        query: Search query or text to analyze
        k: Number of similar documents to retrieve
        add_to_store: If True and document_text is provided, add it to the vector store
        document_text: Optional text to add to the vector store before searching
        
    Returns:
        Formatted string with search results or analysis
    """
    _, get_context_manager, get_error_handler, RetryStrategy = _get_managers()
    context_manager = get_context_manager()
    error_handler = get_error_handler()
    
    def _analyze():
        vector_store = _get_vector_store()
        
        # Check context for previous analysis results
        cached_result = context_manager.get(f"analyzer_result_{hash(query)}")
        if cached_result:
            return cached_result
        
        # If document_text is provided and we should add it, process and add it
        if add_to_store and document_text:
            chunker = Chunker()
            chunks_dict = {"temp_document": chunker.chunk_text(document_text)}
            vector_store.add_documents(chunks_dict)
            vector_store.save()
        
        # Perform semantic search with error handling
        results = error_handler.retry(
            vector_store.search,
            query,
            k=k,
            max_retries=2,
            strategy=RetryStrategy.EXPONENTIAL
        )
        
        if not results:
            return f"No similar documents found for query: '{query}'"
        
        # Format results
        output = [f"Found {len(results)} similar document(s) for query: '{query}'\n"]
        output.append("=" * 60 + "\n")
        
        for i, result in enumerate(results, 1):
            output.append(f"\nResult {i} (distance: {result.get('distance', 'N/A'):.4f}):")
            output.append(f"File: {result.get('file_path', 'Unknown')}")
            output.append(f"Chunk Index: {result.get('chunk_index', 'N/A')}")
            output.append(f"\nText:\n{result.get('text', '')[:500]}...")
            output.append("\n" + "-" * 60 + "\n")
        
        result_str = "\n".join(output)
        
        # Cache result in context
        context_manager.set(f"analyzer_result_{hash(query)}", result_str)
        context_manager.add_tool_result("Analyzer", result_str, {"query": query, "k": k})
        
        return result_str
    
    try:
        return error_handler.safe_execute(_analyze, default_return=f"Error in analysis for query: '{query}'")
    except Exception as e:
        return f"Error in analysis: {str(e)}"


def classify_document(text: str) -> str:
    """
    Classify a document based on its astronomical/astrophysical content.
    
    Args:
        text: Document text to classify
        
    Returns:
        Classification result
    """
    # Use semantic search to find similar documents and infer category
    vector_store = _get_vector_store()
    
    # Common astronomical topics
    topics = [
        "black holes",
        "galaxies",
        "stars",
        "exoplanets",
        "cosmology",
        "dark matter",
        "neutron stars",
        "supernovae",
        "quasars",
        "gravitational waves"
    ]
    
    classifications = []
    for topic in topics:
        results = vector_store.search(f"{topic} {text[:200]}", k=1)
        if results and results[0].get('distance', float('inf')) < 1.5:
            classifications.append(topic)
    
    if classifications:
        return f"Document likely relates to: {', '.join(classifications[:3])}"
    else:
        return "Document classification: General astronomical/astrophysical content"


def identify_key_concepts(text: str, top_k: int = 5) -> str:
    """
    Identify key scientific concepts in the text.
    
    Args:
        text: Text to analyze
        top_k: Number of key concepts to identify
        
    Returns:
        List of key concepts
    """
    # Extract sentences and search for similar content
    sentences = text.split('.')[:10]  # Analyze first 10 sentences
    
    concepts = []
    vector_store = _get_vector_store()
    
    for sentence in sentences:
        if len(sentence.strip()) > 20:
            results = vector_store.search(sentence.strip(), k=1)
            if results:
                # Extract potential concepts from the sentence
                words = sentence.split()
                # Look for capitalized words (potential proper nouns/concepts)
                capitalized = [w.strip('.,;:!?') for w in words if w[0].isupper() and len(w) > 2]
                concepts.extend(capitalized[:2])
    
    # Remove duplicates and return
    unique_concepts = list(dict.fromkeys(concepts))[:top_k]
    
    if unique_concepts:
        return f"Key concepts identified: {', '.join(unique_concepts)}"
    else:
        return "Key concepts: Unable to identify specific concepts"

