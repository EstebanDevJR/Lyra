"""
Utility functions for text processing, logging, and file operations.
"""

import os
import logging
import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime


def setup_logging(log_dir: Optional[str] = None, log_level: str = "INFO"):
    """
    Setup logging configuration.
    
    Args:
        log_dir: Directory to save log files (if None, logs to console only)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create log directory if specified
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )


def clean_text(text: str, preserve_scientific: bool = True) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Raw text to clean
        preserve_scientific: If True, preserves scientific notation and special characters
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace (but preserve line breaks for scientific formatting)
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
    text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines to double newline
    
    if preserve_scientific:
        # Preserve scientific notation, Greek letters, mathematical symbols, etc.
        # Keep: alphanumeric, basic punctuation, scientific notation (e.g., 1.5e-10), 
        # Greek letters, mathematical operators, brackets, etc.
        # Remove only truly problematic characters
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)  # Control characters
    else:
        # More aggressive cleaning (original behavior)
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def save_text_to_file(text: str, file_path: str):
    """
    Save text to a file.
    
    Args:
        text: Text to save
        file_path: Path to save the file
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)


def load_text_from_file(file_path: str) -> str:
    """
    Load text from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Text content
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_file_list(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
    """
    Get list of files in a directory.
    
    Args:
        directory: Directory path
        extensions: List of file extensions to filter (e.g., ['.pdf', '.txt'])
        
    Returns:
        List of file paths
    """
    directory = Path(directory)
    
    if not directory.exists():
        return []
    
    files = []
    for file_path in directory.iterdir():
        if file_path.is_file():
            if extensions is None or file_path.suffix.lower() in extensions:
                files.append(str(file_path))
    
    return sorted(files)


def ensure_dir(directory: str):
    """
    Ensure a directory exists, create if it doesn't.
    
    Args:
        directory: Directory path
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def validate_file_path(file_path: str) -> bool:
    """
    Validate if a file path exists and is readable.
    
    Args:
        file_path: Path to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except Exception:
        return False


def chunk_text_simple(text: str, max_length: int = 1000) -> List[str]:
    """
    Simple text chunking by length (fallback method).
    
    Args:
        text: Text to chunk
        max_length: Maximum length of each chunk
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    chunks = []
    current_chunk = ""
    
    for word in text.split():
        if len(current_chunk) + len(word) + 1 <= max_length:
            current_chunk += (" " + word if current_chunk else word)
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = word
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

