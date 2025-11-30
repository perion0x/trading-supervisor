"""
Retry utilities with exponential backoff for external API calls.

This module provides decorators and functions for implementing retry logic
with exponential backoff for handling transient failures.
"""

import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Any

from src.exceptions import ExternalAPIError, TimeoutError as TradingTimeoutError

logger = logging.getLogger(__name__)


def exponential_backoff_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 10.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    timeout: float = None
):
    """
    Decorator that implements exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 10.0)
        exceptions: Tuple of exception types to catch and retry (default: all)
        timeout: Optional total timeout in seconds for all attempts
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @exponential_backoff_retry(max_retries=3, initial_delay=1.0)
        def fetch_data():
            # API call that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Check timeout before attempting
                    if timeout is not None:
                        elapsed = time.time() - start_time
                        if elapsed >= timeout:
                            raise TradingTimeoutError(
                                f"Operation timed out after {elapsed:.2f} seconds"
                            )
                    
                    # Attempt the function call
                    logger.debug(
                        f"Attempting {func.__name__} (attempt {attempt + 1}/{max_retries + 1})"
                    )
                    result = func(*args, **kwargs)
                    
                    # Success - log if this was a retry
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    # If this was the last attempt, raise the exception
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {str(e)}"
                        )
                        raise
                    
                    # Check timeout before sleeping
                    if timeout is not None:
                        elapsed = time.time() - start_time
                        if elapsed >= timeout:
                            raise TradingTimeoutError(
                                f"Operation timed out after {elapsed:.2f} seconds"
                            )
                    
                    # Log the retry
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt + 1}, "
                        f"retrying in {delay:.2f}s: {str(e)}"
                    )
                    
                    # Sleep before retry
                    time.sleep(delay)
                    
                    # Calculate next delay with exponential backoff
                    delay = min(delay * backoff_factor, max_delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def retry_with_timeout(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    timeout: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Any:
    """
    Execute a function with retry logic and timeout.
    
    This is a functional version of the exponential_backoff_retry decorator.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        timeout: Total timeout in seconds for all attempts
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Result of the function call
        
    Raises:
        TimeoutError: If operation exceeds timeout
        Exception: If all retries fail
        
    Example:
        result = retry_with_timeout(
            lambda: api_call(),
            max_retries=3,
            timeout=10.0
        )
    """
    start_time = time.time()
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TradingTimeoutError(
                    f"Operation timed out after {elapsed:.2f} seconds"
                )
            
            # Attempt the function call
            logger.debug(f"Attempt {attempt + 1}/{max_retries + 1}")
            result = func()
            
            if attempt > 0:
                logger.info(f"Succeeded on attempt {attempt + 1}")
            
            return result
            
        except exceptions as e:
            last_exception = e
            
            if attempt >= max_retries:
                logger.error(f"Failed after {max_retries + 1} attempts: {str(e)}")
                raise
            
            # Check timeout before sleeping
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TradingTimeoutError(
                    f"Operation timed out after {elapsed:.2f} seconds"
                )
            
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {str(e)}")
            time.sleep(delay)
            delay = min(delay * 2.0, 10.0)
    
    if last_exception:
        raise last_exception


def with_timeout(timeout_seconds: float):
    """
    Decorator that adds a timeout to a function.
    
    Note: This uses a simple time-based check, not thread interruption.
    The function must cooperate by checking elapsed time periodically.
    
    Args:
        timeout_seconds: Maximum execution time in seconds
        
    Returns:
        Decorated function with timeout
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            # Store start time in kwargs for function to check
            kwargs['_timeout_start'] = start_time
            kwargs['_timeout_limit'] = timeout_seconds
            
            try:
                result = func(*args, **kwargs)
                
                # Check if we exceeded timeout
                elapsed = time.time() - start_time
                if elapsed >= timeout_seconds:
                    logger.warning(
                        f"{func.__name__} completed but exceeded timeout "
                        f"({elapsed:.2f}s > {timeout_seconds}s)"
                    )
                
                return result
                
            except Exception as e:
                elapsed = time.time() - start_time
                if elapsed >= timeout_seconds:
                    raise TradingTimeoutError(
                        f"{func.__name__} timed out after {elapsed:.2f} seconds"
                    )
                raise
        
        return wrapper
    return decorator
