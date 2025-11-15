"""
Tool Result Cache: Caches tool results to avoid redundant executions.
Implements LRU (Least Recently Used) cache strategy.
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import hashlib
import json
from collections import OrderedDict
import threading


class ToolCache:
    """
    Caches tool results to avoid redundant executions.
    Thread-safe LRU cache implementation.
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of cached entries
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_size = max_size
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = threading.Lock()
    
    def _generate_key(self, tool_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a cache key from tool name and arguments."""
        # Create a hashable representation
        key_data = {
            "tool": tool_name,
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, tool_name: str, args: tuple = (), kwargs: dict = None) -> Optional[Any]:
        """
        Get a cached result.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            kwargs: Tool keyword arguments
            
        Returns:
            Cached result or None if not found/expired
        """
        if kwargs is None:
            kwargs = {}
        
        cache_key = self._generate_key(tool_name, args, kwargs)
        
        with self._lock:
            if cache_key not in self._cache:
                return None
            
            entry = self._cache[cache_key]
            
            # Check if expired
            if datetime.now() - entry["timestamp"] > self._ttl:
                del self._cache[cache_key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
            
            return entry["result"]
    
    def set(self, tool_name: str, result: Any, args: tuple = (), kwargs: dict = None):
        """
        Cache a tool result.
        
        Args:
            tool_name: Name of the tool
            result: Tool result
            args: Tool arguments
            kwargs: Tool keyword arguments
        """
        if kwargs is None:
            kwargs = {}
        
        cache_key = self._generate_key(tool_name, args, kwargs)
        
        with self._lock:
            # Remove oldest entry if cache is full
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            
            self._cache[cache_key] = {
                "result": result,
                "timestamp": datetime.now(),
                "tool_name": tool_name
            }
            
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
    
    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
    
    def clear_tool(self, tool_name: str):
        """Clear all cached entries for a specific tool."""
        with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry["tool_name"] == tool_name
            ]
            for key in keys_to_remove:
                del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "ttl_seconds": self._ttl.total_seconds(),
                "tools_cached": len(set(entry["tool_name"] for entry in self._cache.values()))
            }


# Global cache instance
_tool_cache = None

def get_tool_cache() -> ToolCache:
    """Get the global tool cache instance."""
    global _tool_cache
    if _tool_cache is None:
        _tool_cache = ToolCache()
    return _tool_cache

