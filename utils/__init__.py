"""
Utils package for WTI Agent Trading Bot.

This package contains utility modules for the trading bot:
- retry: Provides retry functionality for handling transient errors
"""

from .retry import retry, retry_with_result, RetryError

# Core utility functions live in ``utils/core.py``. Import them here so they
# are available directly from the ``utils`` package.
from .core import (
    load_config,
    get_db_connection,
    get_data_directory,
    get_logs_directory,
    setup_logger,
)

__all__ = [
    'retry',
    'retry_with_result',
    'RetryError',
    'load_config',
    'get_db_connection',
    'get_data_directory',
    'get_logs_directory',
    'setup_logger',
]
