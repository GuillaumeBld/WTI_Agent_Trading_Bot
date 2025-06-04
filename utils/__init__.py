"""Utility package for the trading bot.

This package exposes the retry helpers as well as the general utility
functions defined in ``utils.py``.  Importing from ``utils`` therefore
behaves consistently whether callers expect the package or the module.
"""

from .retry import retry, retry_with_result, RetryError

# Re-export helper functions from the top-level ``utils.py`` module.  The
# module lives alongside this package so we load it explicitly.
import importlib.util
import os

_module_path = os.path.join(os.path.dirname(__file__), "..", "utils.py")
_spec = importlib.util.spec_from_file_location("_utils_module", _module_path)
_utils_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_utils_module)  # type: ignore

load_config = _utils_module.load_config
get_db_connection = _utils_module.get_db_connection
get_data_directory = _utils_module.get_data_directory
get_logs_directory = _utils_module.get_logs_directory
setup_logger = _utils_module.setup_logger

__all__ = [
    'retry', 'retry_with_result', 'RetryError',
    'load_config', 'get_db_connection', 'get_data_directory',
    'get_logs_directory', 'setup_logger'
]
