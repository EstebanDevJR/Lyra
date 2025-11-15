"""
Context Agent: Adds background information and context about scientific findings.
"""

import sys
from pathlib import Path
from typing import Optional, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from core.vectorstore import VectorStore
from config import OPENAI_API_KEY


def contextualizer_tool(text: str, topic: Optional[str] = None) -> str:
    """
    Tool function for adding background context about scientific findings.
    
    Args:
        text: Text to contextualize
        topic: Specific topic to provide context about (optional)
        
    Returns:
        Text with added context
    """
    if not text:
        return "No text provided for contextualization."
    
    try:
        # Try to find related context from vector store
        vector_store = VectorStore()
        vector_store.load()
        
        # Search for related content
        search_query = topic if topic else text[:200]
        related_docs = vector_store.search(search_query, k=3)
        
        # Build context from related documents
        context_info = []
        if related_docs:
            context_info.append("Related information found:")
            for doc in related_docs:
                context_info.append(f"- {doc.get('text', '')[:200]}...")
        
        # Use LLM to add context
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.5,
            openai_api_key=OPENAI_API_KEY
        )
        
        related_context = "\n".join(context_info) if context_info else "No related context found in knowledge base."
        
        prompt = f"""You are a scientific context assistant specializing in astronomy and astrophysics.

Your task is to add relevant background context to the following scientific text. Provide context that helps understand:
- Historical background
- Related discoveries or theories
- Significance of the findings
- Connections to other areas of astronomy

Original text:
{text[:2000]}

{related_context}

Provide additional context in Spanish that enhances understanding of this text. Be concise but informative."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return f"{text}\n\n--- Contexto adicional ---\n\n{response.content}"
        else:
            return f"{text}\n\n--- Contexto adicional ---\n\n{str(response)}"
            
    except Exception as e:
        return f"{text}\n\n(Note: Error adding context: {str(e)})"


def add_historical_context(text: str) -> str:
    """
    Add historical context about discoveries mentioned in the text.
    
    Args:
        text: Text to add historical context to
        
    Returns:
        Text with historical context
    """
    return contextualizer_tool(text, topic="historical discoveries")


def add_theoretical_context(text: str) -> str:
    """
    Add theoretical context explaining underlying physics/astrophysics.
    
    Args:
        text: Text to add theoretical context to
        
    Returns:
        Text with theoretical context
    """
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.4,
            openai_api_key=OPENAI_API_KEY
        )
        
        prompt = f"""You are an astrophysics educator. Explain the theoretical background and underlying physics concepts relevant to this text.

Text:
{text[:2000]}

Provide a clear explanation in Spanish of the relevant theoretical concepts, equations, or physical principles."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return f"{text}\n\n--- Theoretical Context ---\n\n{response.content}"
        else:
            return f"{text}\n\n--- Theoretical Context ---\n\n{str(response)}"
            
    except Exception as e:
        return f"{text}\n\n(Error adding theoretical context: {str(e)})"

