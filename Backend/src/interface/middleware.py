"""
Middleware for FastAPI: Logging, security headers, etc.
"""

import time
from typing import Callable
from fastapi import Request
from fastapi.responses import Response
import logging

logger = logging.getLogger("lyra.middleware")


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Logging middleware for structured logging."""
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        # Add process time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Error processing request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "process_time": process_time
            },
            exc_info=True
        )
        raise


async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    """Add security headers to responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

