"""
Timeout decorator for async functions and tools.
Prevents indefinite hangs on slow LLM/database calls.
"""

import asyncio
import functools
from typing import Callable, Any, Optional

# Import config dynamically to avoid circular imports
def _get_config():
    from src.config import config
    return config


class TimeoutError(Exception):
    """Raised when function exceeds timeout."""
    pass


def with_timeout(seconds: Optional[int] = None):
    """
    Decorator to add timeout to async functions.
    
    Usage:
        @with_timeout(seconds=30)
        async def my_function():
            ...
    
    Args:
        seconds: Timeout in seconds. If None, uses config default (10s).
    
    Raises:
        TimeoutError: If function exceeds timeout.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            config = _get_config()
            timeout = seconds or config.TOOL_TIMEOUT_SECONDS
            
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                func_name = func.__name__
                raise TimeoutError(
                    f"{func_name} exceeded {timeout}s timeout"
                )
        
        return wrapper
    
    return decorator


def with_timeout_sync(seconds: Optional[int] = None):
    """
    Timeout decorator for synchronous functions.
    
    Note: This is less reliable than async version but can wrap sync tools.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            config = _get_config()
            timeout = seconds or config.TOOL_TIMEOUT_SECONDS
            
            # For sync functions, we can't truly interrupt, so we just warn
            # In production, use async everywhere
            import time
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            
            if elapsed > timeout:
                raise TimeoutError(
                    f"{func.__name__} took {elapsed:.2f}s (timeout: {timeout}s)"
                )
            
            return result
        
        return wrapper
    
    return decorator
