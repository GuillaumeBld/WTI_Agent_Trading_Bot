# utils.py
"""Backward-compatible wrapper for utility functions.

This module now simply re-exports the helpers from :mod:`utils.core` so that
legacy imports ``from utils import ...`` continue to work whether ``utils`` is
treated as a module or a package.
"""

from utils.core import (
    load_config,
    get_db_connection,
    get_data_directory,
    get_logs_directory,
    setup_logger,
)

__all__ = [
    'load_config',
    'get_db_connection',
    'get_data_directory',
    'get_logs_directory',
    'setup_logger',
]
