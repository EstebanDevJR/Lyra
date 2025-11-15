"""
Context Manager: Manages shared context between agents and tools.
Implements Singleton pattern for global context access.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
from collections import defaultdict


class ContextManager:
    """
    Manages shared context between agents and tools.
    Thread-safe singleton implementation.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ContextManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._context: Dict[str, Any] = {}
        self._context_history: List[Dict[str, Any]] = []
        self._tool_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._session_id: Optional[str] = None
        self._lock = threading.Lock()
        self._initialized = True
    
    def set_session(self, session_id: str):
        """Set the current session ID."""
        with self._lock:
            self._session_id = session_id
            if session_id not in self._context:
                self._context[session_id] = {}
    
    def get_session(self) -> Optional[str]:
        """Get the current session ID."""
        return self._session_id
    
    def set(self, key: str, value: Any, session_id: Optional[str] = None):
        """
        Set a context value.
        
        Args:
            key: Context key
            value: Context value
            session_id: Optional session ID (uses current session if None)
        """
        with self._lock:
            sid = session_id or self._session_id or "default"
            if sid not in self._context:
                self._context[sid] = {}
            
            self._context[sid][key] = value
            
            # Track history
            self._context_history.append({
                "timestamp": datetime.now().isoformat(),
                "session_id": sid,
                "key": key,
                "action": "set",
                "value_type": type(value).__name__
            })
    
    def get(self, key: str, default: Any = None, session_id: Optional[str] = None) -> Any:
        """
        Get a context value.
        
        Args:
            key: Context key
            default: Default value if key not found
            session_id: Optional session ID (uses current session if None)
        """
        with self._lock:
            sid = session_id or self._session_id or "default"
            if sid in self._context:
                return self._context[sid].get(key, default)
            return default
    
    def has(self, key: str, session_id: Optional[str] = None) -> bool:
        """Check if a context key exists."""
        with self._lock:
            sid = session_id or self._session_id or "default"
            return sid in self._context and key in self._context[sid]
    
    def add_tool_result(self, tool_name: str, result: Any, metadata: Optional[Dict[str, Any]] = None):
        """
        Store a tool result for later reference.
        
        Args:
            tool_name: Name of the tool
            result: Tool result
            metadata: Optional metadata about the result
        """
        with self._lock:
            self._tool_results[tool_name].append({
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            })
    
    def get_tool_results(self, tool_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent results from a tool."""
        with self._lock:
            return self._tool_results[tool_name][-limit:]
    
    def get_all_context(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get all context for a session."""
        with self._lock:
            sid = session_id or self._session_id or "default"
            return self._context.get(sid, {}).copy()
    
    def clear_session(self, session_id: Optional[str] = None):
        """Clear context for a session."""
        with self._lock:
            sid = session_id or self._session_id or "default"
            if sid in self._context:
                del self._context[sid]
    
    def clear_all(self):
        """Clear all context (use with caution)."""
        with self._lock:
            self._context.clear()
            self._context_history.clear()
            self._tool_results.clear()
    
    def get_context_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of the current context."""
        with self._lock:
            sid = session_id or self._session_id or "default"
            context = self._context.get(sid, {})
            
            return {
                "session_id": sid,
                "keys": list(context.keys()),
                "tool_results_count": {
                    tool: len(results) 
                    for tool, results in self._tool_results.items()
                },
                "context_size": len(context)
            }


# Global instance
_context_manager = None

def get_context_manager() -> ContextManager:
    """Get the global context manager instance."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager

