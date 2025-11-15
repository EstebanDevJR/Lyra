"""
Extractor Agent: Extracts text from PDFs or images using OCR.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.ocr import extract_text, batch_extract_text
from config import RAW_DATA_DIR
from typing import Union, List, Dict
from pathlib import Path


def extractor_tool(file_path: Union[str, List[str]], method: str = 'auto') -> str:
    """
    Tool function for extracting text from PDFs or images using OCR.
    Uses AWS Textract for images and scanned documents, PyPDF2 for readable PDFs.
    
    Args:
        file_path: Path to a single file or list of file paths
        method: Extraction method ('auto', 'textract', 'pypdf2')
                - 'auto': For PDFs, tries PyPDF2 first, then Textract if needed. For images, uses Textract.
                - 'textract': Force use of AWS Textract
                - 'pypdf2': Force use of PyPDF2 (PDFs only)
        
    Returns:
        Extracted text as string (or formatted string for multiple files)
    """
    try:
        if isinstance(file_path, list):
            # Resolve paths for batch extraction
            resolved_paths = []
            for path in file_path:
                resolved = _resolve_file_path(path)
                resolved_paths.append(resolved)
            # Batch extraction
            results = batch_extract_text(resolved_paths, method=method)
            # Format as readable string
            output = []
            for path, text in results.items():
                if isinstance(text, str) and not text.startswith("Error:"):
                    output.append(f"File: {path}\n{text}\n{'='*50}\n")
                else:
                    output.append(f"File: {path}\n{text}\n{'='*50}\n")
            return "\n".join(output)
        else:
            # Resolve file path (handle relative paths and filenames)
            resolved_path = _resolve_file_path(file_path)
            # Single file extraction
            text = extract_text(resolved_path, method=method)
            return text
            
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def _resolve_file_path(file_path: str) -> str:
    """
    Resolve file path to full path.
    If file_path is just a filename or relative path, search in RAW_DATA_DIR.
    
    Args:
        file_path: File path (can be absolute, relative, or just filename)
        
    Returns:
        Resolved absolute file path
    """
    path_obj = Path(file_path)
    
    # If it's an absolute path and exists, use it
    if path_obj.is_absolute() and path_obj.exists():
        return str(path_obj)
    
    # If it's an absolute path but doesn't exist, try RAW_DATA_DIR
    if path_obj.is_absolute():
        raw_data_path = RAW_DATA_DIR / path_obj.name
        if raw_data_path.exists():
            return str(raw_data_path)
    
    # If it's a relative path or just filename, try RAW_DATA_DIR first
    raw_data_path = RAW_DATA_DIR / path_obj.name
    if raw_data_path.exists():
        return str(raw_data_path)
    
    # Try the original path as-is (might be relative to current directory)
    if path_obj.exists():
        return str(path_obj.resolve())
    
    # If nothing found, return original path (will raise error in extract_text)
    return str(path_obj)


def extract_from_image(image_path: str) -> str:
    """
    Extract text from a single image using AWS Textract.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Extracted text
    """
    return extractor_tool(image_path, method='textract')


def extract_from_pdf(pdf_path: str, method: str = 'auto') -> str:
    """
    Extract text from a PDF file.
    Tries PyPDF2 first (for readable PDFs), falls back to Textract (for scanned PDFs).
    
    Args:
        pdf_path: Path to the PDF file
        method: Extraction method ('auto', 'textract', 'pypdf2')
        
    Returns:
        Extracted text
    """
    return extractor_tool(pdf_path, method=method)

