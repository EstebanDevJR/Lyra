"""
Module for text extraction from images and PDFs using OCR.
Uses AWS Textract for images and scanned documents, PyPDF2 for readable PDFs.
"""

import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# Load environment variables
load_dotenv()

# AWS variables (optional, only if using Textract)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')


def extract_text_textract(file_path: str) -> str:
    """
    Extract text from a PDF or image using AWS Textract.
    
    Args:
        file_path: Path to the PDF or image file
        
    Returns:
        Extracted text from the file
    """
    if not BOTO3_AVAILABLE:
        raise ImportError("boto3 is not installed. Install with: pip install boto3")
    
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ValueError("AWS credentials are not configured in environment variables")
    
    try:
        client = boto3.client(
            'textract',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        with open(file_path, 'rb') as file:
            file_content = file.read()
        
        # Use analyze_document for PDFs and images
        response = client.analyze_document(
            Document={'Bytes': file_content},
            FeatureTypes=['FORMS', 'TABLES']
        )
        
        # Extract text from blocks
        text_blocks = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block.get('Text', ''))
        
        return '\n'.join(text_blocks)
    
    except Exception as e:
        raise Exception(f"Error processing file with Textract: {str(e)}")


def extract_text_pypdf2(pdf_path: str) -> str:
    """
    Extract text from a PDF using PyPDF2 (native text only, not images).
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text from the PDF
    """
    if not PYPDF2_AVAILABLE:
        raise ImportError("PyPDF2 is not installed. Install with: pip install PyPDF2")
    
    try:
        reader = PdfReader(pdf_path)
        text_pages = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_pages.append(text)
        
        return '\n\n'.join(text_pages)
    
    except Exception as e:
        raise Exception(f"Error processing PDF with PyPDF2: {str(e)}")


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image using AWS Textract.
    
    Args:
        image_path: Path to the image (PNG, JPG, JPEG, TIFF, BMP, GIF)
        
    Returns:
        Extracted text from the image
    """
    return extract_text_textract(image_path)


def extract_text(file_path: str, method: str = 'auto') -> str:
    """
    Main function to extract text from a file (PDF or image).
    For images: uses AWS Textract.
    For PDFs: tries PyPDF2 first (for readable PDFs), falls back to Textract (for scanned PDFs).
    
    Args:
        file_path: Path to the file (PDF or image)
        method: Method to use ('auto', 'textract', 'pypdf2')
                - 'auto': For PDFs, tries PyPDF2 first, then Textract if needed. For images, uses Textract.
                - 'textract': Force use of AWS Textract
                - 'pypdf2': Force use of PyPDF2 (PDFs only)
        
    Returns:
        Extracted text from the file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If method or file format is invalid
        Exception: If extraction fails
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    file_ext = file_path.suffix.lower()
    
    # If it's an image, use Textract
    if file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']:
        if method == 'textract' or method == 'auto':
            try:
                return extract_text_from_image(str(file_path))
            except Exception as e:
                raise Exception(f"Failed to extract text from image {file_path}: {str(e)}")
        else:
            raise ValueError(f"Method '{method}' not supported for images. Use 'textract' or 'auto'.")
    
    # If it's a PDF, use the specified method
    if file_ext == '.pdf':
        if method == 'auto':
            # Try PyPDF2 first (faster for readable PDFs), then Textract if it fails or no text found
            try:
                text = extract_text_pypdf2(str(file_path))
                if text and text.strip():
                    return text
                # If PyPDF2 returns empty text, it's likely a scanned PDF, use Textract
                print(f"PyPDF2 returned no text, using Textract for scanned PDF: {file_path}")
            except Exception as e:
                print(f"PyPDF2 extraction failed, using Textract as fallback: {str(e)}")
            
            # Use Textract as fallback for scanned PDFs
            try:
                return extract_text_textract(str(file_path))
            except Exception as e:
                raise Exception(f"All extraction methods failed for PDF {file_path}: {str(e)}")
        
        elif method == 'textract':
            return extract_text_textract(str(file_path))
        elif method == 'pypdf2':
            return extract_text_pypdf2(str(file_path))
        else:
            raise ValueError(f"Unknown method: {method}. Valid methods: 'auto', 'textract', 'pypdf2'")
    
    raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP, GIF")


def batch_extract_text(file_paths: List[str], method: str = 'auto') -> dict:
    """
    Extract text from multiple files.
    
    Args:
        file_paths: List of file paths
        method: Method to use ('auto', 'textract', 'pypdf2')
        
    Returns:
        Dictionary with {file_path: extracted_text}
    """
    results = {}
    
    for file_path in file_paths:
        try:
            text = extract_text(file_path, method=method)
            results[file_path] = text
        except Exception as e:
            results[file_path] = f"Error: {str(e)}"
    
    return results

