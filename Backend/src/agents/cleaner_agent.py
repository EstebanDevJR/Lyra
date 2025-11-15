"""
Cleaner Agent: Cleans and normalizes extracted text by removing noise, symbols, and irrelevant data.
"""

import re
import sys
from pathlib import Path
from typing import Union

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.utils import clean_text


def cleaner_tool(text: str, aggressive: bool = False) -> str:
    """
    Tool function for cleaning and normalizing extracted text.
    
    Args:
        text: Raw text to clean
        aggressive: If True, performs more aggressive cleaning (removes more characters)
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Basic cleaning
    cleaned = text.strip()
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove line breaks that don't make sense (multiple consecutive line breaks)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    if aggressive:
        # More aggressive cleaning: remove special characters but keep scientific notation
        # Keep: letters, numbers, basic punctuation, scientific notation (e.g., 1.5e-10)
        cleaned = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}\+\=\*\/\^0-9eE]', '', cleaned)
        
        # Remove standalone special characters
        cleaned = re.sub(r'\s+[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}\+\=\*\/\^0-9eE]+\s+', ' ', cleaned)
    else:
        # Standard cleaning: remove only clearly problematic characters
        # Remove control characters except newlines and tabs
        cleaned = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', cleaned)
        
        # Remove unusual Unicode characters but keep accented letters
        cleaned = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}\+\=\*\/\^0-9eEáéíóúÁÉÍÓÚñÑüÜ]', ' ', cleaned)
    
    # Fix spacing around punctuation
    cleaned = re.sub(r'\s+([\.\,\;\:\!\?])', r'\1', cleaned)
    cleaned = re.sub(r'([\.\,\;\:\!\?])\s*([\.\,\;\:\!\?])', r'\1\2', cleaned)
    
    # Remove multiple spaces
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    
    # Remove spaces at start/end of lines
    lines = cleaned.split('\n')
    lines = [line.strip() for line in lines]
    cleaned = '\n'.join(lines)
    
    # Remove empty lines (keep at most one empty line between paragraphs)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()


def normalize_scientific_text(text: str) -> str:
    """
    Normalize scientific text, preserving scientific notation and formulas.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    cleaned = cleaner_tool(text, aggressive=False)
    
    # Preserve scientific notation patterns
    # e.g., 1.5e-10, 2.3E+5, etc.
    cleaned = re.sub(r'(\d+\.?\d*)\s*[eE]\s*([\+\-]?)\s*(\d+)', r'\1e\2\3', cleaned)
    
    # Normalize spacing around operators in formulas
    cleaned = re.sub(r'\s*([\+\-\=\*\/\^])\s*', r' \1 ', cleaned)
    
    return cleaned.strip()


def remove_noise(text: str) -> str:
    """
    Remove OCR noise and artifacts from text.
    
    Args:
        text: Text with potential OCR noise
        
    Returns:
        Text with noise removed
    """
    # Remove common OCR errors
    # Remove isolated characters (likely OCR errors)
    cleaned = re.sub(r'\s+[a-zA-Z]\s+', ' ', text)
    
    # Remove repeated characters (more than 3 in a row)
    cleaned = re.sub(r'(.)\1{3,}', r'\1\1\1', cleaned)
    
    # Remove lines that are mostly symbols
    lines = cleaned.split('\n')
    filtered_lines = []
    for line in lines:
        # Keep line if it has at least 30% alphanumeric characters
        alnum_count = sum(1 for c in line if c.isalnum())
        if len(line) == 0 or alnum_count / max(len(line), 1) >= 0.3:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

