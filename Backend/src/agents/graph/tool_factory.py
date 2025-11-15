"""
Factory Pattern: Creates and manages tool instances.
"""

from typing import Dict, Callable, List
try:
    from langchain_core.tools import Tool
except ImportError:
    # Fallback for older langchain versions
    try:
        from langchain.tools import Tool
    except ImportError:
        from langchain_classic.tools import Tool
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

# Note: All tool imports are done lazily inside _register_all_tools() 
# to avoid circular dependencies


class ToolFactory:
    """
    Factory class for creating and managing tool instances.
    Implements Singleton pattern to ensure single instance.
    """
    
    _instance = None
    _tools: Dict[str, Tool] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolFactory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._register_all_tools()
        self._initialized = True
    
    def _register_all_tools(self):
        """Register all available tools."""
        # Lazy imports to avoid circular dependencies
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
        from agents.tool_agent import tool_agent_tool
        
        tool_definitions = [
            # Data Ingestion & Cleaning
            {
                "name": "Extractor",
                "func": lambda x: extractor_tool(x) if isinstance(x, str) else extractor_tool(x),
                "description": "Extracts text from PDFs or images using OCR. Input: file path (string) or list of file paths. Returns the raw text content."
            },
            {
                "name": "Cleaner",
                "func": cleaner_tool,
                "description": "Cleans and normalizes extracted text by removing noise, symbols, and irrelevant data. Input: raw text (string). Returns cleaned text."
            },
            {
                "name": "Formatter",
                "func": formatter_tool,
                "description": "Formats the cleaned text into a structured, consistent format ready for analysis. Input: text (string). Returns formatted text."
            },
            # Analysis & Classification
            {
                "name": "Analyzer",
                "func": analyzer_tool,
                "description": "Analyzes the document's scientific content and identifies key concepts or entities. Input: query text (string). Returns similar documents and analysis."
            },
            {
                "name": "Classifier",
                "func": classifier_tool,
                "description": "Classifies the document based on its topic or category (e.g., black holes, galaxies, radiation). Input: text (string). Returns classification."
            },
            {
                "name": "DataCurator",
                "func": data_curator_tool,
                "description": "Curates and organizes extracted data to improve embedding and storage quality. Input: text (string). Returns curated text."
            },
            # Knowledge & Research
            {
                "name": "KnowledgeGraph",
                "func": knowledge_base_tool,
                "description": "Builds and queries knowledge graphs linking concepts (e.g., black hole → event horizon → singularity). Combines RAG + graph knowledge. Input: text (string) or entity name, operation (build/query/find_path). Returns graph information."
            },
            {
                "name": "Researcher",
                "func": lambda x: researcher_tool(x, source="web"),
                "description": "Performs web search using DuckDuckGo to find real-time information and scientific context. Synthesizes results with scientific context. Input: research query (string). Returns search results with scientific context."
            },
            {
                "name": "WebSearch",
                "func": web_search_tool,
                "description": "Performs direct web search using DuckDuckGo. Returns raw search results with titles, descriptions, and URLs. Use this for quick web searches. Input: search query (string)."
            },
            {
                "name": "APIIntegrator",
                "func": lambda x: api_integrator_tool("nasa_apod", x) if "apod" in x.lower() else api_integrator_tool("wikipedia", x) if "wikipedia" in x.lower() else api_integrator_tool("nasa_neo", x),
                "description": "Queries external services (NASA, ESA, ADS, Wikipedia) and returns structured information. Increases dynamic knowledge. Input: service name and query (string). Returns API results."
            },
            # Processing & Transformation
            {
                "name": "Summarizer",
                "func": summarizer_tool,
                "description": "Summarizes documents or extracted text, focusing on key findings and results. Input: text (string). Returns summary."
            },
            {
                "name": "Translator",
                "func": translator_tool,
                "description": "Translates scientific text between English and Spanish, preserving terminology. Input: text (string). Returns translated text."
            },
            {
                "name": "Computation",
                "func": calculate_tool,
                "description": "Performs physical or mathematical calculations (e.g., mass, radius, luminosity) using formulas. Input: calculation expression (string). Returns calculation result."
            },
            # Validation & Evaluation
            {
                "name": "Validator",
                "func": validator_tool,
                "description": "Validates scientific accuracy, data consistency, and textual coherence of the output. Input: text (string). Returns validation results."
            },
            {
                "name": "Evaluator",
                "func": evaluator_tool,
                "description": "Measures performance of agents (precision, recall, latency). Evaluates quality, completeness, and correctness. Input: results text (string), optional agent_name and input_data. Returns evaluation metrics."
            },
            # Planning & Learning
            {
                "name": "Planner",
                "func": lambda x: planner_tool(x, ["Extractor", "Cleaner", "Formatter", "Analyzer", "Classifier", "Summarizer", "Responder", "Researcher", "Computation", "Validator"]),
                "description": "Plans multi-step tasks using Task Decomposition. Divides complex tasks into subtasks with dependencies. Input: task description (string). Returns structured execution plan."
            },
            {
                "name": "ToolAgent",
                "func": lambda x: tool_agent_tool("orbital_calc", x) if "orbital" in x.lower() else tool_agent_tool("black_hole_calc", x) if "black hole" in x.lower() else tool_agent_tool("nasa_api", x),
                "description": "Uses external tools (NASA API, orbital calculators, black hole calculators). Input: tool type and parameters as JSON string. Returns calculated results."
            },
            {
                "name": "Retrainer",
                "func": retrainer_tool,
                "description": "Detects new relevant data and automatically updates embeddings. Automates vector store updates. Input: new data text (string). Returns retraining status."
            },
            {
                "name": "Memory",
                "func": lambda x: memory_tool("retrieve", x) if x else memory_tool("list"),
                "description": "Stores and retrieves previous user interactions or contextual information for continuity. Input: key (string) or empty for list. Returns stored information."
            },
            # Response & Documentation
            {
                "name": "Responder",
                "func": responder_tool,
                "description": "Generates the final response with personality, emotion detection, and natural dialogue. Supports styles: scientific, friendly, enthusiastic, professional, casual, detailed, brief. Input: context text (string), optional user_query and style. Returns enhanced response."
            },
            {
                "name": "Reference",
                "func": reference_tool,
                "description": "Extracts and manages bibliographic references, citations, DOIs, and arXiv IDs from scientific documents. Input: text (string). Returns extracted references."
            },
            {
                "name": "Contextualizer",
                "func": contextualizer_tool,
                "description": "Adds background information and context about scientific findings. Input: text (string). Returns text with added context."
            },
        ]
        
        for tool_def in tool_definitions:
            tool = Tool(
                name=tool_def["name"],
                func=tool_def["func"],
                description=tool_def["description"]
            )
            self._tools[tool_def["name"]] = tool
    
    def get_tool(self, name: str) -> Tool:
        """Get a tool by name."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found")
        return self._tools[name]
    
    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return list(self._tools.keys())
    
    def register_tool(self, name: str, func: Callable, description: str):
        """Register a new tool dynamically."""
        tool = Tool(name=name, func=func, description=description)
        self._tools[name] = tool

