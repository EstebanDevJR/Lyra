"""
Error Handler: Provides robust error handling with retry logic.
Implements Strategy pattern for different retry strategies.
"""

from typing import Callable, Any, Optional, Dict, List
import time
import logging
from functools import wraps
from enum import Enum


class RetryStrategy(Enum):
    """Retry strategies."""
    LINEAR = "linear"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    FIBONACCI = "fibonacci"  # Fibonacci backoff


class ErrorHandler:
    """
    Handles errors with retry logic and error recovery strategies.
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize error handler.
        
        Args:
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds for retries
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.logger = logging.getLogger("lyra.error_handler")
    
    def _calculate_delay(self, attempt: int, strategy: RetryStrategy) -> float:
        """Calculate delay for retry attempt."""
        if strategy == RetryStrategy.LINEAR:
            return self.base_delay
        elif strategy == RetryStrategy.EXPONENTIAL:
            return self.base_delay * (2 ** attempt)
        elif strategy == RetryStrategy.FIBONACCI:
            # Fibonacci sequence: 1, 1, 2, 3, 5, 8, ...
            fib = [1, 1]
            for i in range(2, attempt + 2):
                fib.append(fib[i-1] + fib[i-2])
            return self.base_delay * fib[attempt]
        return self.base_delay
    
    def retry(
        self,
        func: Callable,
        *args,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        retryable_errors: Optional[tuple] = None,
        on_retry: Optional[Callable] = None,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            strategy: Retry strategy
            retryable_errors: Tuple of exception types to retry (None = all)
            on_retry: Optional callback called before each retry
            max_retries: Override default max_retries for this call
            **kwargs: Function keyword arguments (max_retries will be removed)
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        # Use provided max_retries or instance default
        retries = max_retries if max_retries is not None else self.max_retries
        
        # Remove max_retries from kwargs if present (shouldn't be passed to func)
        func_kwargs = {k: v for k, v in kwargs.items() if k != 'max_retries'}
        
        last_exception = None
        
        for attempt in range(retries + 1):
            try:
                return func(*args, **func_kwargs)
            except Exception as e:
                last_exception = e
                
                # Check if error is retryable
                if retryable_errors and not isinstance(e, retryable_errors):
                    raise
                
                # Don't retry on last attempt
                if attempt >= retries:
                    break
                
                # Calculate delay
                delay = self._calculate_delay(attempt, strategy)
                
                self.logger.warning(
                    f"Attempt {attempt + 1}/{retries + 1} failed for {func.__name__}: {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )
                
                # Call retry callback if provided
                if on_retry:
                    try:
                        on_retry(attempt + 1, e)
                    except Exception as callback_error:
                        self.logger.error(f"Error in retry callback: {callback_error}")
                
                time.sleep(delay)
        
        # All retries failed
        self.logger.error(
            f"All {retries + 1} attempts failed for {func.__name__}. "
            f"Last error: {str(last_exception)}"
        )
        raise last_exception
    
    def safe_execute(
        self,
        func: Callable,
        *args,
        default_return: Any = None,
        log_errors: bool = True,
        **kwargs
    ) -> Any:
        """
        Execute a function safely, catching all exceptions.
        
        Args:
            func: Function to execute
            *args: Function arguments
            default_return: Value to return on error
            log_errors: Whether to log errors
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or default_return on error
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_errors:
                self.logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            return default_return


def retry_on_error(
    max_retries: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retryable_errors: Optional[tuple] = None
):
    """
    Decorator for automatic retry on errors.
    
    Args:
        max_retries: Maximum number of retries
        strategy: Retry strategy
        retryable_errors: Tuple of exception types to retry
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = ErrorHandler(max_retries=max_retries)
            return handler.retry(
                func,
                *args,
                strategy=strategy,
                retryable_errors=retryable_errors,
                **kwargs
            )
        return wrapper
    return decorator


# Global error handler instance
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

