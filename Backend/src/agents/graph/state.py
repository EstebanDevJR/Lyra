"""
State definition for LangGraph agent system.
"""

from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class AgentState(TypedDict):
    """
    State schema for the multi-agent system.
    
    Attributes:
        messages: List of messages in the conversation
        current_step: Current step in the workflow
        tool_results: Results from tool executions
        context: Additional context for the current task
        metadata: Metadata about the execution
        next_agent: Next agent to route to (optional)
    """
    messages: Annotated[List[BaseMessage], add_messages]
    current_step: str
    tool_results: Dict[str, any]
    context: Dict[str, any]
    metadata: Dict[str, any]
    next_agent: Optional[str]

