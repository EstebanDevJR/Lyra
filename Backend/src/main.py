"""
Main entry point for Lyra - Astronomical Scientific Analysis Assistant
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Setup LangSmith tracing before any other imports
from core.langsmith_config import setup_langsmith
setup_langsmith()

from config import OPENAI_API_KEY


def main():
    """
    Main function to run Lyra.
    """
    parser = argparse.ArgumentParser(
        description="🌠 Lyra: Astronomical Scientific Analysis Assistant"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for API (API mode only)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host for API (API mode only)"
    )
    
    args = parser.parse_args()
    
    # Check API key
    if not OPENAI_API_KEY:
        print("⚠️  Error: OPENAI_API_KEY is not configured.")
        print("   Please configure the OPENAI_API_KEY environment variable")
        print("   or create a .env file with: OPENAI_API_KEY=your_key_here")
        sys.exit(1)
    
    # Run API
    run_api(args.host, args.port)


def run_api(host: str, port: int):
    """Run FastAPI server."""
    try:
        import uvicorn
        from interface.api import app
        
        print(f"🚀 Starting API server at http://{host}:{port}")
        print(f"📚 Documentation available at http://{host}:{port}/docs")
        print(f"🔍 Alternative interface at http://{host}:{port}/redoc")
        
        uvicorn.run(app, host=host, port=port)
        
    except ImportError:
        print("⚠️  Error: uvicorn is not installed.")
        print("   Install with: pip install uvicorn")
        sys.exit(1)


if __name__ == "__main__":
    main()
