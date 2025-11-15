"""
Supervisor Agent: Orchestrates the multi-agent system using LangGraph.

This module provides both the legacy LangChain implementation and the new LangGraph implementation.
The LangGraph implementation is recommended for production use.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY

# Import LangGraph implementation (recommended)
from agents.graph.supervisor_graph import (
    SupervisorGraph,
    create_supervisor_graph,
    process_query as process_query_graph
)

# Legacy LangChain implementation (kept for backwards compatibility)
try:
    from langchain.agents import initialize_agent, AgentType
    from langchain_core.tools import Tool
except ImportError:
    try:
        from langchain.agents import initialize_agent, AgentType, Tool
    except ImportError:
        from langchain_classic.agents import initialize_agent, AgentType
        from langchain_classic.tools import Tool
from agents.extractor_agent import extractor_tool
from agents.cleaner_agent import cleaner_tool
from agents.analyzer_agent import analyzer_tool
from agents.summarizer_agent import summarizer_tool
from agents.responder_agent import responder_tool
from agents.context_agent import contextualizer_tool
from agents.reference_agent import reference_tool
from agents.additional_tools import (
    formatter_tool,
    classifier_tool,
    data_curator_tool,
    knowledge_base_tool,
    researcher_tool,
    web_search_tool,
    api_integrator_tool,
    translator_tool,
    calculate_tool,
    validator_tool,
    evaluator_tool,
    planner_tool,
    retrainer_tool,
    memory_tool
)

# Initialize LLMs
llmSupervisor = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    openai_api_key=OPENAI_API_KEY
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.5,
    openai_api_key=OPENAI_API_KEY
)

# Legacy tools list (for backwards compatibility)
tools = [
    Tool(name="Extractor", func=lambda x: extractor_tool(x) if isinstance(x, str) else extractor_tool(x),
         description="Extracts text from PDFs or images using OCR."),
    Tool(name="Cleaner", func=cleaner_tool, description="Cleans and normalizes extracted text."),
    Tool(name="Formatter", func=formatter_tool, description="Formats text into structured format."),
    Tool(name="Analyzer", func=analyzer_tool, description="Analyzes scientific content."),
    Tool(name="Classifier", func=classifier_tool, description="Classifies documents by topic."),
    Tool(name="DataCurator", func=data_curator_tool, description="Curates extracted data."),
    Tool(name="KnowledgeGraph", func=knowledge_base_tool, description="Builds knowledge graphs."),
    Tool(name="Researcher", func=lambda x: researcher_tool(x, source="web"), description="Performs web search using DuckDuckGo with scientific context."),
    Tool(name="WebSearch", func=web_search_tool, description="Direct web search using DuckDuckGo. Returns raw results."),
    Tool(name="APIIntegrator", func=lambda x: api_integrator_tool("general", x), description="Integrates with APIs."),
    Tool(name="Summarizer", func=summarizer_tool, description="Summarizes documents."),
    Tool(name="Translator", func=translator_tool, description="Translates scientific text."),
    Tool(name="Computation", func=calculate_tool, description="Performs calculations."),
    Tool(name="Validator", func=validator_tool, description="Validates scientific accuracy."),
    Tool(name="Evaluator", func=evaluator_tool, description="Evaluates result quality."),
    Tool(name="Planner", func=lambda x: planner_tool(x, ["Extractor", "Cleaner", "Analyzer", "Summarizer"]),
         description="Plans multi-step tasks."),
    Tool(name="Retrainer", func=retrainer_tool, description="Retrains models with new data."),
    Tool(name="Memory", func=lambda x: memory_tool("retrieve", x) if x else memory_tool("list"),
         description="Stores and retrieves context."),
    Tool(name="Responder", func=responder_tool, description="Generates final response."),
    Tool(name="Reference", func=reference_tool, description="Extracts references."),
]


def create_supervisor_agent(use_langgraph: bool = True):
    """
    Create and initialize the supervisor agent.
    
    Args:
        use_langgraph: If True, use LangGraph implementation (recommended). 
                      If False, use legacy LangChain implementation.
    
    Returns:
        Initialized agent or graph
    """
    if use_langgraph:
        return create_supervisor_graph()
    else:
        # Legacy implementation
        return initialize_agent(
            tools=tools,
            llm=llmSupervisor,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )


def process_query(query: str, agent=None, use_langgraph: bool = True, chat_history=None, file_path=None):
    """
    Process a user query using the supervisor agent.
    
    Args:
        query: User query string
        agent: Optional pre-initialized agent/graph (creates new one if None)
        use_langgraph: If True, use LangGraph implementation (recommended)
        chat_history: Optional list of previous messages for context
        file_path: Optional file path for document analysis
        
    Returns:
        Agent response string
    """
    if use_langgraph:
        if agent is None:
            agent = create_supervisor_graph()
        # If agent is a SupervisorGraph instance, use its invoke method
        if hasattr(agent, 'invoke'):
            result = agent.invoke(query, chat_history=chat_history, file_path=file_path)
            # Extract response from result
            if isinstance(result, dict):
                return result.get('output', str(result))
            return str(result)
        else:
            # Fallback to process_query_graph function
            return process_query_graph(query, agent)
    else:
        # Legacy implementation
        if agent is None:
            agent = create_supervisor_agent(use_langgraph=False)
        try:
            response = agent.run(query)
            return response
        except Exception as e:
            return f"Error processing query: {str(e)}"


if __name__ == "__main__":
    # Example usage with LangGraph (recommended)
    print("Using LangGraph implementation:")
    graph = create_supervisor_graph()
    test_query = "Analiza un documento sobre agujeros negros"
    result = process_query(test_query, graph)
    print(result)
