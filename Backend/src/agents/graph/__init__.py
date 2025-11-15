"""
LangGraph implementation for multi-agent system.
"""

# Import core components first (no dependencies on agents)
from .state import AgentState
from .observer import Observer, LoggingObserver, MetricsObserver, Subject
from .context_manager import ContextManager, get_context_manager
from .resource_manager import ResourceManager, get_resource_manager
from .error_handler import ErrorHandler, RetryStrategy, get_error_handler
from .tool_cache import ToolCache, get_tool_cache

# Import components that depend on agents (lazy import to avoid circular dependencies)
def _lazy_imports():
    """Lazy imports to avoid circular dependencies."""
    from .supervisor_graph import SupervisorGraph, create_supervisor_graph, process_query
    from .tool_factory import ToolFactory
    return SupervisorGraph, create_supervisor_graph, process_query, ToolFactory

# Make imports available at module level
SupervisorGraph, create_supervisor_graph, process_query, ToolFactory = _lazy_imports()

__all__ = [
    'SupervisorGraph',
    'create_supervisor_graph',
    'process_query',
    'AgentState',
    'ToolFactory',
    'Observer',
    'LoggingObserver',
    'MetricsObserver',
    'Subject',
    'ContextManager',
    'get_context_manager',
    'ResourceManager',
    'get_resource_manager',
    'ErrorHandler',
    'RetryStrategy',
    'get_error_handler',
    'ToolCache',
    'get_tool_cache',
]

