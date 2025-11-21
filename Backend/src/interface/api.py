"""
FastAPI REST API for Lyra - Astronomical Scientific Analysis Assistant
"""

import sys
from pathlib import Path
from typing import Optional, List
import os
import tempfile
import shutil

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
import os
import re
import logging
from pathlib import Path

from agents.supervisor_agent import create_supervisor_agent, process_query
# Use LangGraph implementation by default
from agents.extractor_agent import extractor_tool
from agents.cleaner_agent import cleaner_tool
from agents.analyzer_agent import analyzer_tool
from agents.summarizer_agent import summarizer_tool
from agents.responder_agent import responder_tool
from core.chunking import Chunker
from core.vectorstore import VectorStore
from core.query_validator import validate_query_topic, sanitize_query
from core.langsmith_config import setup_langsmith, configure_langsmith_metadata
from config import OPENAI_API_KEY, RAW_DATA_DIR


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("lyra.api")

# Setup LangSmith tracing
langsmith_enabled = setup_langsmith()
if langsmith_enabled:
    logger.info("LangSmith tracing is enabled")
else:
    logger.info("LangSmith tracing is disabled")

# Initialize FastAPI app
app = FastAPI(
    title="🌠 Lyra API",
    description="API REST para el Asistente de Análisis Científico Astronómico",
    version="1.0.0"
)

# CORS middleware - Restrictive for production
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add custom middleware
from interface.middleware import (
    logging_middleware,
    security_headers_middleware
)

app.middleware("http")(logging_middleware)
app.middleware("http")(security_headers_middleware)

# Global agent instance
_agent = None


def get_agent():
    """Get or create supervisor agent instance (using LangGraph by default)."""
    global _agent
    if _agent is None:
        # Use LangGraph implementation (recommended)
        _agent = create_supervisor_agent(use_langgraph=True)
    return _agent


# Request/Response models
class MessageHistory(BaseModel):
    """Message in conversation history"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000, description="User query")
    file_path: Optional[str] = Field(None, max_length=500, description="Optional file path")
    chat_history: Optional[List[MessageHistory]] = Field(None, description="Previous conversation messages for context")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if v:
            # Prevent path traversal
            if '..' in v or v.startswith('/'):
                raise ValueError("Invalid file path")
        return v
    
    @validator('chat_history')
    def validate_chat_history(cls, v):
        if v:
            # Validate message roles only (no limit on message count)
            for msg in v:
                if msg.role not in ['user', 'assistant']:
                    raise ValueError(f"Invalid message role: {msg.role}. Must be 'user' or 'assistant'")
        return v


class QueryResponse(BaseModel):
    response: str
    status: str = "success"


class FileUploadResponse(BaseModel):
    file_path: str
    extracted_text: Optional[str] = None
    status: str = "success"
    message: str


class ProcessFileRequest(BaseModel):
    file_path: str
    operations: Optional[List[str]] = None  # ["extract", "clean", "analyze", "summarize"]


class ProcessFileResponse(BaseModel):
    results: dict
    status: str = "success"


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "name": "Lyra API",
        "version": "1.0.0",
        "status": "running",
        "description": "Asistente de Análisis Científico Astronómico"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "openai_configured": OPENAI_API_KEY is not None
    }


# Query processing endpoint
@app.post("/query", response_model=QueryResponse)
async def process_query_endpoint(request: QueryRequest):
    """
    Processes a query using the supervisor agent.
    
    Args:
        request: QueryRequest with query and optionally file path
        
    Returns:
        Agent response
    """
    try:
        if not OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY is not configured"
            )
        
        # Sanitize query to prevent prompt injection
        sanitized_query = sanitize_query(request.query)
        
        # Validate query topic (astrophysics, space, nature only)
        # Pass has_file=True if user has uploaded a file to be more permissive with document queries
        # Pass chat_history for context-aware validation
        has_file = bool(request.file_path)
        chat_history_dict = None
        if request.chat_history:
            # Convert MessageHistory objects to dicts for validator
            chat_history_dict = [
                {"role": msg.role, "content": msg.content} 
                for msg in request.chat_history
            ]
        is_valid, rejection_reason = validate_query_topic(
            sanitized_query, 
            use_llm=True, 
            has_file=has_file,
            chat_history=chat_history_dict
        )
        
        if not is_valid:
            logger.warning(f"Query rejected: {sanitized_query[:100]}... Reason: {rejection_reason}")
            return QueryResponse(
                response=rejection_reason or "Lo siento, solo puedo responder preguntas relacionadas con astrofísica, espacio y naturaleza.",
                status="success"
            )
        
        logger.info(f"Processing query: {sanitized_query[:100]}...")
        if request.chat_history:
            logger.info(f"Using chat history with {len(request.chat_history)} messages")
        
        # Resolve file_path to full path if provided
        resolved_file_path = None
        if request.file_path:
            # If file_path is just a filename, construct full path
            file_path_obj = Path(request.file_path)
            if not file_path_obj.is_absolute():
                # Assume it's in RAW_DATA_DIR
                resolved_file_path = RAW_DATA_DIR / file_path_obj.name
            else:
                resolved_file_path = file_path_obj
            
            # Verify file exists
            if not resolved_file_path.exists():
                logger.warning(f"File not found: {resolved_file_path}, trying with just filename")
                # Try with just the filename in RAW_DATA_DIR
                resolved_file_path = RAW_DATA_DIR / Path(request.file_path).name
                if not resolved_file_path.exists():
                    logger.warning(f"File still not found: {resolved_file_path}")
                    resolved_file_path = None
        
        agent = get_agent()
        # process_query handles both LangGraph and legacy LangChain agents
        # Pass chat history and file_path if available
        response = process_query(
            sanitized_query, 
            agent, 
            use_langgraph=True,
            chat_history=request.chat_history,
            file_path=str(resolved_file_path) if resolved_file_path else None
        )
        
        logger.info(f"Query processed successfully. Response length: {len(response)}")
        
        return QueryResponse(
            response=response,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


# File upload endpoint
@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Uploads a file (PDF or image) and extracts text.
    
    Args:
        file: File to upload (PDF, PNG, JPG, etc.)
        
    Returns:
        File information and extracted text
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed: {file_ext}. Allowed: {allowed_extensions}"
            )
        
        # Validate file size (max 50MB)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.0f}MB"
            )
        
        # Sanitize filename to prevent path traversal
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename)
        safe_filename = safe_filename[:255]  # Limit length
        
        # Save file to raw data directory
        file_path = RAW_DATA_DIR / safe_filename
        
        # Write file content (already read into memory)
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Extract text
        try:
            logger.info(f"Extracting text from file: {safe_filename}")
            extracted_text = extractor_tool(str(file_path))
            
            logger.info(f"Text extracted successfully. Length: {len(extracted_text)} characters")
            
            return FileUploadResponse(
                file_path=str(file_path),
                extracted_text=extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,
                status="success",
                message=f"File uploaded and processed successfully. Extracted text: {len(extracted_text)} characters."
            )
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}", exc_info=True)
            return FileUploadResponse(
                file_path=str(file_path),
                extracted_text=None,
                status="partial",
                message=f"File uploaded but error in extraction: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )


# Process file endpoint
@app.post("/process-file", response_model=ProcessFileResponse)
async def process_file_endpoint(request: ProcessFileRequest):
    """
    Processes a file with specific operations.
    
    Args:
        request: ProcessFileRequest with file path and operations
        
    Returns:
        Processing results
    """
    try:
        file_path = Path(request.file_path)
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Archivo no encontrado: {file_path}"
            )
        
        operations = request.operations or ["extract", "clean", "analyze"]
        results = {}
        
        # Extract
        if "extract" in operations:
            results["extracted"] = extractor_tool(str(file_path))
        
        # Clean
        if "clean" in operations and "extracted" in results:
            results["cleaned"] = cleaner_tool(results["extracted"])
        
        # Analyze
        if "analyze" in operations:
            text_to_analyze = results.get("cleaned") or results.get("extracted", "")
            if text_to_analyze:
                results["analysis"] = analyzer_tool(text_to_analyze, k=5)
        
        # Summarize
        if "summarize" in operations:
            text_to_summarize = results.get("cleaned") or results.get("extracted", "")
            if text_to_summarize:
                results["summary"] = summarizer_tool(text_to_summarize)
        
        return ProcessFileResponse(
            results=results,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


# Direct agent tool endpoints
@app.post("/extract")
async def extract_text(file_path: str = Form(...)):
    """Extracts text from a file."""
    try:
        result = extractor_tool(file_path)
        return {"extracted_text": result, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clean")
async def clean_text(text: str = Form(...)):
    """Cleans extracted text."""
    try:
        result = cleaner_tool(text)
        return {"cleaned_text": result, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_text(query: str = Form(...), k: int = Form(5)):
    """Analyzes text using semantic search."""
    try:
        result = analyzer_tool(query, k=k)
        return {"analysis": result, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize")
async def summarize_text(text: str = Form(...), max_length: Optional[int] = Form(None)):
    """Summarizes text."""
    try:
        result = summarizer_tool(text, max_length=max_length)
        return {"summary": result, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Vector store endpoints
@app.get("/vectorstore/stats")
async def get_vectorstore_stats():
    """Gets vector store statistics."""
    try:
        vector_store = VectorStore()
        vector_store.load()
        stats = vector_store.get_stats()
        return {"stats": stats, "status": "success"}
    except Exception as e:
        return {"stats": None, "status": "error", "message": str(e)}


@app.post("/vectorstore/add")
async def add_to_vectorstore(text: str = Form(...)):
    """Adds text to vector store."""
    try:
        chunker = Chunker()
        chunks_dict = {"new_document": chunker.chunk_text(text)}
        
        vector_store = VectorStore()
        vector_store.load()
        vector_store.add_documents(chunks_dict)
        vector_store.save()
        
        stats = vector_store.get_stats()
        return {
            "message": "Text added to vector store",
            "stats": stats,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Batch processing endpoint
@app.post("/batch-process")
async def batch_process(files: List[UploadFile] = File(...)):
    """
    Processes multiple files in batch (maximum 20 files).
    
    Args:
        files: List of files to process (PDFs, images, etc.)
        
    Returns:
        Processing results for each file
    """
    try:
        # Validate maximum number of files (20)
        MAX_FILES = 20
        if len(files) > MAX_FILES:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {MAX_FILES} files allowed. Received {len(files)} files."
            )
        
        results = []
        
        for file in files:
            # Save file
            file_path = RAW_DATA_DIR / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract text
            try:
                extracted = extractor_tool(str(file_path))
                cleaned = cleaner_tool(extracted)
                
                results.append({
                    "filename": file.filename,
                    "file_path": str(file_path),
                    "extracted_length": len(extracted),
                    "cleaned_length": len(cleaned),
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "file_path": str(file_path),
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "results": results,
            "total_files": len(files),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def create_app():
    """Create and return FastAPI app instance."""
    return app


# Import realtime endpoint - DISABLED TEMPORARILY
# from interface.realtime_api import handle_realtime_connection

# @app.websocket("/ws/realtime")
# async def websocket_realtime(websocket: WebSocket):
#     """
#     WebSocket endpoint for OpenAI Realtime API voice conversations.
#     
#     This endpoint proxies audio and events between the frontend and OpenAI Realtime API.
#     """
#     # await handle_realtime_connection(websocket)
#     pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

