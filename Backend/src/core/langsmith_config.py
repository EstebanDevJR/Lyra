"""
LangSmith Configuration: Sets up tracing and observability for LangChain/LangGraph operations.

LangSmith provides:
- Request/response tracing
- Performance monitoring
- Error tracking
- Cost analysis
- Debugging tools
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("lyra.langsmith")

def setup_langsmith() -> bool:
    """
    Configure LangSmith tracing for LangChain/LangGraph operations.
    
    This function sets up environment variables for LangSmith tracing.
    LangSmith will automatically trace all LangChain/LangGraph operations
    when these environment variables are set.
    
    Returns:
        True if LangSmith is configured and enabled, False otherwise
    """
    from config import LANGCHAIN_TRACING_V2, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT, LANGCHAIN_ENDPOINT
    
    if not LANGCHAIN_TRACING_V2:
        logger.info("LangSmith tracing is disabled (LANGCHAIN_TRACING_V2=false)")
        return False
    
    if not LANGCHAIN_API_KEY:
        logger.warning("LangSmith tracing is enabled but LANGCHAIN_API_KEY is not set. Tracing will not work.")
        return False
    
    # Set environment variables for LangSmith
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = LANGCHAIN_ENDPOINT
    
    # Optional: Set tags for better organization
    os.environ["LANGCHAIN_TAGS"] = "lyra,astrophysics,multi-agent"
    
    logger.info(f"LangSmith tracing enabled for project: {LANGCHAIN_PROJECT}")
    logger.info(f"LangSmith endpoint: {LANGCHAIN_ENDPOINT}")
    
    return True


def configure_langsmith_metadata(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Configure metadata for LangSmith tracing.
    
    Args:
        session_id: Optional session ID for grouping related traces
        user_id: Optional user ID for user-specific tracing
        metadata: Optional additional metadata dictionary
        
    Returns:
        Dictionary with LangSmith metadata configuration
    """
    langsmith_metadata = {}
    
    if session_id:
        langsmith_metadata["session_id"] = session_id
    
    if user_id:
        langsmith_metadata["user_id"] = user_id
    
    if metadata:
        langsmith_metadata.update(metadata)
    
    return langsmith_metadata

