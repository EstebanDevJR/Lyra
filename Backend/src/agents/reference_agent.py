"""
Reference Agent: Manages citations, references, and bibliographic information from scientific documents.
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY


def reference_tool(text: str, operation: str = "extract") -> str:
    """
    Tool function for extracting and managing references from scientific documents.
    
    Args:
        text: Document text containing references
        operation: Operation type ("extract", "format", "validate", "cite")
        
    Returns:
        Processed references or citation information
    """
    if not text:
        return "No text provided for reference processing."
    
    try:
        if operation == "extract":
            return _extract_references(text)
        elif operation == "format":
            return _format_references(text)
        elif operation == "validate":
            return _validate_references(text)
        elif operation == "cite":
            return _generate_citation(text)
        else:
            return f"Unknown operation: {operation}. Use 'extract', 'format', 'validate', or 'cite'"
            
    except Exception as e:
        return f"Error processing references: {str(e)}"


def _extract_references(text: str) -> str:
    """
    Extract bibliographic references from text.
    
    Args:
        text: Text containing references
        
    Returns:
        Extracted references
    """
    # Pattern for common reference formats
    # Pattern 1: Author et al. (Year) format
    pattern1 = r'([A-Z][a-z]+(?:\s+et\s+al\.?)?(?:\s+[A-Z][a-z]+)*)\s*\((\d{4})\)'
    
    # Pattern 2: [Author, Year] format
    pattern2 = r'\[([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(\d{4})\]'
    
    # Pattern 3: Numbered references [1], [2], etc.
    pattern3 = r'\[(\d+)\]'
    
    references = []
    
    # Find all matches
    matches1 = re.finditer(pattern1, text, re.IGNORECASE)
    for match in matches1:
        author = match.group(1)
        year = match.group(2)
        references.append(f"{author} ({year})")
    
    matches2 = re.finditer(pattern2, text)
    for match in matches2:
        author = match.group(1)
        year = match.group(2)
        references.append(f"{author} ({year})")
    
    matches3 = re.finditer(pattern3, text)
    ref_numbers = [int(m.group(1)) for m in matches3]
    
    # Use LLM to extract more detailed references
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=OPENAI_API_KEY
        )
        
        prompt = f"""Extract all bibliographic references from this scientific text. Include authors, titles, journals, years, and DOIs if present.

Text:
{text[:3000]}

List all references found in a structured format in Spanish."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            llm_refs = response.content
        else:
            llm_refs = str(response)
        
        # Combine pattern-based and LLM-based extraction
        result = "References found:\n\n"
        if references:
            result += "References by pattern:\n"
            for ref in set(references):
                result += f"- {ref}\n"
            result += "\n"
        
        if ref_numbers:
            result += f"Reference numbers found: {', '.join(map(str, sorted(set(ref_numbers))))}\n\n"
        
        result += "Detailed references (LLM):\n"
        result += llm_refs
        
        return result
        
    except Exception as e:
        # Fallback to pattern-based extraction
        if references:
            return "Referencias encontradas:\n" + "\n".join(f"- {ref}" for ref in set(references))
        else:
            return "No se encontraron referencias en el formato esperado."


def _format_references(text: str) -> str:
    """
    Format references into a consistent bibliographic style.
    
    Args:
        text: Text with references
        
    Returns:
        Formatted references
    """
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            openai_api_key=OPENAI_API_KEY
        )
        
        prompt = f"""Format the following references into a consistent bibliographic style (APA format).

Text with references:
{text[:2000]}

Provide formatted references in Spanish, following APA style."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        return f"Error formatting references: {str(e)}"


def _validate_references(text: str) -> str:
    """
    Validate that references are complete and properly formatted.
    
    Args:
        text: Text with references
        
    Returns:
        Validation results
    """
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            openai_api_key=OPENAI_API_KEY
        )
        
        prompt = f"""Validate the bibliographic references in this text. Check for:
- Complete information (authors, year, title, journal/venue)
- Consistent formatting
- Valid years and publication information

Text:
{text[:2000]}

Provide validation results in Spanish, noting any issues or confirming correctness."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        return f"Error validating references: {str(e)}"


def _generate_citation(text: str, style: str = "APA") -> str:
    """
    Generate a citation for the document itself.
    
    Args:
        text: Document text
        style: Citation style ("APA", "MLA", "Chicago")
        
    Returns:
        Generated citation
    """
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=OPENAI_API_KEY
        )
        
        prompt = f"""Generate a {style}-style citation for this scientific document. Extract:
- Author(s)
- Year
- Title
- Journal/Conference (if mentioned)
- DOI or URL (if mentioned)

Document text:
{text[:2000]}

Provide the citation in {style} format in Spanish."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        return f"Error generating citation: {str(e)}"


def extract_doi(text: str) -> str:
    """
    Extract DOI (Digital Object Identifier) from text.
    
    Args:
        text: Text that may contain DOI
        
    Returns:
        Extracted DOI(s)
    """
    # DOI pattern: 10.xxxx/xxxxx
    doi_pattern = r'10\.\d{4,}/[^\s]+'
    
    dois = re.findall(doi_pattern, text)
    
    if dois:
        return f"DOIs encontrados:\n" + "\n".join(f"- {doi}" for doi in set(dois))
    else:
        return "No se encontraron DOIs en el texto."


def extract_arxiv_id(text: str) -> str:
    """
    Extract arXiv ID from text.
    
    Args:
        text: Text that may contain arXiv ID
        
    Returns:
        Extracted arXiv ID(s)
    """
    # arXiv pattern: arXiv:XXXX.XXXXX or arxiv.org/abs/XXXX.XXXXX
    arxiv_pattern = r'arXiv[:\s]+(\d{4}\.\d{4,5}(?:v\d+)?)'
    arxiv_url_pattern = r'arxiv\.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?)'
    
    ids = re.findall(arxiv_pattern, text, re.IGNORECASE)
    ids.extend(re.findall(arxiv_url_pattern, text, re.IGNORECASE))
    
    if ids:
        return f"arXiv IDs encontrados:\n" + "\n".join(f"- {arxiv_id}" for arxiv_id in set(ids))
    else:
        return "No se encontraron arXiv IDs en el texto."


def create_reference_list(text: str) -> str:
    """
    Create a formatted reference list from extracted references.
    
    Args:
        text: Document text
        
    Returns:
        Formatted reference list
    """
    references = _extract_references(text)
    
    # Try to get more detailed references using LLM
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=OPENAI_API_KEY
        )
        
        prompt = f"""Create a complete reference list from this scientific document. Extract all citations and format them properly.

Document:
{text[:3000]}

Provide a numbered reference list in APA format in Spanish."""

        response = llm.invoke(prompt)
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        return references + f"\n\n(Error generating detailed list: {str(e)})"

