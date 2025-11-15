"""
Additional tools for the multi-agent system: formatter, classifier, validator, etc.
"""

import sys
import re
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY
from core.vectorstore import VectorStore
from core.chunking import Chunker


# ─────────────────────────────
# FORMATTER TOOL
# ─────────────────────────────

def formatter_tool(text: str, format_type: str = "structured") -> str:
    """
    Formats cleaned text into a structured, consistent format ready for analysis.
    
    Args:
        text: Text to format
        format_type: Type of formatting ("structured", "paragraphs", "sections")
        
    Returns:
        Formatted text
    """
    if not text:
        return ""
    
    if format_type == "structured":
        # Add proper spacing and structure
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Ensure sentences end properly
                if not para.endswith(('.', '!', '?', ':')):
                    para += '.'
                formatted_paragraphs.append(para)
        
        return '\n\n'.join(formatted_paragraphs)
    
    elif format_type == "paragraphs":
        # Ensure double line breaks between paragraphs
        return re.sub(r'\n{3,}', '\n\n', text)
    
    elif format_type == "sections":
        # Try to identify and format sections
        lines = text.split('\n')
        formatted = []
        for line in lines:
            line = line.strip()
            if line:
                # Check if it's a section header (all caps or title case)
                if line.isupper() or (line[0].isupper() and len(line) < 100):
                    formatted.append(f"\n{line}\n{'='*len(line)}\n")
                else:
                    formatted.append(line)
        return '\n'.join(formatted)
    
    return text


# ─────────────────────────────
# CLASSIFIER TOOL
# ─────────────────────────────

def classifier_tool(text: str) -> str:
    """
    Classifies the document based on its topic or category.
    
    Args:
        text: Text to classify
        
    Returns:
        Classification result
    """
    if not text:
        return "No text provided for classification."
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=OPENAI_API_KEY
        )
        
        prompt = f"""Classify the following astronomical/astrophysical text into one or more categories:

Categories: black holes, galaxies, stars, exoplanets, cosmology, dark matter, neutron stars, supernovae, quasars, gravitational waves, general astronomy

Text:
{text[:1500]}

Respond with the category/categories in Spanish, separated by commas."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return f"Classification: {response.content}"
        else:
            return f"Classification: {str(response)}"
            
    except Exception as e:
        # Fallback: simple keyword-based classification
        text_lower = text.lower()
        categories = []
        
        if any(term in text_lower for term in ['black hole', 'agujero negro', 'event horizon']):
            categories.append("black holes")
        if any(term in text_lower for term in ['galaxy', 'galaxia', 'milky way']):
            categories.append("galaxies")
        if any(term in text_lower for term in ['star', 'estrella', 'stellar']):
            categories.append("stars")
        if any(term in text_lower for term in ['exoplanet', 'exoplaneta', 'planet']):
            categories.append("exoplanets")
        
        return f"Classification: {', '.join(categories) if categories else 'general astronomy'}"


# ─────────────────────────────
# DATA CURATOR TOOL
# ─────────────────────────────

def data_curator_tool(text: str) -> str:
    """
    Curates and organizes extracted data to improve embedding and storage quality.
    
    Args:
        text: Text to curate
        
    Returns:
        Curated text
    """
    if not text:
        return ""
    
    # Remove very short lines (likely noise)
    lines = text.split('\n')
    curated_lines = [line for line in lines if len(line.strip()) > 10]
    
    # Remove duplicate lines
    seen = set()
    unique_lines = []
    for line in curated_lines:
        line_lower = line.lower().strip()
        if line_lower not in seen:
            seen.add(line_lower)
            unique_lines.append(line)
    
    # Group related content
    curated_text = '\n'.join(unique_lines)
    
    # Ensure proper spacing
    curated_text = re.sub(r'\n{3,}', '\n\n', curated_text)
    
    return curated_text.strip()


# ─────────────────────────────
# KNOWLEDGE GRAPH TOOL
# ─────────────────────────────

def knowledge_base_tool(text: str, operation: str = "build", **kwargs) -> str:
    """
    Builds or queries a knowledge graph linking scientific entities and relationships.
    Uses KnowledgeGraphAgent for real graph operations.
    
    Args:
        text: Text to process or entity to query
        operation: Operation type ("build", "query", "find_path")
        **kwargs: Additional parameters (entity, source, target, depth)
        
    Returns:
        Knowledge graph information
    """
    try:
        from agents.knowledge_graph_agent import knowledge_graph_agent_tool
        return knowledge_graph_agent_tool(text, operation, **kwargs)
    except ImportError:
        # Fallback if agent not available
        if not text:
            return "No text provided."
        
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                openai_api_key=OPENAI_API_KEY
            )
            
            if operation == "extract" or operation == "build":
                prompt = f"""Extract scientific entities and their relationships from the following text.

Text:
{text[:2000]}

List entities and relationships in structured format in Spanish."""

            elif operation == "query":
                prompt = f"""Identify relationships between entities in this text.

Text:
{text[:2000]}

Describe the relationships between key scientific entities."""

            else:
                prompt = f"""Build a knowledge graph representation of this text.

Text:
{text[:2000]}

Create a structured representation showing entities and their connections."""

            response = llm.invoke(prompt)
            
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            return f"Error processing knowledge graph: {str(e)}"
    except Exception as e:
        return f"Error in graph operation: {str(e)}"


# ─────────────────────────────
# RESEARCHER TOOL (Web Search)
# ─────────────────────────────

# Check if DuckDuckGo search is available
# Try new package name first (ddgs), then fallback to old name for compatibility
DDG_AVAILABLE = False
DDGS = None
try:
    from ddgs import DDGS
    DDG_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDG_AVAILABLE = True
    except ImportError:
        DDG_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def _add_search_results_to_vectorstore(search_results: List[Dict], query: str) -> None:
    """
    Adds search results to vector store for continuous learning.
    
    Args:
        search_results: List of search results
        query: Original query that generated these results
    """
    try:
        # Combine all results into text to add to vector store
        combined_text = f"Web search performed: {query}\n\n"
        combined_text += "Results found:\n\n"
        
        for i, result in enumerate(search_results, 1):
            title = result.get('title', 'No title')
            body = result.get('body', 'No description')
            href = result.get('href', '')
            
            combined_text += f"Result {i}:\n"
            combined_text += f"Title: {title}\n"
            combined_text += f"Description: {body}\n"
            combined_text += f"URL: {href}\n\n"
        
        # Create unique identifier for this search document
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_id = f"web_search_{timestamp}_{hash(query) % 10000}"
        
        # Chunk the text
        chunker = Chunker()
        chunks = chunker.chunk_text(combined_text)
        
        if chunks:
            # Prepare chunks for vector store
            chunks_dict = {doc_id: chunks}
            
            # Add to vector store
            vector_store = VectorStore()
            vector_store.load()
            vector_store.add_documents(chunks_dict)
            vector_store.save()
            
            print(f"✅ Added {len(chunks)} web search chunks to vector store (doc: {doc_id})")
        
    except Exception as e:
        # Don't fail if unable to add to vector store, just log
        print(f"⚠️  Warning: Could not add search results to vector store: {str(e)}")


def web_search_tool(query: str, max_results: int = 5, learn: bool = True) -> str:
    """
    Performs web searches using DuckDuckGo.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return (default: 5)
        learn: If True, adds results to vector store for learning (default: True)
        
    Returns:
        Formatted search results
    """
    if not DDG_AVAILABLE:
        return "Error: duckduckgo-search is not installed. Install with: pip install ddgs"
    
    try:
        results = []
        search_results_raw = []
        
        # Improve query for scientific searches
        enhanced_query = _enhance_search_query(query)
        
        with DDGS() as ddgs:
            # Perform search with enhanced query
            search_results_raw = list(ddgs.text(enhanced_query, max_results=max_results))
            
            if not search_results_raw:
                return f"No results found for search: '{query}'"
            
            # Format results
            formatted_results = []
            for i, result in enumerate(search_results_raw, 1):
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')
                href = result.get('href', '')
                
                formatted_results.append(
                    f"Result {i}:\n"
                    f"Title: {title}\n"
                    f"Description: {body}\n"
                    f"URL: {href}\n"
                )
            
            # Add results to vector store for learning (in background)
            if learn and search_results_raw:
                try:
                    _add_search_results_to_vectorstore(search_results_raw, query)
                except Exception as e:
                    # Don't fail if unable to learn, just continue
                    print(f"⚠️  Could not learn from results: {str(e)}")
            
            return "\n---\n".join(formatted_results)
            
    except Exception as e:
        return f"Error performing web search: {str(e)}"


def _enhance_search_query(query: str) -> str:
    """
    Enhance search query for better scientific results.
    Adds context and filters to improve relevance.
    
    Args:
        query: Original search query
        
    Returns:
        Enhanced query string
    """
    query_lower = query.lower()
    
    # For CERN-specific queries, prioritize official CERN sources
    if 'cern' in query_lower:
        # Remove common date references that might confuse search
        query_clean = re.sub(r'\b(hasta|until|by)\s+\d{1,2}\s+(de|of)\s+\w+\s+\d{4}\b', '', query, flags=re.IGNORECASE)
        query_clean = query_clean.strip()
        # Add site filter for CERN official sites
        return f"{query_clean} site:cern.ch OR site:home.cern"
    
    # For other scientific queries, add keywords to improve relevance
    scientific_keywords = ['discovery', 'discoveries', 'descubrimiento', 'descubrimientos', 
                          'research', 'investigación', 'experiment', 'experimento',
                          'LHC', 'particle', 'partícula', 'physics', 'física', 'astrophysics', 'astrofísica']
    
    if any(keyword in query_lower for keyword in scientific_keywords):
        # Add site filters for reputable scientific sources
        return f"{query} site:edu OR site:org OR site:gov"
    
    return query


def researcher_tool(query: str, source: str = "web", learn: bool = True) -> str:
    """
    Performs external research using web search (DuckDuckGo) or APIs.
    Results are automatically added to vector store for continuous learning.
    
    Args:
        query: Research query
        source: Source type ("web", "general", "nasa", "arxiv", "wikipedia")
                - "web": Uses real web search with DuckDuckGo (recommended)
                - Others: Uses LLM as fallback
        learn: If True, adds results to vector store for learning (default: True)
        
    Returns:
        Research results
    """
    # If source is "web", use real web search
    if source == "web" and DDG_AVAILABLE:
        try:
            # Perform web search (this already adds results to vector store if learn=True)
            search_results = web_search_tool(query, max_results=5, learn=learn)
            
            # Use LLM to synthesize and contextualize results
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.5,
                openai_api_key=OPENAI_API_KEY
            )
            
            # Get current date context
            from core.date_utils import get_date_context_string
            date_context = get_date_context_string()
            
            prompt = f"""You are a scientific research assistant specialized in astronomy and astrophysics.

{date_context}

I have performed a web search on: "{query}"

Results found:
{search_results}

Please synthesize this information in Spanish, providing:
1. Key and relevant information
2. Scientific context when appropriate
3. Sources mentioned if available
4. Any recent information or relevant discoveries

IMPORTANT: Use the current date provided above as your reference. When the user asks about "hasta hoy", "hasta ahora", "recientes", or similar temporal references, use the current date shown above. Do NOT mention your training data cutoff date (like "octubre de 2023"). Instead, use the current date provided.

Be precise, scientific, and cite sources when possible."""

            response = llm.invoke(prompt)
            
            # Also add synthesis to vector store for learning
            if learn:
                try:
                    synthesis_text = response.content if hasattr(response, 'content') else str(response)
                    combined_text = f"Web search and synthesis: {query}\n\nSynthesis:\n{synthesis_text}\n\n---\nOriginal results:\n{search_results}"
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    doc_id = f"web_research_synthesis_{timestamp}_{hash(query) % 10000}"
                    
                    chunker = Chunker()
                    chunks = chunker.chunk_text(combined_text)
                    
                    if chunks:
                        chunks_dict = {doc_id: chunks}
                        vector_store = VectorStore()
                        vector_store.load()
                        vector_store.add_documents(chunks_dict)
                        vector_store.save()
                        print(f"✅ Added search synthesis to vector store (doc: {doc_id})")
                except Exception as e:
                    print(f"⚠️  Could not add synthesis to vector store: {str(e)}")
            
            if hasattr(response, 'content'):
                return f"Web search results for '{query}':\n\n{response.content}\n\n---\nSources consulted:\n{search_results}"
            else:
                return f"Web search results for '{query}':\n\n{str(response)}\n\n---\nSources consulted:\n{search_results}"
                
        except Exception as e:
            # Fallback to web search without LLM if it fails
            return f"Web search performed. Results:\n\n{web_search_tool(query, max_results=5, learn=learn)}\n\nNote: Error synthesizing with LLM: {str(e)}"
    
    # Fallback for other source types or if DuckDuckGo is not available
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.5,
            openai_api_key=OPENAI_API_KEY
        )
        
        source_info = {
            "nasa": "NASA databases and publications",
            "arxiv": "arXiv preprint server",
            "wikipedia": "Wikipedia articles",
            "general": "general scientific knowledge"
        }
        
        if not DDG_AVAILABLE and source == "web":
            return "Error: duckduckgo-search is not installed. Install with: pip install ddgs"
        
        # Get current date context
        from core.date_utils import get_date_context_string
        date_context = get_date_context_string()
        
        prompt = f"""You are a scientific research assistant specialized in astronomy and astrophysics.

{date_context}

Provide information about the following query based on {source_info.get(source, "general scientific knowledge")}.

IMPORTANT: Use the current date provided above as your reference. When the user asks about "hasta hoy", "hasta ahora", "recientes", or similar temporal references, use the current date shown above. Do NOT mention your training data cutoff date (like "octubre de 2023"). Instead, use the current date provided.

Query: {query}

Provide relevant information in Spanish, including key facts, recent discoveries if applicable, and scientific context."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return f"Research results ({source}):\n\n{response.content}"
        else:
            return f"Research results ({source}):\n\n{str(response)}"
            
    except Exception as e:
        return f"Error performing research: {str(e)}"


# ─────────────────────────────
# API INTEGRATOR TOOL
# ─────────────────────────────

def api_integrator_tool(api_name: str, query: str) -> str:
    """
    Integrates with external APIs or data sources.
    Uses APIIntegrationAgent for real API calls.
    
    Args:
        api_name: Name of the API to use ("nasa_apod", "nasa_neo", "wikipedia", "ads")
        query: Query or parameters for the API
        
    Returns:
        Structured results from the API
    """
    try:
        from agents.api_integration_agent import api_integration_agent_tool
        return api_integration_agent_tool(api_name, query)
    except ImportError:
        # Fallback if agent not available
        return f"API integration for {api_name} with query '{query}' - APIIntegrationAgent not available"
    except Exception as e:
        return f"Error en integración API: {str(e)}"


# ─────────────────────────────
# TRANSLATOR TOOL
# ─────────────────────────────

def translator_tool(text: str, target_lang: str = "es", source_lang: str = "auto") -> str:
    """
    Translates scientific text between languages, preserving terminology.
    
    Args:
        text: Text to translate
        target_lang: Target language code ("es" for Spanish, "en" for English)
        source_lang: Source language code ("auto" for auto-detect)
        
    Returns:
        Translated text
    """
    if not text:
        return ""
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=OPENAI_API_KEY
        )
        
        lang_names = {"es": "Spanish", "en": "English"}
        target = lang_names.get(target_lang, target_lang)
        
        prompt = f"""Translate the following scientific text to {target}, preserving all scientific terminology, units, and technical terms accurately.

Text:
{text[:2000]}

Provide only the translation, maintaining scientific accuracy."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        return f"Error translating: {str(e)}"


# ─────────────────────────────
# COMPUTATION TOOL
# ─────────────────────────────

def calculate_tool(expression: str, calculation_type: str = "general") -> str:
    """
    Performs physical or mathematical calculations.
    
    Args:
        expression: Mathematical expression or description of calculation
        calculation_type: Type of calculation ("general", "astrophysical", "cosmological")
        
    Returns:
        Calculation result
    """
    try:
        # Try to evaluate simple mathematical expressions
        import math
        
        # Replace common scientific constants
        expression = expression.replace('pi', str(math.pi))
        expression = expression.replace('e', str(math.e))
        
        # Try direct evaluation for simple expressions
        try:
            result = eval(expression, {"__builtins__": {}, "math": math, "sqrt": math.sqrt, 
                                      "sin": math.sin, "cos": math.cos, "tan": math.tan,
                                      "log": math.log, "exp": math.exp})
            return f"Calculation result: {result}"
        except:
            pass
        
        # Use LLM for complex calculations or descriptions
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=OPENAI_API_KEY
        )
        
        prompt = f"""Perform the following {calculation_type} calculation. Show your work and provide the result.

Calculation: {expression}

Provide the result with appropriate units and scientific notation if needed."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        return f"Error performing calculation: {str(e)}"


# ─────────────────────────────
# VALIDATOR TOOL
# ─────────────────────────────

def validator_tool(text: str, validation_type: str = "scientific") -> str:
    """
    Validates scientific accuracy, data consistency, and textual coherence.
    
    Args:
        text: Text to validate
        validation_type: Type of validation ("scientific", "consistency", "coherence")
        
    Returns:
        Validation results
    """
    if not text:
        return "No text provided for validation."
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            openai_api_key=OPENAI_API_KEY
        )
        
        validation_prompts = {
            "scientific": "Validate the scientific accuracy of the following text. Check for factual errors, incorrect units, or implausible values.",
            "consistency": "Check the consistency of data and facts throughout the text.",
            "coherence": "Validate the textual coherence, grammar, and logical flow of the text."
        }
        
        prompt = f"""{validation_prompts.get(validation_type, validation_prompts["scientific"])}

Text:
{text[:2000]}

Provide validation results in Spanish, noting any issues found or confirming accuracy."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        return f"Error during validation: {str(e)}"


# ─────────────────────────────
# EVALUATOR TOOL
# ─────────────────────────────

def evaluator_tool(results: str, criteria: str = "quality", agent_name: Optional[str] = None, 
                   input_data: Optional[str] = None, execution_time: Optional[float] = None) -> str:
    """
    Evaluates the overall quality, completeness, and correctness of generated results.
    Can also evaluate agent performance if agent_name and input_data are provided.
    
    Args:
        results: Results to evaluate
        criteria: Evaluation criteria ("quality", "completeness", "correctness")
        agent_name: Optional agent name for performance evaluation
        input_data: Optional input data for performance evaluation
        execution_time: Optional execution time for performance metrics
        
    Returns:
        Evaluation results
    """
    if not results:
        return "No results provided for evaluation."
    
    # Use EvaluatorAgent if agent_name provided
    if agent_name and input_data:
        try:
            from agents.evaluator_agent import evaluator_agent_tool
            return evaluator_agent_tool(agent_name, input_data, results, None, execution_time)
        except ImportError:
            pass  # Fallback to basic evaluation
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=OPENAI_API_KEY
        )
        
        prompt = f"""Evaluate the following results based on {criteria} criteria.

Results:
{results[:2000]}

Provide an evaluation in Spanish, noting strengths and areas for improvement."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        return f"Error durante evaluación: {str(e)}"


# ─────────────────────────────
# PLANNER TOOL
# ─────────────────────────────

def planner_tool(task: str, available_tools: Optional[List[str]] = None) -> str:
    """
    Plans multi-step tasks and decides the sequence of agents or tools to use.
    Uses PlannerAgent for structured task decomposition.
    
    Args:
        task: Task description
        available_tools: List of available tool names
        
    Returns:
        Execution plan
    """
    try:
        from agents.planner_agent import planner_agent_tool
        return planner_agent_tool(task, available_tools)
    except ImportError:
        # Fallback if agent not available
        if not task:
            return "No task provided for planning."
        
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.4,
                openai_api_key=OPENAI_API_KEY
            )
            
            tools_list = ", ".join(available_tools) if available_tools else "all available tools"
            
            prompt = f"""You are a task planner for a multi-agent astronomical analysis system.

Task: {task}

Available tools: {tools_list}

Create a step-by-step execution plan in Spanish, specifying which tools to use and in what order."""

            response = llm.invoke(prompt)
            
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            return f"Error creando plan: {str(e)}"
    except Exception as e:
        return f"Error en planificación: {str(e)}"


# ─────────────────────────────
# RETRAINER TOOL
# ─────────────────────────────

def retrainer_tool(new_data: str, auto_detect: bool = True) -> str:
    """
    Updates embeddings or retrains internal models with new data.
    Can automatically detect and extract relevant new information.
    
    Args:
        new_data: New data to incorporate
        auto_detect: If True, automatically detects and extracts relevant information
        
    Returns:
        Status message
    """
    try:
        # Import here to avoid circular imports
        from core.vectorstore import VectorStore
        from core.chunking import Chunker
        from agents.graph.resource_manager import get_resource_manager
        from agents.graph.context_manager import get_context_manager
        
        if not new_data or not new_data.strip():
            return "No data provided for retraining."
        
        resource_manager = get_resource_manager()
        context_manager = get_context_manager()
        
        # Auto-detect relevant information if enabled
        if auto_detect:
            llm = resource_manager.get_llm(model="gpt-4o-mini", temperature=0.2)
            
            prompt = f"""Analyze the following text and extract only relevant scientific information about astronomy/astrophysics.
            
Remove:
- Irrelevant information
- Repetitions
- Unnecessary formatting

Keep:
- Scientific concepts
- Important numerical data
- Relationships between concepts
- Discoveries or findings

Text:
{new_data[:5000]}

Provide only the extracted relevant text:"""

            try:
                response = llm.invoke(prompt)
                extracted_data = response.content if hasattr(response, 'content') else str(response)
                
                # Only use extracted data if it's significantly different (not just a summary)
                if len(extracted_data) > len(new_data) * 0.3:  # At least 30% of original
                    new_data = extracted_data
                    context_manager.set("last_retraining_extraction", {
                        "original_length": len(new_data),
                        "extracted_length": len(extracted_data)
                    })
            except Exception as e:
                # Continue with original data if extraction fails
                pass
        
        # Process and add new data to vector store
        chunker = Chunker()
        chunks_dict = {"retraining_document": chunker.chunk_text(new_data)}
        
        vector_store = resource_manager.get_vector_store()
        vector_store.add_documents(chunks_dict)
        vector_store.save()
        
        stats = vector_store.get_stats()
        
        # Store retraining info in context
        context_manager.add_tool_result("Retrainer", {
            "data_length": len(new_data),
            "chunks_added": len(chunks_dict["retraining_document"]),
            "total_chunks": stats.get('total_chunks', 0)
        }, {"auto_detect": auto_detect})
        
        return f"✅ Retraining completed successfully.\n- Data added: {len(new_data)} characters\n- Chunks created: {len(chunks_dict['retraining_document'])}\n- Total in vector store: {stats.get('total_chunks', 0)} chunks from {stats.get('total_documents', 0)} documents"
        
    except Exception as e:
        return f"Error during retraining: {str(e)}. Data length: {len(new_data)} characters."


# ─────────────────────────────
# MEMORY TOOL
# ─────────────────────────────

# Simple in-memory storage (in production, use a proper database)
_memory_store: Dict[str, str] = {}
_memory_timestamps: Dict[str, str] = {}


def memory_tool(operation: str, key: Optional[str] = None, value: Optional[str] = None) -> str:
    """
    Stores and retrieves previous user interactions or contextual information.
    
    Args:
        operation: Operation type ("store", "retrieve", "list", "delete", "clear")
        key: Key for storage/retrieval
        value: Value to store (for "store" operation)
        
    Returns:
        Result of the operation
    """
    from datetime import datetime
    
    if operation == "store":
        if key and value:
            _memory_store[key] = value
            _memory_timestamps[key] = datetime.now().isoformat()
            return f"Stored information under key: {key} (timestamp: {_memory_timestamps[key]})"
        else:
            return "Error: Both key and value required for store operation"
    
    elif operation == "retrieve":
        if key:
            if key in _memory_store:
                timestamp = _memory_timestamps.get(key, "unknown")
                return f"Retrieved from memory ({key}, stored: {timestamp}):\n{_memory_store[key]}"
            else:
                return f"No information found for key: {key}"
        else:
            return "Error: Key required for retrieve operation"
    
    elif operation == "list":
        if _memory_store:
            keys = list(_memory_store.keys())
            result = "Stored keys:\n"
            for k in keys:
                timestamp = _memory_timestamps.get(k, "unknown")
                result += f"- {k} (stored: {timestamp})\n"
            return result.strip()
        else:
            return "No stored information"
    
    elif operation == "delete":
        if key:
            if key in _memory_store:
                del _memory_store[key]
                if key in _memory_timestamps:
                    del _memory_timestamps[key]
                return f"Deleted key: {key}"
            else:
                return f"Key not found: {key}"
        else:
            return "Error: Key required for delete operation"
    
    elif operation == "clear":
        count = len(_memory_store)
        _memory_store.clear()
        _memory_timestamps.clear()
        return f"Cleared all stored information ({count} entries removed)"
    
    else:
        return f"Unknown operation: {operation}. Use 'store', 'retrieve', 'list', 'delete', or 'clear'"

