"""
LangGraph implementation of the supervisor agent system.
Uses StateGraph for workflow orchestration.
"""

import sys
from pathlib import Path
from typing import Literal, Dict, Any
import time

sys.path.append(str(Path(__file__).parent.parent.parent))

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Try to import from langchain_classic (newer versions) or langchain.agents (older versions)
try:
    from langchain_classic.agents import create_openai_tools_agent, AgentExecutor
except ImportError:
    try:
        from langchain.agents import create_openai_tools_agent, AgentExecutor
    except ImportError:
        # If both fail, set to None - will only be used if legacy mode is needed
        create_openai_tools_agent = None
        AgentExecutor = None

from config import OPENAI_API_KEY
from agents.graph.state import AgentState
from agents.graph.tool_factory import ToolFactory
from agents.graph.observer import Subject, LoggingObserver, MetricsObserver
from agents.graph.context_manager import get_context_manager
from agents.graph.resource_manager import get_resource_manager
from agents.graph.error_handler import get_error_handler, RetryStrategy
from agents.graph.tool_cache import get_tool_cache


class SupervisorGraph(Subject):
    """
    LangGraph-based supervisor agent.
    Implements Singleton pattern and Observer pattern.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupervisorGraph, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        Subject.__init__(self)
        
        # Initialize managers
        self.context_manager = get_context_manager()
        self.resource_manager = get_resource_manager()
        self.error_handler = get_error_handler()
        self.tool_cache = get_tool_cache()
        
        # Initialize components
        self.tool_factory = ToolFactory()
        self.llm = self.resource_manager.get_llm(model="gpt-4o-mini", temperature=0.7)
        
        # Create agent with tools
        self.tools = self.tool_factory.get_all_tools()
        self.agent = self._create_agent()
        
        # Build graph
        self.graph = self._build_graph()
        
        # Attach default observers
        self.attach(LoggingObserver())
        self.attach(MetricsObserver())
        
        self._initialized = True
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt with current date context."""
        from core.date_utils import get_date_context_string
        
        date_context = get_date_context_string()
        
        return f"""You are Lyra, an AI assistant specialized in astronomical, astrophysical, and nature-related scientific analysis.

{date_context}

SCOPE GUIDELINES:
- Your PRIMARY focus is: astrophysics, astronomy, space phenomena, galaxies, stars, planets, black holes, solar storms, auroras, cosmic radiation, nature, Earth sciences, geology, climate, ecology, and related scientific topics.
- You should REFUSE questions about: politics, current events (non-scientific), history (non-scientific), personal opinions, biographies of non-scientists, or clearly off-topic subjects.
- IMPORTANT: Be PERMISSIVE with scientific queries. If a question mentions scientific terms (NGC, mass, pattern, attenuation, objects, etc.), astronomical objects, or seems to be a scientific question, you should process it even if it's not perfectly clear.
- Only redirect users if the question is CLEARLY outside your scope (e.g., "who was JFK?" or "what do you think about politics?").
- For ambiguous queries, err on the side of processing them as they might be scientific questions.

You have access to multiple tools organized in categories:
1. Data Ingestion: Extractor, Cleaner, Formatter
2. Analysis: Analyzer, Classifier, DataCurator
3. Knowledge: KnowledgeGraph (builds/queries concept relationships), Researcher (web search with context), WebSearch (direct web search), APIIntegrator (NASA, ESA, Wikipedia, ADS)
4. Processing: Summarizer, Translator, Computation
5. Validation: Validator, Evaluator (measures agent performance)
6. Planning: Planner (Task Decomposition), ToolAgent (external tools), Retrainer (auto-detects new data), Memory
7. Response: Responder (with personality & emotion detection), Reference, Contextualizer

IMPORTANT: Use Researcher or WebSearch when you need current information from the internet. Researcher provides synthesized scientific context, while WebSearch provides raw search results.

IMPORTANT: If the user mentions a document, file, or asks about uploaded content, use the Extractor tool with the file path. If a file_path is available in the context, use it when calling Extractor. If only a filename is mentioned, try using that filename with Extractor - it will automatically search in the data directory.

Use these tools strategically to help users analyze scientific documents, answer questions, and perform calculations - BUT ONLY within your scope.

Always respond in Spanish unless the user requests otherwise.
Be precise, scientific, and helpful.
When in doubt about whether a query is scientific, process it rather than rejecting it."""

    def _create_agent(self):
        """Create the agent executor with tools."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with improved routing."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("validate", self._validate_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "supervisor",
            self._should_validate,
            {
                "validate": "validate",
                "execute": "agent"
            }
        )
        
        workflow.add_edge("validate", "agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "agent",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _should_validate(self, state: AgentState) -> str:
        """Decide if validation step is needed."""
        # Validate if this is a complex query or if previous step had errors
        query = state["messages"][-1].content if state["messages"] else ""
        
        # Complex queries might need validation
        complex_keywords = ["analizar", "resumir", "comparar", "calcular", "validar"]
        if any(keyword in query.lower() for keyword in complex_keywords):
            return "validate"
        
        return "execute"
    
    def _should_continue(self, state: AgentState) -> str:
        """Decide if agent should continue processing."""
        # Check if there are pending tasks or if result needs refinement
        tool_results = state.get("tool_results", {})
        
        # Continue if no results yet or if result indicates more work needed
        if not tool_results.get("agent"):
            return "continue"
        
        # Check if result suggests continuation
        result = tool_results.get("agent", {})
        output = result.get("output", "")
        
        # If output suggests more processing needed
        if any(phrase in output.lower() for phrase in ["necesito más", "requiere", "debería"]):
            return "continue"
        
        return "end"
    
    def _validate_node(self, state: AgentState) -> AgentState:
        """Validate input before processing."""
        self.notify("validation", {
            "message": "Validating input",
            "query": state["messages"][-1].content if state["messages"] else ""
        })
        
        # Store validation in context
        query = state["messages"][-1].content if state["messages"] else ""
        self.context_manager.set("validated_query", query)
        self.context_manager.set("validation_timestamp", time.time())
        
        state["current_step"] = "validated"
        return state
    
    def _supervisor_node(self, state: AgentState) -> AgentState:
        """Supervisor node that routes to agent."""
        self.notify("start", {
            "message": "Starting supervisor workflow",
            "query": state["messages"][-1].content if state["messages"] else ""
        })
        
        state["current_step"] = "supervisor"
        state["metadata"]["started_at"] = time.time()
        
        return state
    
    def _agent_node(self, state: AgentState) -> AgentState:
        """Agent node that executes tools."""
        try:
            start_time = time.time()
            
            # Get the last message
            last_message = state["messages"][-1]
            query = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            self.notify("tool_call", {
                "tool_name": "Agent",
                "message": f"Processing query: {query[:100]}...",
                "level": "INFO"
            })
            
            # Execute agent
            result = self.agent.invoke({
                "messages": state["messages"],
                "chat_history": []
            })
            
            execution_time = time.time() - start_time
            
            # Update state
            state["messages"].append(AIMessage(content=result.get("output", str(result))))
            state["current_step"] = "completed"
            state["tool_results"]["agent"] = result
            state["metadata"]["execution_time"] = execution_time
            state["metadata"]["completed_at"] = time.time()
            
            self.notify("tool_call", {
                "tool_name": "Agent",
                "message": "Query processed successfully",
                "level": "INFO",
                "execution_time": execution_time
            })
            
        except Exception as e:
            error_msg = f"Error in agent execution: {str(e)}"
            self.notify("error", {
                "error": error_msg,
                "context": {"state": state.get("current_step", "unknown")}
            })
            
            state["messages"].append(AIMessage(content=f"Error: {error_msg}"))
            state["current_step"] = "error"
            state["metadata"]["error"] = str(e)
        
        return state
    
    def invoke(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Invoke the graph with a query.
        
        Args:
            query: User query string
            chat_history: Optional list of previous messages (dict with 'role' and 'content')
            file_path: Optional file path for document analysis
            **kwargs: Additional arguments (session_id, use_cache, etc.)
            
        Returns:
            Result dictionary
        """
        # Set session context
        session_id = kwargs.get("session_id", f"session_{int(time.time())}")
        self.context_manager.set_session(session_id)
        
        # Store query and file_path in context
        self.context_manager.set("current_query", query)
        file_path = kwargs.get("file_path")
        if file_path:
            self.context_manager.set("file_path", file_path)
        
        # Configure LangSmith metadata for this trace
        try:
            from core.langsmith_config import configure_langsmith_metadata
            langsmith_metadata = configure_langsmith_metadata(
                session_id=session_id,
                metadata={
                    "query": query[:100],  # Truncate for metadata
                    "has_file": bool(file_path),
                    "has_history": len(kwargs.get("chat_history", [])) > 0
                }
            )
        except Exception as e:
            logger.warning(f"Failed to configure LangSmith metadata: {e}")
            langsmith_metadata = {}
        
        # Build message list with chat history if provided
        messages = []
        chat_history = kwargs.get("chat_history", [])
        
        # Add previous messages from chat history
        if chat_history:
            for msg in chat_history:
                role = msg.get("role") if isinstance(msg, dict) else msg.role
                content = msg.get("content") if isinstance(msg, dict) else msg.content
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        initial_state: AgentState = {
            "messages": messages,
            "current_step": "initialized",
            "tool_results": {},
            "context": kwargs.get("context", {}),
            "metadata": {
                "query": query,
                "session_id": session_id,
                "has_history": len(chat_history) > 0,
                "langsmith_metadata": langsmith_metadata,
                **kwargs.get("metadata", {})
            },
            "next_agent": None
        }
        
        try:
            # Use error handler for robust execution
            # LangSmith will automatically trace the graph execution
            result = self.error_handler.retry(
                self.graph.invoke,
                initial_state,
                strategy=RetryStrategy.EXPONENTIAL,
                max_retries=2
            )
            
            # Store result in context
            output = result["messages"][-1].content if result["messages"] else ""
            self.context_manager.add_tool_result("supervisor", output, {
                "query": query,
                "execution_time": result.get("metadata", {}).get("execution_time", 0)
            })
            
            self.notify("end", {
                "message": "Workflow completed",
                "execution_time": result.get("metadata", {}).get("execution_time", 0)
            })
            
            return {
                "output": output,
                "state": result,
                "metrics": self._get_metrics(),
                "context_summary": self.context_manager.get_context_summary(session_id)
            }
        except Exception as e:
            self.notify("error", {
                "error": str(e),
                "context": {"query": query, "session_id": session_id}
            })
            raise
    
    def stream(self, query: str, **kwargs):
        """Stream results from the graph."""
        initial_state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "current_step": "initialized",
            "tool_results": {},
            "context": kwargs.get("context", {}),
            "metadata": {
                "query": query,
                **kwargs.get("metadata", {})
            },
            "next_agent": None
        }
        
        return self.graph.stream(initial_state)
    
    def _get_metrics(self) -> Dict[str, Any]:
        """Get metrics from MetricsObserver."""
        for observer in self._observers:
            if isinstance(observer, MetricsObserver):
                return observer.get_metrics()
        return {}


def create_supervisor_graph() -> SupervisorGraph:
    """Factory function to create supervisor graph instance."""
    return SupervisorGraph()


def process_query(query: str, graph: SupervisorGraph = None, chat_history=None) -> str:
    """
    Process a user query using the supervisor graph.
    
    Args:
        query: User query string
        graph: Optional supervisor graph instance
        chat_history: Optional list of previous messages for context
        
    Returns:
        Response string
    """
    if graph is None:
        graph = SupervisorGraph()
    
    try:
        result = graph.invoke(query, chat_history=chat_history)
        return result.get("output", "No response generated")
    except Exception as e:
        return f"Error processing query: {str(e)}"

