"""
Resource Manager: Manages shared resources like VectorStore, LLMs, etc.
Implements Singleton pattern and lazy initialization.
"""

from typing import Optional, Dict, Any
import threading
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.vectorstore import VectorStore
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY


class ResourceManager:
    """
    Manages shared resources across agents.
    Thread-safe singleton implementation with lazy initialization.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ResourceManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._vector_store: Optional[VectorStore] = None
        self._llm_cache: Dict[str, ChatOpenAI] = {}
        self._lock = threading.Lock()
        self._initialized = True
    
    def get_vector_store(self) -> VectorStore:
        """
        Get or create the VectorStore instance.
        Lazy initialization with thread safety.
        """
        if self._vector_store is None:
            with self._lock:
                if self._vector_store is None:
                    self._vector_store = VectorStore()
                    self._vector_store.load()
        return self._vector_store
    
    def get_llm(self, model: str = "gpt-4o-mini", temperature: float = 0.7) -> ChatOpenAI:
        """
        Get or create an LLM instance.
        Caches instances by model and temperature.
        LangSmith tracing is automatically enabled via environment variables.
        
        Args:
            model: Model name
            temperature: Temperature setting
            
        Returns:
            ChatOpenAI instance (automatically traced by LangSmith if configured)
        """
        cache_key = f"{model}_{temperature}"
        
        if cache_key not in self._llm_cache:
            with self._lock:
                if cache_key not in self._llm_cache:
                    # LangSmith tracing is automatically enabled via LANGCHAIN_TRACING_V2 env var
                    self._llm_cache[cache_key] = ChatOpenAI(
                        model=model,
                        temperature=temperature,
                        openai_api_key=OPENAI_API_KEY
                    )
        
        return self._llm_cache[cache_key]
    
    def reset_vector_store(self):
        """Reset the VectorStore instance (useful for testing)."""
        with self._lock:
            self._vector_store = None
    
    def clear_llm_cache(self):
        """Clear the LLM cache."""
        with self._lock:
            self._llm_cache.clear()
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get statistics about resource usage."""
        return {
            "vector_store_initialized": self._vector_store is not None,
            "llm_cache_size": len(self._llm_cache),
            "cached_models": list(self._llm_cache.keys())
        }


# Global instance
_resource_manager = None

def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance."""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager

