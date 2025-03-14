"""
Retry Utility Module

This module provides retry functionality for handling transient errors in network operations
and other failure-prone tasks. It implements exponential backoff with configurable parameters.
"""

import time
import random
import logging
import functools
from typing import Callable, TypeVar, Any, Optional, List, Type, Dict, Union

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for generic function return type
T = TypeVar('T')

class RetryError(Exception):
    """Exception raised when all retry attempts have failed."""
    
    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        self.message = message
        self.last_exception = last_exception
        super().__init__(message)

def retry(
    max_tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    jitter: bool = True,
    logger_name: Optional[str] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry decorator with exponential backoff for handling transient errors.
    
    Args:
        max_tries (int): Maximum number of retry attempts before giving up.
        delay (float): Initial delay between retries in seconds.
        backoff (float): Backoff multiplier (e.g. value of 2 will double the delay each retry).
        exceptions (Exception or list): Exception(s) to catch and retry on.
        jitter (bool): Whether to add random jitter to delay to prevent thundering herd problem.
        logger_name (str, optional): Name of the logger to use. If None, uses the default logger.
    
    Returns:
        Callable: Decorated function with retry logic.
    """
    if logger_name:
        retry_logger = logging.getLogger(logger_name)
    else:
        retry_logger = logger
    
    if not isinstance(exceptions, (list, tuple)):
        exceptions = [exceptions]
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            tries = 0
            current_delay = delay
            last_exception = None
            
            while tries < max_tries:
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    tries += 1
                    last_exception = e
                    
                    if tries >= max_tries:
                        retry_logger.error(
                            f"Failed after {tries} attempts: {func.__name__}. Last error: {str(e)}"
                        )
                        break
                    
                    # Calculate next delay with optional jitter
                    if jitter:
                        # Add random jitter between 0% and 10% of the delay
                        sleep_time = current_delay * (1 + random.uniform(0, 0.1))
                    else:
                        sleep_time = current_delay
                    
                    retry_logger.warning(
                        f"Retry {tries}/{max_tries} for {func.__name__} after error: {str(e)}. "
                        f"Retrying in {sleep_time:.2f} seconds..."
                    )
                    
                    time.sleep(sleep_time)
                    current_delay *= backoff
            
            # If we've exhausted all retries, raise a RetryError
            raise RetryError(
                f"Failed after {max_tries} attempts: {func.__name__}",
                last_exception
            )
        
        return wrapper
    
    return decorator

def retry_with_result(
    max_tries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    validator: Callable[[Any], bool] = lambda x: x is not None,
    jitter: bool = True,
    logger_name: Optional[str] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry decorator that retries until a valid result is returned.
    
    Args:
        max_tries (int): Maximum number of retry attempts before giving up.
        delay (float): Initial delay between retries in seconds.
        backoff (float): Backoff multiplier (e.g. value of 2 will double the delay each retry).
        validator (Callable): Function that takes the result and returns True if valid, False otherwise.
        jitter (bool): Whether to add random jitter to delay to prevent thundering herd problem.
        logger_name (str, optional): Name of the logger to use. If None, uses the default logger.
    
    Returns:
        Callable: Decorated function with retry logic based on result validation.
    """
    if logger_name:
        retry_logger = logging.getLogger(logger_name)
    else:
        retry_logger = logger
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            tries = 0
            current_delay = delay
            last_result = None
            
            while tries < max_tries:
                result = func(*args, **kwargs)
                last_result = result
                
                if validator(result):
                    return result
                
                tries += 1
                if tries >= max_tries:
                    retry_logger.error(
                        f"Failed to get valid result after {tries} attempts: {func.__name__}"
                    )
                    break
                
                # Calculate next delay with optional jitter
                if jitter:
                    sleep_time = current_delay * (1 + random.uniform(0, 0.1))
                else:
                    sleep_time = current_delay
                
                retry_logger.warning(
                    f"Invalid result on attempt {tries}/{max_tries} for {func.__name__}. "
                    f"Retrying in {sleep_time:.2f} seconds..."
                )
                
                time.sleep(sleep_time)
                current_delay *= backoff
            
            # If we've exhausted all retries, return the last result
            return last_result
        
        return wrapper
    
    return decorator
