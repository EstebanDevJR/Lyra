"""
Configuration variables and paths for the project.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent

# Data paths
RAW_DATA_DIR = BASE_DIR / "src" / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "src" / "data" / "processed"
CHUNKS_DIR = BASE_DIR / "src" / "data" / "chunks"
VECTORSTORE_DIR = BASE_DIR / "src" / "data" / "vectorstore"

# Create directories if they don't exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

# Embedding configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536  # For text-embedding-3-small

# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")  # AWS region for serverless index (e.g., "us-east-1", "us-west-2")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "lyra-vectorstore")

# Legacy FAISS configuration (deprecated, kept for backwards compatibility)
FAISS_INDEX_NAME = "vectorstore.index"
FAISS_INDEX_PATH = VECTORSTORE_DIR / FAISS_INDEX_NAME

# OpenAI configuration (from environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# AWS configuration (optional, for Textract)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# LangSmith configuration (for observability and tracing)
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")  # LangSmith API key
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "lyra")  # Project name in LangSmith
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")  # LangSmith endpoint

