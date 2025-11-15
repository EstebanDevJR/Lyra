"""
Summarizer Agent: Summarizes documents or extracted text, focusing on key findings and results.
"""

import sys
import re
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY


def summarizer_tool(text: str, max_length: Optional[int] = None, 
                    focus: str = "key findings") -> str:
    """
    Tool function for summarizing documents or extracted text.
    
    Args:
        text: Text to summarize
        max_length: Maximum length of summary in words (None for automatic)
        focus: What to focus on ("key findings", "methods", "results", "general")
        
    Returns:
        Summarized text
    """
    if not text or not text.strip():
        return "No text provided for summarization."
    
    try:
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=OPENAI_API_KEY
        )
        
        # Determine summary length instruction
        length_instruction = ""
        if max_length:
            length_instruction = f" The summary should be approximately {max_length} words."
        
        # Create prompt based on focus
        focus_prompts = {
            "key findings": "Focus on the main scientific findings, discoveries, and conclusions.",
            "methods": "Focus on the methodology, experimental setup, and techniques used.",
            "results": "Focus on the results, data, measurements, and quantitative outcomes.",
            "general": "Provide a general overview covering the main topics and important information."
        }
        
        focus_instruction = focus_prompts.get(focus, focus_prompts["general"])
        
        prompt = f"""You are a scientific summarization assistant specializing in astronomical and astrophysical content.

Your task is to summarize the following text in Spanish, focusing on {focus_instruction}{length_instruction}

Text to summarize:
{text[:4000]}  # Limit to avoid token limits

Provide a clear, concise summary that preserves important scientific terminology and concepts."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        # Fallback to simple extraction-based summary
        return _simple_summary(text, max_length)


def _simple_summary(text: str, max_length: Optional[int] = None) -> str:
    """
    Simple extraction-based summary as fallback.
    
    Args:
        text: Text to summarize
        max_length: Maximum length in words
        
    Returns:
        Simple summary
    """
    sentences = text.split('.')
    
    # Take first few sentences and last few sentences
    if len(sentences) > 4:
        summary_sentences = sentences[:2] + sentences[-2:]
    else:
        summary_sentences = sentences
    
    summary = '. '.join(s.strip() for s in summary_sentences if s.strip())
    
    if max_length:
        words = summary.split()
        if len(words) > max_length:
            summary = ' '.join(words[:max_length]) + "..."
    
    return summary


def summarize_sections(text: str) -> str:
    """
    Summarize different sections of a document separately.
    
    Args:
        text: Document text
        
    Returns:
        Section-by-section summary
    """
    # Split by common section markers
    sections = re.split(r'\n\s*(?:Abstract|Introduction|Methods|Results|Discussion|Conclusion|Resumen|Introducción|Métodos|Resultados|Discusión|Conclusión)\s*\n', text, flags=re.IGNORECASE)
    
    summaries = []
    for i, section in enumerate(sections):
        if section.strip():
            section_summary = summarizer_tool(section, max_length=100, focus="general")
            summaries.append(f"Section {i+1}:\n{section_summary}\n")
    
    return "\n".join(summaries) if summaries else summarizer_tool(text)

