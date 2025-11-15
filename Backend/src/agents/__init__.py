"""
Agents module for Lyra - Multi-agent system for astronomical scientific analysis.

This module contains all agent implementations for the Lyra system.
"""

# Main agents
from .extractor_agent import extractor_tool, extract_from_image, extract_from_pdf
from .cleaner_agent import cleaner_tool, normalize_scientific_text, remove_noise
from .analyzer_agent import analyzer_tool, classify_document, identify_key_concepts
from .summarizer_agent import summarizer_tool, summarize_sections
from .responder_agent import responder_tool, format_response
from .context_agent import contextualizer_tool, add_historical_context, add_theoretical_context
from .reference_agent import (
    reference_tool,
    extract_doi,
    extract_arxiv_id,
    create_reference_list
)

# Additional tools
from .additional_tools import (
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

# Supervisor
from .supervisor_agent import create_supervisor_agent, process_query, tools, llmSupervisor, llm

__all__ = [
    # Main agents
    'extractor_tool',
    'extract_from_image',
    'extract_from_pdf',
    'cleaner_tool',
    'normalize_scientific_text',
    'remove_noise',
    'analyzer_tool',
    'classify_document',
    'identify_key_concepts',
    'summarizer_tool',
    'summarize_sections',
    'responder_tool',
    'format_response',
    'contextualizer_tool',
    'add_historical_context',
    'add_theoretical_context',
    'reference_tool',
    'extract_doi',
    'extract_arxiv_id',
    'create_reference_list',
    
    # Additional tools
    'formatter_tool',
    'classifier_tool',
    'data_curator_tool',
    'knowledge_base_tool',
    'researcher_tool',
    'web_search_tool',
    'api_integrator_tool',
    'translator_tool',
    'calculate_tool',
    'validator_tool',
    'evaluator_tool',
    'planner_tool',
    'retrainer_tool',
    'memory_tool',
    
    # Supervisor
    'create_supervisor_agent',
    'process_query',
    'tools',
    'llmSupervisor',
    'llm',
]

